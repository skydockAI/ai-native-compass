import enum

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from . import BaseModel


class UserRole(enum.Enum):
    ADMIN = 'admin'
    EDITOR = 'editor'
    VIEWER = 'viewer'


class User(BaseModel, UserMixin):
    """User account with local authentication and role-based access (REQ-016)."""

    __tablename__ = 'users'

    email = db.Column(db.String(255), nullable=False, unique=True)
    full_name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole, native_enum=False), nullable=False, default=UserRole.VIEWER)
    is_seeded = db.Column(
        db.Boolean, nullable=False, default=False, server_default='false'
    )

    # ------------------------------------------------------------------
    # Password helpers
    # ------------------------------------------------------------------

    def set_password(self, password: str) -> None:
        """Hash and store *password*. Raises ``ValueError`` if shorter than 8 chars."""
        if len(password) < 8:
            raise ValueError('Password must be at least 8 characters long.')
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Return ``True`` when *password* matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    # ------------------------------------------------------------------
    # Email normalisation
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_email(email: str) -> str:
        """Return *email* stripped and lowercased for case-insensitive uniqueness."""
        return email.strip().lower()

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Flask-Login interface
    # ------------------------------------------------------------------

    # Inheritance order ``(BaseModel, UserMixin)`` ensures SQLAlchemy's
    # ``InstrumentedAttribute`` for ``is_active`` (from ``BaseModel``) takes
    # precedence over ``UserMixin.is_active`` (which always returns ``True``).
    # Flask-Login reads ``user.is_active`` when ``login_user()`` is called;
    # the ``before_request`` hook additionally checks ``is_archived`` every request.

    def __repr__(self) -> str:
        return f'<User {self.email}>'
