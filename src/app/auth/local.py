"""Local email/password authentication strategy (REQ-001, REQ-002, REQ-010)."""

from ..models.user import User


def authenticate_user(email: str, password: str):
    """Verify *email* + *password* and return the matching :class:`User`.

    Returns ``None`` for **any** failure — invalid email, wrong password, or
    inactive/archived account — so that error messages never reveal which
    field was incorrect (REQ-001).
    """
    normalized = User.normalize_email(email)
    user = User.query.filter_by(email=normalized).first()

    if user is None:
        return None

    if not user.check_password(password):
        return None

    if not user.is_active or user.is_archived:
        return None

    return user
