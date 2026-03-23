"""Shared attribute management business logic (REQ-034, REQ-035, REQ-036)."""

from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models.shared_attribute import SharedAttributeDefinition


class SharedAttributeServiceError(Exception):
    """Raised when a shared attribute operation fails with a user-facing message."""


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def get_attributes(include_inactive=False, custom_only=False):
    """Return shared attribute definitions ordered by defaults first, then name.

    By default only active attributes are returned.
    Pass ``custom_only=True`` to exclude the four default attributes (Name, Team,
    URL, Description) — used in repository pages where those are already rendered
    as native model fields (REQ-034).
    """
    query = SharedAttributeDefinition.query.order_by(
        SharedAttributeDefinition.is_default.desc(),
        SharedAttributeDefinition.name,
    )
    if not include_inactive:
        query = query.filter_by(is_active=True)
    if custom_only:
        query = query.filter_by(is_default=False)
    return query.all()


def get_attribute_by_id(attr_id):
    """Return a single SharedAttributeDefinition by primary key or ``None``."""
    return db.session.get(SharedAttributeDefinition, attr_id)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def create_attribute(name):
    """Create a new custom shared attribute (REQ-035).

    Custom attributes are text-only and marked ``is_default=False``.
    Raises ``SharedAttributeServiceError`` on validation failure.
    """
    name = name.strip() if name else ''
    if not name:
        raise SharedAttributeServiceError('Attribute name is required.')

    existing = SharedAttributeDefinition.query.filter(
        db.func.lower(SharedAttributeDefinition.name) == name.lower()
    ).first()
    if existing:
        raise SharedAttributeServiceError(
            f'A shared attribute named "{name}" already exists.'
        )

    attr = SharedAttributeDefinition(name=name, is_default=False, is_active=True)
    try:
        db.session.add(attr)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise SharedAttributeServiceError(
            f'A shared attribute named "{name}" already exists.'
        )
    return attr


def update_attribute(attr_id, name):
    """Rename a custom shared attribute (REQ-035).

    Raises ``SharedAttributeServiceError`` if the attribute is a default (REQ-036),
    does not exist, or the new name conflicts with an existing attribute.
    """
    attr = db.session.get(SharedAttributeDefinition, attr_id)
    if attr is None:
        raise SharedAttributeServiceError('Shared attribute not found.')

    if attr.is_default:
        raise SharedAttributeServiceError(
            f'"{attr.name}" is a default attribute and cannot be renamed (REQ-036).'
        )

    name = name.strip() if name else ''
    if not name:
        raise SharedAttributeServiceError('Attribute name is required.')

    existing = SharedAttributeDefinition.query.filter(
        db.func.lower(SharedAttributeDefinition.name) == name.lower(),
        SharedAttributeDefinition.id != attr_id,
    ).first()
    if existing:
        raise SharedAttributeServiceError(
            f'A shared attribute named "{name}" already exists.'
        )

    attr.name = name
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise SharedAttributeServiceError(
            f'A shared attribute named "{name}" already exists.'
        )
    return attr


def deactivate_attribute(attr_id):
    """Deactivate a custom shared attribute (REQ-035).

    Raises ``SharedAttributeServiceError`` if the attribute is a default (REQ-036).
    """
    attr = db.session.get(SharedAttributeDefinition, attr_id)
    if attr is None:
        raise SharedAttributeServiceError('Shared attribute not found.')

    if attr.is_default:
        raise SharedAttributeServiceError(
            f'"{attr.name}" is a default attribute and cannot be deactivated (REQ-036).'
        )

    if not attr.is_active:
        raise SharedAttributeServiceError('Attribute is already inactive.')

    attr.is_active = False
    db.session.commit()
    return attr


def reactivate_attribute(attr_id):
    """Reactivate a previously deactivated custom shared attribute."""
    attr = db.session.get(SharedAttributeDefinition, attr_id)
    if attr is None:
        raise SharedAttributeServiceError('Shared attribute not found.')

    if attr.is_active:
        raise SharedAttributeServiceError('Attribute is already active.')

    attr.is_active = True
    db.session.commit()
    return attr
