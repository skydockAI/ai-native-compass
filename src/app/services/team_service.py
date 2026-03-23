"""Team management business logic (REQ-019, REQ-020, REQ-022, REQ-049)."""

from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models.team import Team
from . import audit_service


class TeamServiceError(Exception):
    """Raised when a team operation fails with a user-facing message."""


def get_teams(include_archived=False):
    """Return teams, optionally including archived ones."""
    query = Team.query.order_by(Team.name)
    if not include_archived:
        query = query.filter_by(is_archived=False)
    return query.all()


def get_team_by_id(team_id):
    """Return a single team by primary key or ``None``."""
    return db.session.get(Team, team_id)


def create_team(name, description=None):
    """Create a new team after validating name uniqueness (REQ-020).

    Returns the newly created ``Team`` on success.
    Raises ``TeamServiceError`` on validation failure.
    """
    name = name.strip() if name else ''
    if not name:
        raise TeamServiceError('Team name is required.')

    existing = Team.query.filter(
        db.func.lower(Team.name) == name.lower()
    ).first()
    if existing:
        raise TeamServiceError(
            f'A team named "{name}" already exists. Please choose a different name.'
        )

    team = Team(name=name, description=description or None)
    try:
        db.session.add(team)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise TeamServiceError(
            f'A team named "{name}" already exists. Please choose a different name.'
        )
    actor_id = current_user.id if current_user.is_authenticated else None
    audit_service.log('create', 'team', team.id, before=None, after=team.to_audit_dict(), user_id=actor_id)
    return team


def update_team(team_id, name, description, expected_version):
    """Update an existing team with optimistic locking.

    Raises ``TeamServiceError`` on validation or concurrency failure.
    """
    team = db.session.get(Team, team_id)
    if team is None:
        raise TeamServiceError('Team not found.')

    if team.version != expected_version:
        raise TeamServiceError(
            'This record has been modified by another user. '
            'Please reload and try again.'
        )

    name = name.strip() if name else ''
    if not name:
        raise TeamServiceError('Team name is required.')

    # Uniqueness check excluding current team
    existing = Team.query.filter(
        db.func.lower(Team.name) == name.lower(),
        Team.id != team_id,
    ).first()
    if existing:
        raise TeamServiceError(
            f'A team named "{name}" already exists. Please choose a different name.'
        )

    before = team.to_audit_dict()
    team.name = name
    team.description = description or None
    team.version += 1
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise TeamServiceError(
            f'A team named "{name}" already exists. Please choose a different name.'
        )
    actor_id = current_user.id if current_user.is_authenticated else None
    audit_service.log('update', 'team', team.id, before=before, after=team.to_audit_dict(), user_id=actor_id)
    return team


def archive_team(team_id):
    """Soft-delete a team (REQ-046).

    Checks for active repositories assigned to this team before archiving (REQ-022, REQ-049).
    Returns ``(team, blocking_repos)`` where ``blocking_repos`` is a list of
    active repository names blocking the archive.  If the list is non-empty,
    the archive is denied and a ``TeamServiceError`` is raised.

    Note: Until DI-007 (Repository entity) is implemented the blocking check
    always returns an empty list, so archive always succeeds.
    """
    team = db.session.get(Team, team_id)
    if team is None:
        raise TeamServiceError('Team not found.')

    if team.is_archived:
        raise TeamServiceError('Team is already archived.')

    blocking_repos = _get_blocking_repositories(team)
    if blocking_repos:
        names = ', '.join(r.name for r in blocking_repos)
        raise TeamServiceError(
            f'Cannot archive team "{team.name}": the following active repositories '
            f'are still assigned to it: {names}. '
            'Archive or reassign those repositories first.'
        )

    before = team.to_audit_dict()
    team.is_archived = True
    team.is_active = False
    team.version += 1
    db.session.commit()
    actor_id = current_user.id if current_user.is_authenticated else None
    audit_service.log('archive', 'team', team.id, before=before, after=team.to_audit_dict(), user_id=actor_id)
    return team


def reactivate_team(team_id):
    """Restore an archived team."""
    team = db.session.get(Team, team_id)
    if team is None:
        raise TeamServiceError('Team not found.')

    if not team.is_archived:
        raise TeamServiceError('Team is not archived.')

    before = team.to_audit_dict()
    team.is_archived = False
    team.is_active = True
    team.version += 1
    db.session.commit()
    actor_id = current_user.id if current_user.is_authenticated else None
    audit_service.log('reactivate', 'team', team.id, before=before, after=team.to_audit_dict(), user_id=actor_id)
    return team


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_blocking_repositories(team):
    """Return list of active repositories blocking archive of *team*.

    Once DI-007 introduces the Repository model with a ``team_id`` foreign key,
    replace this stub with:

        from ..models.repository import Repository
        return Repository.query.filter_by(team_id=team.id, is_archived=False).all()
    """
    try:
        from ..models.repository import Repository  # noqa: F401 — available post DI-007
        return Repository.query.filter_by(team_id=team.id, is_archived=False).all()
    except ImportError:
        return []
