"""Tests for repository service business logic (TS-007 TC-007-003 through TC-007-019)."""

import pytest

from app.models.repository import Repository, RepositoryArtifactValue
from app.models.shared_attribute import SharedAttributeDefinition, RepositorySharedAttributeValue
from app.models.team import Team
from app.models.template import ArtifactType, ArtifactValueType, RepoTemplate, TemplateArtifact
from app.services import repository_service
from app.services.repository_service import RepositoryServiceError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def team(db):
    t = Team(name='Engineering')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def template(db):
    t = RepoTemplate(name='Standard')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def doc_artifact(db, template):
    a = TemplateArtifact(
        template_id=template.id,
        type=ArtifactType.document,
        name='Design Doc',
        display_order=1,
    )
    db.session.add(a)
    db.session.commit()
    return a


@pytest.fixture
def required_text_artifact(db, template):
    a = TemplateArtifact(
        template_id=template.id,
        type=ArtifactType.other,
        name='Owner',
        value_type=ArtifactValueType.text,
        is_required=True,
        display_order=2,
    )
    db.session.add(a)
    db.session.commit()
    return a


@pytest.fixture
def custom_attr(db):
    attr = SharedAttributeDefinition(name='Tech Stack', is_default=False, is_active=True)
    db.session.add(attr)
    db.session.commit()
    return attr


def _make_repo(db, name, url, team, template, artifact_values=None, shared_attr_values=None):
    return repository_service.create_repository(
        name=name,
        url=url,
        team_id=team.id,
        template_id=template.id,
        artifact_values=artifact_values or {},
        shared_attr_values=shared_attr_values or {},
    )


# ---------------------------------------------------------------------------
# TC-007-003: Create repository successfully
# ---------------------------------------------------------------------------

class TestCreateRepository:

    def test_create_basic(self, db, team, template):
        repo = _make_repo(db, 'My Repo', 'https://github.com/org/my-repo', team, template)
        assert repo.id is not None
        assert repo.name == 'My Repo'
        assert repo.url == 'https://github.com/org/my-repo'
        assert repo.team_id == team.id
        assert repo.template_id == template.id
        assert repo.is_active is True
        assert repo.is_archived is False

    def test_artifact_values_created_for_each_active_artifact(self, db, team, template, doc_artifact):
        repo = _make_repo(db, 'AV Repo', 'https://github.com/org/av', team, template,
                          artifact_values={doc_artifact.id: 'Yes'})
        avs = RepositoryArtifactValue.query.filter_by(repository_id=repo.id).all()
        assert len(avs) == 1
        assert avs[0].template_artifact_id == doc_artifact.id
        assert avs[0].value_text == 'Yes'

    # TC-007-014: Shared attribute values stored per repository
    def test_shared_attr_value_stored(self, db, team, template, custom_attr):
        repo = _make_repo(db, 'SA Repo', 'https://github.com/org/sa', team, template,
                          shared_attr_values={custom_attr.id: 'Python, Flask'})
        savs = RepositorySharedAttributeValue.query.filter_by(repository_id=repo.id).all()
        assert len(savs) == 1
        assert savs[0].attribute_id == custom_attr.id
        assert savs[0].value == 'Python, Flask'

    def test_name_required(self, db, team, template):
        with pytest.raises(RepositoryServiceError, match='name is required'):
            repository_service.create_repository(name='', url='https://github.com/org/x', team_id=team.id, template_id=template.id)

    def test_url_required(self, db, team, template):
        with pytest.raises(RepositoryServiceError, match='URL is required'):
            repository_service.create_repository(name='X', url='', team_id=team.id, template_id=template.id)

    # TC-007-008: Team assignment mandatory
    def test_team_required(self, db, template):
        with pytest.raises(RepositoryServiceError, match='Team is required'):
            repository_service.create_repository(name='X', url='https://github.com/org/x', team_id=None, template_id=template.id)

    # TC-007-009: Only active teams allowed
    def test_archived_team_rejected(self, db, team, template):
        team.is_archived = True
        db.session.commit()
        with pytest.raises(RepositoryServiceError, match='archived'):
            repository_service.create_repository(name='X', url='https://github.com/org/x', team_id=team.id, template_id=template.id)

    def test_template_required(self, db, team):
        with pytest.raises(RepositoryServiceError, match='Template is required'):
            repository_service.create_repository(name='X', url='https://github.com/org/x', team_id=team.id, template_id=None)

    def test_archived_template_rejected(self, db, team, template):
        template.is_archived = True
        db.session.commit()
        with pytest.raises(RepositoryServiceError, match='archived'):
            repository_service.create_repository(name='X', url='https://github.com/org/x', team_id=team.id, template_id=template.id)

    # TC-007-012: Required artifact validation on create
    def test_required_artifact_missing_raises(self, db, team, template, required_text_artifact):
        with pytest.raises(RepositoryServiceError, match='required'):
            repository_service.create_repository(
                name='X', url='https://github.com/org/x', team_id=team.id, template_id=template.id,
                artifact_values={},
            )

    def test_required_artifact_provided_succeeds(self, db, team, template, required_text_artifact):
        repo = repository_service.create_repository(
            name='X', url='https://github.com/org/x', team_id=team.id, template_id=template.id,
            artifact_values={required_text_artifact.id: 'Alice'},
        )
        assert repo.id is not None


