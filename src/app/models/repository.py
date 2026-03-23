"""Repository models (REQ-021, REQ-027, REQ-028, REQ-029, REQ-030)."""

from ..extensions import db
from . import BaseModel

# ---------------------------------------------------------------------------
# product_repository M:N association table (DI-007; linking UI in DI-009)
# ---------------------------------------------------------------------------
# Note: product_id has no FK to products.id here because the products table
# is created in DI-009.  The FK constraint will be added via a migration in
# DI-009 (same pattern as RepositorySharedAttributeValue.repository_id in DI-006).

product_repository = db.Table(
    'product_repository',
    db.Column('product_id', db.Integer, nullable=False),
    db.Column(
        'repository_id',
        db.Integer,
        db.ForeignKey('repositories.id', ondelete='CASCADE'),
        nullable=False,
    ),
    db.UniqueConstraint('product_id', 'repository_id', name='uq_product_repository'),
)


class Repository(BaseModel):
    """Repository entity (REQ-027).

    Template assignment is immutable after creation (REQ-029).
    URL is globally unique across active and archived repositories (REQ-028).
    Every repository must belong to exactly one active Team (REQ-021).
    """

    __tablename__ = 'repositories'

    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(2048), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    team_id = db.Column(
        db.Integer,
        db.ForeignKey('teams.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    template_id = db.Column(
        db.Integer,
        db.ForeignKey('repo_templates.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )

    team = db.relationship('Team', lazy='select')
    template = db.relationship('RepoTemplate', lazy='select')

    artifact_values = db.relationship(
        'RepositoryArtifactValue',
        back_populates='repository',
        cascade='all, delete-orphan',
        lazy='select',
    )

    shared_attr_values = db.relationship(
        'RepositorySharedAttributeValue',
        primaryjoin='Repository.id == foreign(RepositorySharedAttributeValue.repository_id)',
        lazy='select',
        overlaps='attribute',
    )

    def __repr__(self) -> str:
        return f'<Repository {self.name}>'


class RepositoryArtifactValue(db.Model):
    """Typed EAV row storing a repository's value for one template artifact (REQ-027, REQ-030).

    Typed columns per architecture Section 4.2:
    - Document / Skill / Agent  → value_text ('Yes' / 'No' / 'N/A')
    - Other:text                → value_text
    - Other:number              → value_number
    - Other:boolean             → value_boolean (nullable tri-state)
    - Other:list                → value_list_option_id (FK → ArtifactListOption)
    """

    __tablename__ = 'repository_artifact_values'

    id = db.Column(db.Integer, primary_key=True)
    repository_id = db.Column(
        db.Integer,
        db.ForeignKey('repositories.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    template_artifact_id = db.Column(
        db.Integer,
        db.ForeignKey('template_artifacts.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    value_text = db.Column(db.Text, nullable=True)
    value_number = db.Column(db.Numeric(18, 6), nullable=True)
    value_boolean = db.Column(db.Boolean, nullable=True)
    value_list_option_id = db.Column(
        db.Integer,
        db.ForeignKey('artifact_list_options.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        db.UniqueConstraint(
            'repository_id', 'template_artifact_id',
            name='uq_repo_artifact_value',
        ),
    )

    repository = db.relationship('Repository', back_populates='artifact_values')
    artifact = db.relationship('TemplateArtifact', lazy='select')
    list_option = db.relationship('ArtifactListOption', lazy='select')

    def __repr__(self) -> str:
        return f'<RepositoryArtifactValue repo={self.repository_id} artifact={self.template_artifact_id}>'
