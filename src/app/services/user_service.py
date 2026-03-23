"""User management business logic (REQ-005, REQ-006, REQ-016, REQ-017, REQ-018)."""

from ..extensions import db
from ..models.user import User, UserRole


class UserServiceError(Exception):
    """Raised when a user operation fails with a user-facing message."""


def get_users(include_archived=False):
    """Return users, optionally including archived ones."""
    query = User.query.order_by(User.full_name)
    if not include_archived:
        query = query.filter_by(is_archived=False)
    return query.all()


def get_user_by_id(user_id):
    """Return a single user by primary key or ``None``."""
    return db.session.get(User, user_id)


def create_user(email, full_name, password, role_value):
    """Create a new user after validating email uniqueness (REQ-017).

    Returns the newly created ``User`` on success.
    Raises ``UserServiceError`` on validation failure.
    """
    email = User.normalize_email(email)
    full_name = full_name.strip()

    if not email:
        raise UserServiceError('Email is required.')
    if not full_name:
        raise UserServiceError('Full name is required.')

    # Case-insensitive email uniqueness — includes archived users (REQ-017)
    existing = User.query.filter(db.func.lower(User.email) == email).first()
    if existing:
        raise UserServiceError('A user with this email address already exists.')

    try:
        role = UserRole(role_value)
    except ValueError:
        raise UserServiceError(f'Invalid role: {role_value}')

    user = User(email=email, full_name=full_name, role=role)
    try:
        user.set_password(password)
    except ValueError as exc:
        raise UserServiceError(str(exc))

    db.session.add(user)
    db.session.commit()
    return user


def update_user(user_id, email, full_name, role_value, expected_version):
    """Update an existing user with optimistic locking.

    Raises ``UserServiceError`` on validation or concurrency failure.
    """
    user = db.session.get(User, user_id)
    if user is None:
        raise UserServiceError('User not found.')

    if user.version != expected_version:
        raise UserServiceError(
            'This record has been modified by another user. '
            'Please reload and try again.'
        )

    # Seeded admin protection (REQ-009)
    if user.is_seeded:
        new_role = UserRole(role_value)
        if new_role != UserRole.ADMIN:
            raise UserServiceError('Seeded admin users cannot be demoted.')

    email = User.normalize_email(email)
    full_name = full_name.strip()

    if not email:
        raise UserServiceError('Email is required.')
    if not full_name:
        raise UserServiceError('Full name is required.')

    # Email uniqueness check excluding current user (REQ-017)
    existing = User.query.filter(
        db.func.lower(User.email) == email,
        User.id != user_id,
    ).first()
    if existing:
        raise UserServiceError('A user with this email address already exists.')

    try:
        role = UserRole(role_value)
    except ValueError:
        raise UserServiceError(f'Invalid role: {role_value}')

    user.email = email
    user.full_name = full_name
    user.role = role
    user.version += 1
    db.session.commit()
    return user


def archive_user(user_id):
    """Soft-delete a user (REQ-046, REQ-047).

    Seeded admins cannot be archived (REQ-009).
    """
    user = db.session.get(User, user_id)
    if user is None:
        raise UserServiceError('User not found.')

    if user.is_seeded:
        raise UserServiceError('Seeded admin users cannot be archived.')

    if user.is_archived:
        raise UserServiceError('User is already archived.')

    user.is_archived = True
    user.is_active = False
    user.version += 1
    db.session.commit()
    return user


def reactivate_user(user_id):
    """Restore an archived user."""
    user = db.session.get(User, user_id)
    if user is None:
        raise UserServiceError('User not found.')

    if not user.is_archived:
        raise UserServiceError('User is not archived.')

    user.is_archived = False
    user.is_active = True
    user.version += 1
    db.session.commit()
    return user


def change_password(user_id, current_password, new_password):
    """Self-service password change (REQ-005).

    Validates the current password before setting the new one.
    """
    user = db.session.get(User, user_id)
    if user is None:
        raise UserServiceError('User not found.')

    if not user.check_password(current_password):
        raise UserServiceError('Current password is incorrect.')

    try:
        user.set_password(new_password)
    except ValueError as exc:
        raise UserServiceError(str(exc))

    user.version += 1
    db.session.commit()
    return user


def admin_reset_password(user_id, new_password):
    """Admin password reset for any user account (REQ-006).

    Does not require current password verification.
    """
    user = db.session.get(User, user_id)
    if user is None:
        raise UserServiceError('User not found.')

    try:
        user.set_password(new_password)
    except ValueError as exc:
        raise UserServiceError(str(exc))

    user.version += 1
    db.session.commit()
    return user
