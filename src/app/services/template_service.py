"""Template management business logic (REQ-031, REQ-032, REQ-033, REQ-037–041, REQ-049)."""

from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models.template import ArtifactListOption, ArtifactType, ArtifactValueType, RepoTemplate, TemplateArtifact


class TemplateServiceError(Exception):
    """Raised when a template operation fails with a user-facing message."""


# ---------------------------------------------------------------------------
# Template CRUD
# ---------------------------------------------------------------------------

def get_templates(include_archived=False):
    """Return templates, optionally including archived ones."""
    query = RepoTemplate.query.order_by(RepoTemplate.name)
    if not include_archived:
        query = query.filter_by(is_archived=False)
    return query.all()


def get_template_by_id(template_id):
    """Return a single template by primary key or ``None``."""
    return db.session.get(RepoTemplate, template_id)


def create_template(name, description=None):
    """Create a new template after validating name uniqueness (REQ-032).

    Returns the newly created ``RepoTemplate`` on success.
    Raises ``TemplateServiceError`` on validation failure.
    """
    name = name.strip() if name else ''
    if not name:
        raise TemplateServiceError('Template name is required.')

    existing = RepoTemplate.query.filter(
        db.func.lower(RepoTemplate.name) == name.lower()
    ).first()
    if existing:
        raise TemplateServiceError(
            f'A template named "{name}" already exists. Please choose a different name.'
        )

    template = RepoTemplate(name=name, description=description or None)
    try:
        db.session.add(template)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise TemplateServiceError(
            f'A template named "{name}" already exists. Please choose a different name.'
        )
    return template


def update_template(template_id, name, description, expected_version):
    """Update an existing template with optimistic locking.

    Raises ``TemplateServiceError`` on validation or concurrency failure.
    """
    template = db.session.get(RepoTemplate, template_id)
    if template is None:
        raise TemplateServiceError('Template not found.')

    if template.version != expected_version:
        raise TemplateServiceError(
            'This record has been modified by another user. '
            'Please reload and try again.'
        )

    name = name.strip() if name else ''
    if not name:
        raise TemplateServiceError('Template name is required.')

    existing = RepoTemplate.query.filter(
        db.func.lower(RepoTemplate.name) == name.lower(),
        RepoTemplate.id != template_id,
    ).first()
    if existing:
        raise TemplateServiceError(
            f'A template named "{name}" already exists. Please choose a different name.'
        )

    template.name = name
    template.description = description or None
    template.version += 1
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise TemplateServiceError(
            f'A template named "{name}" already exists. Please choose a different name.'
        )
    return template


def archive_template(template_id):
    """Soft-delete a template (REQ-046).

    Checks for active repositories using this template before archiving (REQ-033, REQ-049).
    Raises ``TemplateServiceError`` if blocking repositories exist.
    """
    template = db.session.get(RepoTemplate, template_id)
    if template is None:
        raise TemplateServiceError('Template not found.')

    if template.is_archived:
        raise TemplateServiceError('Template is already archived.')

    blocking_repos = _get_blocking_repositories(template)
    if blocking_repos:
        names = ', '.join(r.name for r in blocking_repos)
        raise TemplateServiceError(
            f'Cannot archive template "{template.name}": the following active repositories '
            f'are still using it: {names}. '
            'Archive or reassign those repositories first.'
        )

    template.is_archived = True
    template.is_active = False
    template.version += 1
    db.session.commit()
    return template


def reactivate_template(template_id):
    """Restore an archived template."""
    template = db.session.get(RepoTemplate, template_id)
    if template is None:
        raise TemplateServiceError('Template not found.')

    if not template.is_archived:
        raise TemplateServiceError('Template is not archived.')

    template.is_archived = False
    template.is_active = True
    template.version += 1
    db.session.commit()
    return template


# ---------------------------------------------------------------------------
# Artifact CRUD
# ---------------------------------------------------------------------------

