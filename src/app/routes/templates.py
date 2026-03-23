"""Template management routes (REQ-031, REQ-032, REQ-033, REQ-037–041)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from ..authz import role_required
from ..models.template import ArtifactType, ArtifactValueType
from ..services import template_service
from ..services.template_service import TemplateServiceError
from .forms import ArtifactForm, ListOptionForm, TemplateCreateForm, TemplateEditForm

templates_bp = Blueprint('templates', __name__, url_prefix='/templates')


# --------------------------------------------------------------------------
# Template list (all authenticated users)
# --------------------------------------------------------------------------

@templates_bp.route('/')
@login_required
def index():
    """Template list with active/archived filter."""
    show_archived = request.args.get('archived', '0') == '1'
    templates = (
        template_service.get_templates(include_archived=True)
        if show_archived
        else template_service.get_templates()
    )
    return render_template(
        'templates/list.html',
        templates=templates,
        show_archived=show_archived,
    )


# --------------------------------------------------------------------------
# Template detail (all authenticated users)
# --------------------------------------------------------------------------

@templates_bp.route('/<int:template_id>')
@login_required
def detail(template_id):
    """Template detail page showing all artifacts."""
    tmpl = template_service.get_template_by_id(template_id)
    if tmpl is None:
        flash('Template not found.', 'danger')
        return redirect(url_for('templates.index'))
    return render_template('templates/detail.html', template=tmpl)


# --------------------------------------------------------------------------
# Create template (Admin only)
# --------------------------------------------------------------------------

@templates_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create():
    """Display and process new-template form."""
    form = TemplateCreateForm()
    if form.validate_on_submit():
        try:
            template_service.create_template(
                name=form.name.data,
                description=form.description.data,
            )
            flash('Template created successfully.', 'success')
            return redirect(url_for('templates.index'))
        except TemplateServiceError as exc:
            flash(str(exc), 'danger')

    return render_template('templates/form.html', form=form, is_edit=False)


# --------------------------------------------------------------------------
# Edit template (Admin only)
# --------------------------------------------------------------------------

@templates_bp.route('/<int:template_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit(template_id):
    """Display and process edit-template form."""
    tmpl = template_service.get_template_by_id(template_id)
    if tmpl is None:
        flash('Template not found.', 'danger')
        return redirect(url_for('templates.index'))

    form = TemplateEditForm(obj=tmpl)

    if request.method == 'GET':
        form.name.data = tmpl.name
        form.description.data = tmpl.description
        form.version.data = tmpl.version

    if form.validate_on_submit():
        try:
            template_service.update_template(
                template_id=template_id,
                name=form.name.data,
                description=form.description.data,
                expected_version=int(form.version.data),
            )
            flash('Template updated successfully.', 'success')
            return redirect(url_for('templates.index'))
        except TemplateServiceError as exc:
            flash(str(exc), 'danger')

    return render_template('templates/form.html', form=form, is_edit=True, template=tmpl)


# --------------------------------------------------------------------------
# Archive / Reactivate template (Admin only)
# --------------------------------------------------------------------------

@templates_bp.route('/<int:template_id>/archive', methods=['POST'])
@login_required
@role_required('admin')
def archive(template_id):
    """Archive a template."""
    try:
        template_service.archive_template(template_id)
        flash('Template archived successfully.', 'success')
    except TemplateServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('templates.index'))


@templates_bp.route('/<int:template_id>/reactivate', methods=['POST'])
@login_required
@role_required('admin')
def reactivate(template_id):
    """Reactivate an archived template."""
    try:
        template_service.reactivate_template(template_id)
        flash('Template reactivated successfully.', 'success')
    except TemplateServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('templates.index', archived='1'))


# --------------------------------------------------------------------------
# Artifact management (Admin only)
# --------------------------------------------------------------------------

@templates_bp.route('/<int:template_id>/artifacts/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_artifact(template_id):
    """Add an artifact to a template."""
    tmpl = template_service.get_template_by_id(template_id)
    if tmpl is None:
        flash('Template not found.', 'danger')
        return redirect(url_for('templates.index'))

    form = ArtifactForm()
    if form.validate_on_submit():
        try:
            artifact_type = ArtifactType(form.type.data)
            value_type = None
            if artifact_type == ArtifactType.other and form.value_type.data:
                value_type = ArtifactValueType(form.value_type.data)
            template_service.add_artifact(
                template_id=template_id,
                artifact_type=artifact_type,
                name=form.name.data,
                description=form.description.data,
                value_type=value_type,
                is_required=form.is_required.data,
                display_order=form.display_order.data or 0,
            )
            flash('Artifact added successfully.', 'success')
            return redirect(url_for('templates.detail', template_id=template_id))
        except (TemplateServiceError, ValueError) as exc:
            flash(str(exc), 'danger')

    return render_template(
        'templates/artifact_form.html',
        form=form,
        template=tmpl,
        is_edit=False,
    )


@templates_bp.route('/<int:template_id>/artifacts/<int:artifact_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_artifact(template_id, artifact_id):
    """Edit an existing artifact."""
    tmpl = template_service.get_template_by_id(template_id)
    if tmpl is None:
        flash('Template not found.', 'danger')
        return redirect(url_for('templates.index'))

    from ..models.template import TemplateArtifact
    artifact = TemplateArtifact.query.filter_by(id=artifact_id, template_id=template_id).first()
    if artifact is None:
        flash('Artifact not found.', 'danger')
        return redirect(url_for('templates.detail', template_id=template_id))

    form = ArtifactForm(obj=artifact)

    if request.method == 'GET':
        form.type.data = artifact.type.value
        form.name.data = artifact.name
        form.description.data = artifact.description
        form.value_type.data = artifact.value_type.value if artifact.value_type else ''
        form.is_required.data = artifact.is_required
        form.display_order.data = artifact.display_order

    if form.validate_on_submit():
        try:
            template_service.update_artifact(
                artifact_id=artifact_id,
                name=form.name.data,
                description=form.description.data,
                is_required=form.is_required.data,
                display_order=form.display_order.data or 0,
            )
            flash('Artifact updated successfully.', 'success')
            return redirect(url_for('templates.detail', template_id=template_id))
        except TemplateServiceError as exc:
            flash(str(exc), 'danger')

    return render_template(
        'templates/artifact_form.html',
        form=form,
        template=tmpl,
        artifact=artifact,
        is_edit=True,
    )


@templates_bp.route('/<int:template_id>/artifacts/<int:artifact_id>/remove', methods=['POST'])
@login_required
@role_required('admin')
def remove_artifact(template_id, artifact_id):
    """Remove an artifact from a template."""
    try:
        template_service.remove_artifact(artifact_id)
        flash('Artifact removed successfully.', 'success')
    except TemplateServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('templates.detail', template_id=template_id))


# --------------------------------------------------------------------------
# List option management (Admin only)
# --------------------------------------------------------------------------

@templates_bp.route(
    '/<int:template_id>/artifacts/<int:artifact_id>/options/new',
    methods=['GET', 'POST'],
)
@login_required
@role_required('admin')
def add_list_option(template_id, artifact_id):
    """Add a list option to an Other:list artifact."""
    tmpl = template_service.get_template_by_id(template_id)
    if tmpl is None:
        flash('Template not found.', 'danger')
        return redirect(url_for('templates.index'))

    from ..models.template import TemplateArtifact
    artifact = TemplateArtifact.query.filter_by(id=artifact_id, template_id=template_id).first()
    if artifact is None:
        flash('Artifact not found.', 'danger')
        return redirect(url_for('templates.detail', template_id=template_id))

    form = ListOptionForm()
    if form.validate_on_submit():
        try:
            template_service.add_list_option(
                artifact_id=artifact_id,
                value=form.value.data,
                display_order=form.display_order.data or 0,
            )
            flash('List option added successfully.', 'success')
            return redirect(url_for('templates.detail', template_id=template_id))
        except TemplateServiceError as exc:
            flash(str(exc), 'danger')

    return render_template(
        'templates/list_option_form.html',
        form=form,
        template=tmpl,
        artifact=artifact,
        is_edit=False,
    )


@templates_bp.route(
    '/<int:template_id>/artifacts/<int:artifact_id>/options/<int:option_id>/edit',
    methods=['GET', 'POST'],
)
@login_required
@role_required('admin')
def edit_list_option(template_id, artifact_id, option_id):
    """Edit an existing list option."""
    tmpl = template_service.get_template_by_id(template_id)
    if tmpl is None:
        flash('Template not found.', 'danger')
        return redirect(url_for('templates.index'))

    from ..models.template import ArtifactListOption, TemplateArtifact
    artifact = TemplateArtifact.query.filter_by(id=artifact_id, template_id=template_id).first()
    if artifact is None:
        flash('Artifact not found.', 'danger')
        return redirect(url_for('templates.detail', template_id=template_id))

    option = ArtifactListOption.query.filter_by(id=option_id, artifact_id=artifact_id).first()
    if option is None:
        flash('List option not found.', 'danger')
        return redirect(url_for('templates.detail', template_id=template_id))

    form = ListOptionForm(obj=option)
    if request.method == 'GET':
        form.value.data = option.value
        form.display_order.data = option.display_order

    if form.validate_on_submit():
        try:
            template_service.update_list_option(
                option_id=option_id,
                value=form.value.data,
                display_order=form.display_order.data or 0,
            )
            flash('List option updated successfully.', 'success')
            return redirect(url_for('templates.detail', template_id=template_id))
        except TemplateServiceError as exc:
            flash(str(exc), 'danger')

    return render_template(
        'templates/list_option_form.html',
        form=form,
        template=tmpl,
        artifact=artifact,
        option=option,
        is_edit=True,
    )


@templates_bp.route(
    '/<int:template_id>/artifacts/<int:artifact_id>/options/<int:option_id>/deactivate',
    methods=['POST'],
)
@login_required
@role_required('admin')
def deactivate_list_option(template_id, artifact_id, option_id):
    """Deactivate a list option."""
    try:
        template_service.deactivate_list_option(option_id)
        flash('List option deactivated.', 'success')
    except TemplateServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('templates.detail', template_id=template_id))


@templates_bp.route(
    '/<int:template_id>/artifacts/<int:artifact_id>/options/<int:option_id>/delete',
    methods=['POST'],
)
@login_required
@role_required('admin')
def delete_list_option(template_id, artifact_id, option_id):
    """Delete a list option if unused."""
    try:
        template_service.delete_list_option(option_id)
        flash('List option deleted.', 'success')
    except TemplateServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('templates.detail', template_id=template_id))
