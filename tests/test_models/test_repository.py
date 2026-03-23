"""Tests for Repository and RepositoryArtifactValue models (TC-007-001, TC-007-002)."""

import pytest

from app.extensions import db as _db
from app.models.repository import Repository, RepositoryArtifactValue
from app.models.team import Team
from app.models.template import ArtifactListOption, ArtifactType, ArtifactValueType, RepoTemplate, TemplateArtifact


@pytest.fixture
def team(db):
    t = Team(name='Alpha Team')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def template(db):
    t = RepoTemplate(name='Standard Template')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def artifact(db, template):
    a = TemplateArtifact(
        template_id=template.id,
        type=ArtifactType.document,
        name='Design Doc',
        display_order=1,
    )
    db.session.add(a)
    db.session.commit()
    return a


class TestRepositoryModel:
    """TC-007-001: Repository model fields present."""

    def test_fields_present(self, db, team, template):
        repo = Repository(
            name='My Repo',
            url='https://github.com/org/my-repo',
            description='A test repo',
            team_id=team.id,
            template_id=template.id,
        )
        db.session.add(repo)
        db.session.commit()

        fetched = _db.session.get(Repository, repo.id)
        assert fetched.name == 'My Repo'
        assert fetched.url == 'https://github.com/org/my-repo'
        assert fetched.description == 'A test repo'
        assert fetched.team_id == team.id
        assert fetched.template_id == template.id
        assert fetched.is_active is True
        assert fetched.is_archived is False
        assert fetched.created_at is not None
        assert fetched.updated_at is not None
        assert fetched.version == 1

    def test_url_unique_constraint(self, db, team, template):
        repo1 = Repository(name='Repo 1', url='https://github.com/org/same', team_id=team.id, template_id=template.id)
        db.session.add(repo1)
        db.session.commit()

        repo2 = Repository(name='Repo 2', url='https://github.com/org/same', team_id=team.id, template_id=template.id)
        db.session.add(repo2)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_relationships_accessible(self, db, team, template):
        repo = Repository(name='Rel Repo', url='https://github.com/org/rel', team_id=team.id, template_id=template.id)
        db.session.add(repo)
        db.session.commit()

        assert repo.team is not None
        assert repo.team.name == 'Alpha Team'
        assert repo.template is not None
        assert repo.template.name == 'Standard Template'


class TestRepositoryArtifactValueModel:
    """TC-007-002: RepositoryArtifactValue model fields present."""

    def test_fields_present(self, db, team, template, artifact):
        repo = Repository(name='AV Repo', url='https://github.com/org/av', team_id=team.id, template_id=template.id)
        db.session.add(repo)
        db.session.commit()

        av = RepositoryArtifactValue(
            repository_id=repo.id,
            template_artifact_id=artifact.id,
            value_text='Yes',
        )
        db.session.add(av)
        db.session.commit()

        fetched = _db.session.get(RepositoryArtifactValue, av.id)
        assert fetched.repository_id == repo.id
        assert fetched.template_artifact_id == artifact.id
        assert fetched.value_text == 'Yes'
        assert fetched.value_number is None
        assert fetched.value_boolean is None
        assert fetched.value_list_option_id is None

    def test_unique_constraint(self, db, team, template, artifact):
        repo = Repository(name='UQ AV Repo', url='https://github.com/org/uqav', team_id=team.id, template_id=template.id)
        db.session.add(repo)
        db.session.commit()

        av1 = RepositoryArtifactValue(repository_id=repo.id, template_artifact_id=artifact.id, value_text='Yes')
        db.session.add(av1)
        db.session.commit()

        av2 = RepositoryArtifactValue(repository_id=repo.id, template_artifact_id=artifact.id, value_text='No')
        db.session.add(av2)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()
