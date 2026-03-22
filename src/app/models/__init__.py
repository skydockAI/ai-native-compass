from ..extensions import db
from sqlalchemy import func


class BaseModel(db.Model):
    """Abstract base model with common fields for all business entities.

    Provides soft-delete support (REQ-046), timestamps, and optimistic locking (REQ-069).
    """
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default='true')
    is_archived = db.Column(db.Boolean, nullable=False, default=False, server_default='false')
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    version = db.Column(db.Integer, nullable=False, default=1, server_default='1')