def add_artifact(template_id, artifact_type, name, description=None,
                 value_type=None, is_required=False, display_order=0):
    """Add an artifact to a template (REQ-037, REQ-038, REQ-039, REQ-040).

    ``artifact_type`` must be an ``ArtifactType`` enum value.
    ``value_type`` must be an ``ArtifactValueType`` enum value or ``None``.
    ``is_required`` is only honoured for Other-type artifacts.
    """
    template = db.session.get(RepoTemplate, template_id)
    if template is None:
        raise TemplateServiceError('Template not found.')

    name = name.strip() if name else ''
    if not name:
        raise TemplateServiceError('Artifact name is required.')

    if not isinstance(artifact_type, ArtifactType):
        raise TemplateServiceError('Invalid artifact type.')

    # value_type is only valid for Other type
    if artifact_type != ArtifactType.other:
        value_type = None
        is_required = False
    else:
        if value_type is None:
            raise TemplateServiceError('Value type is required for Other artifacts.')
        if not isinstance(value_type, ArtifactValueType):
            raise TemplateServiceError('Invalid value type.')

    artifact = TemplateArtifact(
        template_id=template_id,
        type=artifact_type,
        name=name,
        description=description or None,
        value_type=value_type,
        is_required=bool(is_required),
        display_order=int(display_order),
    )
    db.session.add(artifact)
    db.session.commit()
    return artifact


def update_artifact(artifact_id, name, description=None, is_required=False, display_order=0):
    """Update artifact name, description, is_required, and display_order."""
    artifact = db.session.get(TemplateArtifact, artifact_id)
    if artifact is None:
        raise TemplateServiceError('Artifact not found.')

    name = name.strip() if name else ''
    if not name:
        raise TemplateServiceError('Artifact name is required.')

    artifact.name = name
    artifact.description = description or None
    # is_required only meaningful for Other type
    if artifact.type == ArtifactType.other:
        artifact.is_required = bool(is_required)
    artifact.display_order = int(display_order)
    artifact.version += 1
    db.session.commit()
    return artifact


def remove_artifact(artifact_id):
    """Hard-delete an artifact from a template."""
    artifact = db.session.get(TemplateArtifact, artifact_id)
    if artifact is None:
        raise TemplateServiceError('Artifact not found.')
    db.session.delete(artifact)
    db.session.commit()


# ---------------------------------------------------------------------------
# List option management
# ---------------------------------------------------------------------------

def add_list_option(artifact_id, value, display_order=0):
    """Add a list option to an Other:list artifact (REQ-041)."""
    artifact = db.session.get(TemplateArtifact, artifact_id)
    if artifact is None:
        raise TemplateServiceError('Artifact not found.')
    if artifact.type != ArtifactType.other or artifact.value_type != ArtifactValueType.list:
        raise TemplateServiceError('List options are only valid for Other:list artifacts.')

    value = value.strip() if value else ''
    if not value:
        raise TemplateServiceError('Option value is required.')

    option = ArtifactListOption(
        artifact_id=artifact_id,
        value=value,
        display_order=int(display_order),
    )
    db.session.add(option)
    db.session.commit()
    return option


def update_list_option(option_id, value, display_order=0):
    """Update a list option's value and display_order."""
    option = db.session.get(ArtifactListOption, option_id)
    if option is None:
        raise TemplateServiceError('List option not found.')

    value = value.strip() if value else ''
    if not value:
        raise TemplateServiceError('Option value is required.')

    option.value = value
    option.display_order = int(display_order)
    db.session.commit()
    return option


def deactivate_list_option(option_id):
    """Deactivate a list option (hidden from new selections, preserved on existing records)."""
    option = db.session.get(ArtifactListOption, option_id)
    if option is None:
        raise TemplateServiceError('List option not found.')
    option.is_active = False
    db.session.commit()
    return option


def delete_list_option(option_id):
    """Hard-delete a list option only if it is not in use by any repository (REQ-041).

    Until DI-007 introduces RepositoryArtifactValue, all options are considered unused.
    """
    option = db.session.get(ArtifactListOption, option_id)
    if option is None:
        raise TemplateServiceError('List option not found.')

    if _is_list_option_in_use(option):
        raise TemplateServiceError(
            f'Cannot delete option "{option.value}": it is currently selected by one or more '
            'active repositories. Deactivate it instead.'
        )

    db.session.delete(option)
    db.session.commit()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_blocking_repositories(template):
    """Return list of active repositories blocking archive of *template*.

    Once DI-007 introduces the Repository model with a ``template_id`` FK,
    replace the stub with:

        from ..models.repository import Repository
        return Repository.query.filter_by(template_id=template.id, is_archived=False).all()
    """
    try:
        from ..models.repository import Repository  # noqa: F401 — available post DI-007
        return Repository.query.filter_by(template_id=template.id, is_archived=False).all()
    except ImportError:
        return []


def _is_list_option_in_use(option):
    """Return True if the option is referenced by any repository artifact value."""
    try:
        from ..models.repository import RepositoryArtifactValue
        return RepositoryArtifactValue.query.filter_by(
            value_list_option_id=option.id
        ).first() is not None
    except ImportError:
        return False
