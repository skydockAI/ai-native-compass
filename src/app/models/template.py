"""Repo Template models (REQ-031, REQ-037, REQ-039, REQ-041)."""

import enum

from sqlalchemy import func

from ..extensions import db
from . import BaseModel


class ArtifactType(enum.Enum):
    """Artifact classification types (REQ-037)."""
    document = 'document'
    skill = 'skill'
    agent = 'agent'
    other = 'other'


class ArtifactValueType(enum.Enum):
    """Value types for Other-type artifacts (REQ-039)."""
    text = 'text'
    number = 'number'
    boolean = 'boolean'
    list = 'list'


class RepoTemplate(BaseModel):
    """Repo Template entity (REQ-031, REQ-032)."""

    __tablename__ = 'repo_templates'

    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    artifacts = db.relationship(
        'TemplateArtifact',
        back_populates='template',
        order_by='TemplateArtifact.display_order',
        cascade='all, delete-orphan',
        lazy='select',
    )

    def __repr__(self) -> str:
        return f'<RepoTemplate {self.name}>'


class TemplateArtifact(BaseModel):
    """Artifact definition within a Repo Template (REQ-037, REQ-038, REQ-039, REQ-040)."""

    __tablename__ = 'template_artifacts'

    template_id = db.Column(
        db.Integer,
        db.ForeignKey('repo_templates.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    type = db.Column(db.Enum(ArtifactType, native_enum=False), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.Enum(ArtifactValueType, native_enum=False), nullable=True)
    is_required = db.Column(db.Boolean, nullable=False, default=False, server_default='false')
    display_order = db.Column(db.Integer, nullable=False, default=0, server_default='0')

    template = db.relationship('RepoTemplate', back_populates='artifacts')
    list_options = db.relationship(
        'ArtifactListOption',
        back_populates='artifact',
        order_by='ArtifactListOption.display_order',
        cascade='all, delete-orphan',
        lazy='select',
    )

    def __repr__(self) -> str:
        return f'<TemplateArtifact {self.name} ({self.type.value})>'


class ArtifactListOption(db.Model):
    """Option entry for Other:list artifacts (REQ-041).

    Does not extend BaseModel because it has its own minimal schema and
    lifecycle is managed differently (add/deactivate/delete, no version lock).
    """

    __tablename__ = 'artifact_list_options'

    id = db.Column(db.Integer, primary_key=True)
    artifact_id = db.Column(
        db.Integer,
        db.ForeignKey('template_artifacts.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    value = db.Column(db.String(255), nullable=False)
    display_order = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default='true')
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.now(),
    )

    artifact = db.relationship('TemplateArtifact', back_populates='list_options')

    def __repr__(self) -> str:
        return f'<ArtifactListOption {self.value}>'
