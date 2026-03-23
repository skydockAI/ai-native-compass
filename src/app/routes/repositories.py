"""Repository management routes (REQ-021, REQ-027–030, REQ-050, REQ-051)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from ..authz import role_required
from ..services import repository_service, shared_attribute_service, team_service, template_service
from ..services.repository_service import RepositoryServiceError
from .forms import RepositoryCreateForm, RepositoryDuplicateForm, RepositoryEditForm

repositories_bp = Blueprint('repositories', __name__, url_prefix='/repositories')


# ---------------------------------------------------------------------------
# Repository list
# ---------------------------------------------------------------------------

@repositories_bp.route('/')
@login_required
def index():
    """Repository list with active/archived filter."""
    show_archived = request.args.get('archived', '0') == '1'
    repos = repository_service.get_repositories(include_archived=True) if show_archived \
        else repository_service.get_repositories()
    return render_template(
        'repositories/list.html',
        repos=repos,
        show_archived=show_archived,
    )


# ---------------------------------------------------------------------------
# Repository detail
# ---------------------------------------------------------------------------

@repositories_bp.route('/<int:repo_id>')
@login_required
def detail(repo_id):
    """Repository detail page showing shared attributes and artifact values."""
    repo = repository_service.get_repository_by_id(repo_id)
    if repo is None:
        flash('Repository not found.', 'danger')
        return redirect(url_for('repositories.index'))

    artifact_values = repository_service.get_artifact_values_map(repo_id)
    shared_attr_values = repository_service.get_shared_attr_values_map(repo_id)
    custom_attrs = shared_attribute_service.get_attributes(include_inactive=False, custom_only=True)
    # Also include inactive custom attrs if repo has values for them
    return render_template(
        'repositories/detail.html',
        repo=repo,
        artifact_values=artifact_values,
        shared_attr_values=shared_attr_values,
        custom_attrs=custom_attrs,
    )


# ---------------------------------------------------------------------------
# Create repository (Admin + Editor)
# ---------------------------------------------------------------------------

@repositories_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'editor')
def create():
    """Display and process new-repository form (template-first workflow)."""
    form = RepositoryCreateForm()

    active_templates = template_service.get_templates(include_archived=False)
    active_teams = team_service.get_teams(include_archived=False)

    form.template_id.choices = [(0, '— select a template —')] + [
        (t.id, t.name) for t in active_templates
    ]
    form.team_id.choices = [(0, '— select a team —')] + [
        (t.id, t.name) for t in active_teams
    ]

    if form.validate_on_submit():
        # Collect artifact values from raw form data (dynamic fields via HTMX)
        artifact_values = _extract_artifact_values(request.form)
        # Collect shared attribute values
        shared_attr_values = _extract_shared_attr_values(request.form)

        try:
            repo = repository_service.create_repository(
                name=form.name.data,
                url=form.url.data,
                description=form.description.data,
                team_id=form.team_id.data,
                template_id=form.template_id.data,
                artifact_values=artifact_values,
                shared_attr_values=shared_attr_values,
            )
            flash('Repository created successfully.', 'success')
            return redirect(url_for('repositories.detail', repo_id=repo.id))
        except RepositoryServiceError as exc:
            flash(str(exc), 'danger')

    # On GET or re-render after validation failure, load artifact fields if
    # a template was previously selected (form re-render after POST failure)
    selected_template_id = form.template_id.data or 0
    selected_template = None
    if selected_template_id:
        selected_template = template_service.get_template_by_id(selected_template_id)

    custom_attrs = shared_attribute_service.get_attributes(include_inactive=False, custom_only=True)

    return render_template(
        'repositories/create.html',
        form=form,
        selected_template=selected_template,
        custom_attrs=custom_attrs,
    )


# ---------------------------------------------------------------------------
# HTMX endpoint — dynamic artifact fields
# ---------------------------------------------------------------------------

@repositories_bp.route('/artifact-fields')
@login_required
@role_required('admin', 'editor')
def artifact_fields():
    """Return HTMX partial with artifact input fields for a given template (REQ-050)."""
    template_id = request.args.get('template_id', type=int)
    template = template_service.get_template_by_id(template_id) if template_id else None
    custom_attrs = shared_attribute_service.get_attributes(include_inactive=False, custom_only=True)
    return render_template(
        'repositories/partials/artifact_fields.html',
        template=template,
        custom_attrs=custom_attrs,
        artifact_values={},
        shared_attr_values={},
    )


# ---------------------------------------------------------------------------
# Edit repository (Admin + Editor)
# ---------------------------------------------------------------------------

@repositories_bp.route('/<int:repo_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'editor')
def edit(repo_id):
    """Display and process edit-repository form (template read-only)."""
    repo = repository_service.get_repository_by_id(repo_id)
    if repo is None:
        flash('Repository not found.', 'danger')
        return redirect(url_for('repositories.index'))

    active_teams = team_service.get_teams(include_archived=False)
    # Also include current team even if archived (so current assignment is visible)
    team_choices = [(t.id, t.name) for t in active_teams]
    if repo.team and not any(t[0] == repo.team_id for t in team_choices):
        team_choices.insert(0, (repo.team_id, f'{repo.team.name} (archived)'))

    form = RepositoryEditForm(obj=repo)
    form.team_id.choices = team_choices

    if request.method == 'GET':
        form.name.data = repo.name
        form.url.data = repo.url
        form.description.data = repo.description
        form.team_id.data = repo.team_id
        form.version.data = repo.version

    if form.validate_on_submit():
        artifact_values = _extract_artifact_values(request.form)
        shared_attr_values = _extract_shared_attr_values(request.form)

        try:
            repository_service.update_repository(
                repo_id=repo_id,
                name=form.name.data,
                url=form.url.data,
                description=form.description.data,
                team_id=form.team_id.data,
                artifact_values=artifact_values,
                shared_attr_values=shared_attr_values,
                expected_version=int(form.version.data),
            )
            flash('Repository updated successfully.', 'success')
            return redirect(url_for('repositories.detail', repo_id=repo_id))
        except RepositoryServiceError as exc:
            flash(str(exc), 'danger')

    artifact_values_map = repository_service.get_artifact_values_map(repo_id)
    shared_attr_values_map = repository_service.get_shared_attr_values_map(repo_id)
    custom_attrs = shared_attribute_service.get_attributes(include_inactive=False, custom_only=True)

    return render_template(
        'repositories/edit.html',
        form=form,
        repo=repo,
        artifact_values=artifact_values_map,
        shared_attr_values=shared_attr_values_map,
        custom_attrs=custom_attrs,
    )


# ---------------------------------------------------------------------------
# Duplicate repository (Admin + Editor)
# ---------------------------------------------------------------------------

@repositories_bp.route('/<int:repo_id>/duplicate', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'editor')
def duplicate(repo_id):
    """Display and process the duplicate-repository form (REQ-052)."""
    source = repository_service.get_repository_by_id(repo_id)
    if source is None:
        flash('Repository not found.', 'danger')
        return redirect(url_for('repositories.index'))

    form = RepositoryDuplicateForm()

    if request.method == 'GET':
        form.name.data = f'Copy of {source.name}'
        form.url.data = ''

    if form.validate_on_submit():
        try:
            dup = repository_service.duplicate_repository(
                source_repo_id=repo_id,
                name=form.name.data,
                url=form.url.data,
            )
            flash('Repository duplicated successfully.', 'success')
            return redirect(url_for('repositories.detail', repo_id=dup.id))
        except RepositoryServiceError as exc:
            flash(str(exc), 'danger')

    return render_template(
        'repositories/duplicate.html',
        form=form,
        source=source,
    )


# ---------------------------------------------------------------------------
# Archive / Reactivate
# ---------------------------------------------------------------------------

@repositories_bp.route('/<int:repo_id>/archive', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def archive(repo_id):
    """Archive a repository."""
    try:
        repository_service.archive_repository(repo_id)
        flash('Repository archived successfully.', 'success')
    except RepositoryServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('repositories.index'))


@repositories_bp.route('/<int:repo_id>/reactivate', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def reactivate(repo_id):
    """Reactivate an archived repository."""
    try:
        repository_service.reactivate_repository(repo_id)
        flash('Repository reactivated successfully.', 'success')
    except RepositoryServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('repositories.index', archived='1'))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_artifact_values(form_data):
    """Extract artifact_<id> fields from form data.

    Returns dict mapping artifact_id (int) → raw string value.
    """
    result = {}
    for key, value in form_data.items():
        if key.startswith('artifact_'):
            try:
                artifact_id = int(key[len('artifact_'):])
                result[artifact_id] = value
            except ValueError:
                pass
    return result


def _extract_shared_attr_values(form_data):
    """Extract shared_attr_<id> fields from form data.

    Returns dict mapping attribute_id (int str) → raw string value.
    """
    result = {}
    for key, value in form_data.items():
        if key.startswith('shared_attr_'):
            try:
                attr_id = int(key[len('shared_attr_'):])
                result[attr_id] = value
            except ValueError:
                pass
    return result
