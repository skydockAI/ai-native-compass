"""AuditLog model — permanent, immutable record of all system events (REQ-048, REQ-059, REQ-060)."""

from datetime import datetime, timezone

from sqlalchemy import Index

from ..extensions import db


class AuditLog(db.Model):
    """Permanent audit log entry.

    Entries are never deleted or archived.  ``user_id`` is nullable to support
    system-generated events (e.g., admin seeding on startup).

    entity_type values: user, team, product, repository, template, session
    action values: login, logout, create, update, archive, reactivate,
                   role_change, template_change
    """

    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)
    before_value = db.Column(db.JSON, nullable=True)
    after_value = db.Column(db.JSON, nullable=True)

    # Relationship for convenient access to the acting user
    actor = db.relationship('User', foreign_keys=[user_id], lazy='joined')

    __table_args__ = (
        Index('ix_audit_log_timestamp', 'timestamp'),
        Index('ix_audit_log_entity', 'entity_type', 'entity_id'),
        Index('ix_audit_log_user_id', 'user_id'),
    )

    def __repr__(self) -> str:
        return f'<AuditLog {self.action} {self.entity_type}:{self.entity_id}>'
