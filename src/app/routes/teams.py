"""Team management routes (REQ-019, REQ-020, REQ-022)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from ..authz import role_required
from ..services import team_service
from ..services.team_service import TeamServiceError
from .forms import TeamCreateForm, TeamEditForm

teams_bp = Blueprint('teams', __name__, url_prefix='/teams')


# --------------------------------------------------------------------------
# Team list (all authenticated users)
# --------------------------------------------------------------------------

@teams_bp.route('/')
@login_required
def index():
    """Team list with active/archived filter (REQ-058)."""
    show_archived = request.args.get('archived', '0') == '1'
    teams = team_service.get_teams(include_archived=show_archived)
    ctx = dict(teams=teams, show_archived=show_archived)
    if request.headers.get('HX-Request'):
        return render_template('teams/partials/team_list.html', **ctx)
    return render_template('teams/list.html', **ctx)


# --------------------------------------------------------------------------
# Create team (Admin + Editor)
# --------------------------------------------------------------------------

@teams_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'editor')
def create():
    """Display and process new-team form."""
    form = TeamCreateForm()
    if form.validate_on_submit():
        try:
            team_service.create_team(
                name=form.name.data,
                description=form.description.data,
            )
            flash('Team created successfully.', 'success')
            return redirect(url_for('teams.index'))
        except TeamServiceError as exc:
            flash(str(exc), 'danger')

    return render_template('teams/form.html', form=form, is_edit=False)


# --------------------------------------------------------------------------
# Edit team (Admin + Editor)
# --------------------------------------------------------------------------

@teams_bp.route('/<int:team_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'editor')
def edit(team_id):
    """Display and process edit-team form."""
    team = team_service.get_team_by_id(team_id)
    if team is None:
        flash('Team not found.', 'danger')
        return redirect(url_for('teams.index'))

    form = TeamEditForm(obj=team)

    if request.method == 'GET':
        form.name.data = team.name
        form.description.data = team.description
        form.version.data = team.version

    if form.validate_on_submit():
        try:
            team_service.update_team(
                team_id=team_id,
                name=form.name.data,
                description=form.description.data,
                expected_version=int(form.version.data),
            )
            flash('Team updated successfully.', 'success')
            return redirect(url_for('teams.index'))
        except TeamServiceError as exc:
            flash(str(exc), 'danger')

    return render_template('teams/form.html', form=form, is_edit=True, team=team)


# --------------------------------------------------------------------------
# Archive / Reactivate team (Admin + Editor)
# --------------------------------------------------------------------------

@teams_bp.route('/<int:team_id>/archive', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def archive(team_id):
    """Archive a team."""
    try:
        team_service.archive_team(team_id)
        flash('Team archived successfully.', 'success')
    except TeamServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('teams.index'))


@teams_bp.route('/<int:team_id>/reactivate', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def reactivate(team_id):
    """Reactivate an archived team."""
    try:
        team_service.reactivate_team(team_id)
        flash('Team reactivated successfully.', 'success')
    except TeamServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('teams.index', archived='1'))
