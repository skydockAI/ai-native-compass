from ..extensions import db
from . import BaseModel


class Team(BaseModel):
    """Team entity for categorising Repositories (REQ-019, REQ-020)."""

    __tablename__ = 'teams'

    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    def to_audit_dict(self) -> dict:
        """Return auditable fields as a plain dict for before/after capture."""
        return {
            'name': self.name,
            'description': self.description,
            'is_archived': self.is_archived,
            'is_active': self.is_active,
        }

    def __repr__(self) -> str:
        return f'<Team {self.name}>'