# ---------------------------------------------------------------------------
# TC-007-004 & 007-005: URL uniqueness
# ---------------------------------------------------------------------------

class TestUrlUniqueness:

    # TC-007-004
    def test_duplicate_url_on_create_rejected(self, db, team, template):
        _make_repo(db, 'Repo A', 'https://github.com/org/dup', team, template)
        with pytest.raises(RepositoryServiceError, match='already exists'):
            _make_repo(db, 'Repo B', 'https://github.com/org/dup', team, template)

    # TC-007-005: includes archived
    def test_duplicate_url_archived_also_rejected(self, db, team, template):
        repo = _make_repo(db, 'Old Repo', 'https://github.com/org/old', team, template)
        repository_service.archive_repository(repo.id)
        with pytest.raises(RepositoryServiceError, match='already exists'):
            _make_repo(db, 'New Repo', 'https://github.com/org/old', team, template)

    # TC-007-006: edit rejected
    def test_duplicate_url_on_edit_rejected(self, db, team, template):
        repo_a = _make_repo(db, 'A', 'https://github.com/org/a', team, template)
        repo_b = _make_repo(db, 'B', 'https://github.com/org/b', team, template)
        with pytest.raises(RepositoryServiceError, match='already exists'):
            repository_service.update_repository(
                repo_id=repo_b.id,
                name='B',
                url='https://github.com/org/a',
                team_id=team.id,
                expected_version=repo_b.version,
            )

    def test_update_same_url_allowed(self, db, team, template):
        repo = _make_repo(db, 'Repo', 'https://github.com/org/same', team, template)
        updated = repository_service.update_repository(
            repo_id=repo.id,
            name='Repo Updated',
            url='https://github.com/org/same',
            team_id=team.id,
            expected_version=repo.version,
        )
        assert updated.name == 'Repo Updated'


# ---------------------------------------------------------------------------
# TC-007-007: Template immutability
# ---------------------------------------------------------------------------

class TestTemplateImmutability:

    def test_template_unchanged_after_update(self, db, team, template):
        repo = _make_repo(db, 'Repo', 'https://github.com/org/r', team, template)
        original_template_id = repo.template_id

        # Create a second template — even if we could pass it, service ignores it
        t2 = RepoTemplate(name='Other Template')
        db.session.add(t2)
        db.session.commit()

        repository_service.update_repository(
            repo_id=repo.id,
            name='Repo',
            url='https://github.com/org/r',
            team_id=team.id,
            expected_version=repo.version,
        )

        from app.extensions import db as _db
        refreshed = _db.session.get(Repository, repo.id)
        assert refreshed.template_id == original_template_id


# ---------------------------------------------------------------------------
# TC-007-010: Team can be changed on edit
# ---------------------------------------------------------------------------

class TestTeamChange:

    def test_team_can_change(self, db, team, template):
        repo = _make_repo(db, 'Repo', 'https://github.com/org/tc', team, template)
        team2 = Team(name='Platform')
        db.session.add(team2)
        db.session.commit()

        updated = repository_service.update_repository(
            repo_id=repo.id,
            name='Repo',
            url='https://github.com/org/tc',
            team_id=team2.id,
            expected_version=repo.version,
        )
        assert updated.team_id == team2.id


# ---------------------------------------------------------------------------
# TC-007-011: Typed columns
# ---------------------------------------------------------------------------

class TestArtifactValueTypedColumns:

    def test_document_stored_as_text(self, db, team, template, doc_artifact):
        repo = _make_repo(db, 'R', 'https://g/a', team, template,
                          artifact_values={doc_artifact.id: 'Yes'})
        av = RepositoryArtifactValue.query.filter_by(
            repository_id=repo.id, template_artifact_id=doc_artifact.id
        ).first()
        assert av.value_text == 'Yes'
        assert av.value_number is None
        assert av.value_boolean is None

    def test_other_text_stored_as_value_text(self, db, team, template):
        a = TemplateArtifact(
            template_id=template.id, type=ArtifactType.other,
            name='Notes', value_type=ArtifactValueType.text, display_order=1,
        )
        db.session.add(a)
        db.session.commit()

        repo = _make_repo(db, 'R2', 'https://g/b', team, template,
                          artifact_values={a.id: 'Some notes'})
        av = RepositoryArtifactValue.query.filter_by(
            repository_id=repo.id, template_artifact_id=a.id
        ).first()
        assert av.value_text == 'Some notes'

    def test_other_number_stored_as_value_number(self, db, team, template):
        a = TemplateArtifact(
            template_id=template.id, type=ArtifactType.other,
            name='Score', value_type=ArtifactValueType.number, display_order=1,
        )
        db.session.add(a)
        db.session.commit()

        repo = _make_repo(db, 'R3', 'https://g/c', team, template,
                          artifact_values={a.id: '42.5'})
        av = RepositoryArtifactValue.query.filter_by(
            repository_id=repo.id, template_artifact_id=a.id
        ).first()
        assert float(av.value_number) == pytest.approx(42.5)

    def test_other_boolean_stored_as_value_boolean(self, db, team, template):
        a = TemplateArtifact(
            template_id=template.id, type=ArtifactType.other,
            name='Flag', value_type=ArtifactValueType.boolean, display_order=1,
        )
        db.session.add(a)
        db.session.commit()

        repo = _make_repo(db, 'R4', 'https://g/d', team, template,
                          artifact_values={a.id: 'true'})
        av = RepositoryArtifactValue.query.filter_by(
            repository_id=repo.id, template_artifact_id=a.id
        ).first()
        assert av.value_boolean is True

    def test_other_boolean_na_stored_as_none(self, db, team, template):
        a = TemplateArtifact(
            template_id=template.id, type=ArtifactType.other,
            name='Flag2', value_type=ArtifactValueType.boolean, display_order=1,
        )
        db.session.add(a)
        db.session.commit()

        repo = _make_repo(db, 'R5', 'https://g/e', team, template,
                          artifact_values={a.id: ''})
        av = RepositoryArtifactValue.query.filter_by(
            repository_id=repo.id, template_artifact_id=a.id
        ).first()
        assert av.value_boolean is None


