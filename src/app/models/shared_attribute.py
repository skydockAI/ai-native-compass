"""Shared Repository Attribute models (REQ-034, REQ-035, REQ-036)."""

from sqlalchemy import func

from ..extensions import db


class SharedAttributeDefinition(db.Model):
    """Definition of a shared attribute that applies to all repositories.

    Four default attributes (Name, Team, URL, Description) are seeded on startup
    with ``is_default=True`` and cannot be renamed or removed (REQ-034, REQ-036).
    Custom attributes are created by Admins (REQ-035).
    """

    __tablename__ = 'shared_attribute_definitions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    is_default = db.Column(db.Boolean, nullable=False, default=False, server_default='false')
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default='true')
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    values = db.relationship(
        'RepositorySharedAttributeValue',
        back_populates='attribute',
        cascade='all, delete-orphan',
        lazy='dynamic',
    )

    def __repr__(self) -> str:
        return f'<SharedAttributeDefinition {self.name} default={self.is_default}>'


class RepositorySharedAttributeValue(db.Model):
    """EAV value row linking a repository to a shared attribute definition (REQ-035).

    The ``repository_id`` FK is intentionally left as a plain Integer column here
    (no ForeignKeyConstraint to ``repositories.id``) so that this model can be
    created before the Repository table exists (DI-007).  The FK will be added
    via a migration in DI-007.
    """

    __tablename__ = 'repository_shared_attribute_values'

    id = db.Column(db.Integer, primary_key=True)
    repository_id = db.Column(db.Integer, nullable=False, index=True)
    attribute_id = db.Column(
        db.Integer,
        db.ForeignKey('shared_attribute_definitions.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    value = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('repository_id', 'attribute_id', name='uq_repo_shared_attr'),
    )

    attribute = db.relationship('SharedAttributeDefinition', back_populates='values')

    def __repr__(self) -> str:
        return f'<RepositorySharedAttributeValue repo={self.repository_id} attr={self.attribute_id}>'