# ---------------------------------------------------------------------------
# TC-007-013: Required artifact validation on edit
# ---------------------------------------------------------------------------

class TestRequiredArtifactOnEdit:

    def test_clearing_required_artifact_raises(self, db, team, template, required_text_artifact):
        repo = repository_service.create_repository(
            name='X', url='https://github.com/org/x', team_id=team.id, template_id=template.id,
            artifact_values={required_text_artifact.id: 'Alice'},
        )
        with pytest.raises(RepositoryServiceError, match='required'):
            repository_service.update_repository(
                repo_id=repo.id,
                name='X', url='https://github.com/org/x',
                team_id=team.id,
                artifact_values={required_text_artifact.id: ''},
                expected_version=repo.version,
            )


# ---------------------------------------------------------------------------
# TC-007-015 & 007-016: Archive / Reactivate
# ---------------------------------------------------------------------------

class TestArchiveReactivate:

    def test_archive(self, db, team, template):
        repo = _make_repo(db, 'Archive Me', 'https://github.com/org/arch', team, template)
        archived = repository_service.archive_repository(repo.id)
        assert archived.is_archived is True
        assert archived.is_active is False

    def test_reactivate(self, db, team, template):
        repo = _make_repo(db, 'Reactivate Me', 'https://github.com/org/react', team, template)
        repository_service.archive_repository(repo.id)
        restored = repository_service.reactivate_repository(repo.id)
        assert restored.is_archived is False
        assert restored.is_active is True

    def test_archive_already_archived_raises(self, db, team, template):
        repo = _make_repo(db, 'Double Archive', 'https://github.com/org/da', team, template)
        repository_service.archive_repository(repo.id)
        with pytest.raises(RepositoryServiceError, match='already archived'):
            repository_service.archive_repository(repo.id)

    def test_reactivate_active_raises(self, db, team, template):
        repo = _make_repo(db, 'Not Archived', 'https://github.com/org/na', team, template)
        with pytest.raises(RepositoryServiceError, match='not archived'):
            repository_service.reactivate_repository(repo.id)

    def test_archive_nonexistent_raises(self, db):
        with pytest.raises(RepositoryServiceError, match='not found'):
            repository_service.archive_repository(99999)


# ---------------------------------------------------------------------------
# TC-007-017: Optimistic locking
# ---------------------------------------------------------------------------

class TestOptimisticLocking:

    def test_stale_version_rejected(self, db, team, template):
        repo = _make_repo(db, 'Lock Repo', 'https://github.com/org/lock', team, template)
        with pytest.raises(RepositoryServiceError, match='modified by another'):
            repository_service.update_repository(
                repo_id=repo.id,
                name='Lock Repo',
                url='https://github.com/org/lock',
                team_id=team.id,
                expected_version=repo.version + 999,
            )


# ---------------------------------------------------------------------------
# TC-007-018 & 007-019: List with archive filter
# ---------------------------------------------------------------------------

class TestGetRepositories:

    def test_excludes_archived_by_default(self, db, team, template):
        active = _make_repo(db, 'Active', 'https://github.com/org/act', team, template)
        archived = _make_repo(db, 'Archived', 'https://github.com/org/arc', team, template)
        repository_service.archive_repository(archived.id)

        result = repository_service.get_repositories(include_archived=False)
        names = [r.name for r in result]
        assert 'Active' in names
        assert 'Archived' not in names

    def test_includes_archived_when_requested(self, db, team, template):
        active = _make_repo(db, 'Active2', 'https://github.com/org/act2', team, template)
        archived = _make_repo(db, 'Archived2', 'https://github.com/org/arc2', team, template)
        repository_service.archive_repository(archived.id)

        result = repository_service.get_repositories(include_archived=True)
        names = [r.name for r in result]
        assert 'Active2' in names
        assert 'Archived2' in names
