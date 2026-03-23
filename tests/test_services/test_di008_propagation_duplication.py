"""Tests for DI-008: Template Change Propagation & Repository Duplication (TS-008)."""

import pytest

from app.models.repository import Repository, RepositoryArtifactValue
from app.models.shared_attribute import RepositorySharedAttributeValue, SharedAttributeDefinition
from app.models.team import Team
from app.models.template import ArtifactType, ArtifactValueType, RepoTemplate, TemplateArtifact
from app.services import repository_service, template_service
from app.services.repository_service import RepositoryServiceError
from app.services.template_service import TemplateServiceError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def team(db):
    t = Team(name='DI-008 Team')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def template(db):
    t = RepoTemplate(name='DI-008 Template')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def repo(db, team, template):
    return repository_service.create_repository(
        name='DI-008 Repo',
        url='https://github.com/org/di008-repo',
        team_id=team.id,
        template_id=template.id,
    )


# ---------------------------------------------------------------------------
# TC-008-001 to TC-008-003: Artifact addition propagation (REQ-042)
# ---------------------------------------------------------------------------

class TestArtifactAdditionPropagation:

    def test_propagates_to_active_repos(self, db, team, template):
        """TC-008-001: Adding artifact creates empty value rows for active repos."""
        r1 = repository_service.create_repository(
            name='R1', url='https://g.com/r1', team_id=team.id, template_id=template.id
        )
        r2 = repository_service.create_repository(
            name='R2', url='https://g.com/r2', team_id=team.id, template_id=template.id
        )
        r3 = repository_service.create_repository(
            name='R3', url='https://g.com/r3', team_id=team.id, template_id=template.id
        )
        repository_service.archive_repository(r3.id)

        artifact = template_service.add_artifact(
            template_id=template.id,
            artifact_type=ArtifactType.document,
            name='New Doc',
        )

        av1 = RepositoryArtifactValue.query.filter_by(
            repository_id=r1.id, template_artifact_id=artifact.id
        ).first()
        av2 = RepositoryArtifactValue.query.filter_by(
            repository_id=r2.id, template_artifact_id=artifact.id
        ).first()
        av3 = RepositoryArtifactValue.query.filter_by(
            repository_id=r3.id, template_artifact_id=artifact.id
        ).first()

        assert av1 is not None
        assert av2 is not None
        assert av3 is None  # TC-008-001: archived repos not propagated

    def test_propagated_values_are_null(self, db, team, template):
        """TC-008-002: Propagated rows have all null typed columns."""
        r = repository_service.create_repository(
            name='NullRepo', url='https://g.com/null', team_id=team.id, template_id=template.id
        )
        artifact = template_service.add_artifact(
            template_id=template.id,
            artifact_type=ArtifactType.document,
            name='Null Doc',
        )
        av = RepositoryArtifactValue.query.filter_by(
            repository_id=r.id, template_artifact_id=artifact.id
        ).first()
        assert av is not None
        assert av.value_text is None
        assert av.value_number is None
        assert av.value_boolean is None
        assert av.value_list_option_id is None

    def test_propagation_does_not_affect_other_templates(self, db, team):
        """TC-008-003: Propagation is scoped to the artifact's template only."""
        t1 = RepoTemplate(name='T1-008')
        t2 = RepoTemplate(name='T2-008')
        db.session.add_all([t1, t2])
        db.session.commit()

        r1 = repository_service.create_repository(
            name='T1Repo', url='https://g.com/t1r', team_id=team.id, template_id=t1.id
        )
        r2 = repository_service.create_repository(
            name='T2Repo', url='https://g.com/t2r', team_id=team.id, template_id=t2.id
        )

        artifact = template_service.add_artifact(
            template_id=t1.id,
            artifact_type=ArtifactType.skill,
            name='T1 Only Skill',
        )

        av_r1 = RepositoryArtifactValue.query.filter_by(
            repository_id=r1.id, template_artifact_id=artifact.id
        ).first()
        av_r2 = RepositoryArtifactValue.query.filter_by(
            repository_id=r2.id, template_artifact_id=artifact.id
        ).first()

        assert av_r1 is not None
        assert av_r2 is None


# ---------------------------------------------------------------------------
# TC-008-004 to TC-008-006: Artifact removal soft-delete (REQ-044)
# ---------------------------------------------------------------------------

class TestArtifactRemovalSoftDelete:

    def test_remove_artifact_soft_deletes(self, db, team, template):
        """TC-008-004: Removal sets is_active=False, row + RepositoryArtifactValue preserved."""
        artifact = template_service.add_artifact(
            template_id=template.id,
            artifact_type=ArtifactType.document,
            name='To Remove',
        )
        r = repository_service.create_repository(
            name='SoftDelRepo', url='https://g.com/soft', team_id=team.id, template_id=template.id
        )
        # Ensure an artifact value exists for the repo
        av = RepositoryArtifactValue.query.filter_by(
            repository_id=r.id, template_artifact_id=artifact.id
        ).first()
        assert av is not None

        template_service.remove_artifact(artifact.id)

        # Artifact row still exists with is_active=False
        fetched = db.session.get(TemplateArtifact, artifact.id)
        assert fetched is not None
        assert fetched.is_active is False

        # RepositoryArtifactValue row still exists
        av_after = RepositoryArtifactValue.query.filter_by(
            repository_id=r.id, template_artifact_id=artifact.id
        ).first()
        assert av_after is not None

    def test_removed_artifact_not_in_active_list(self, db, team, template):
        """TC-008-005: Soft-deleted artifact excluded from active artifacts on template."""
        a1 = template_service.add_artifact(
            template_id=template.id, artifact_type=ArtifactType.document, name='Keep Me'
        )
        a2 = template_service.add_artifact(
            template_id=template.id, artifact_type=ArtifactType.skill, name='Remove Me'
        )
        template_service.remove_artifact(a2.id)

        db.session.expire_all()
        tmpl = db.session.get(RepoTemplate, template.id)
        active = [a for a in tmpl.artifacts if a.is_active]
        names = [a.name for a in active]
        assert 'Keep Me' in names
        assert 'Remove Me' not in names


# ---------------------------------------------------------------------------
# TC-008-009 to TC-008-013: Repository duplication (REQ-052)
# ---------------------------------------------------------------------------

class TestRepositoryDuplication:

    def test_duplicate_copies_artifact_values(self, db, team, template):
        """TC-008-009: Duplicate copies all artifact values."""
        artifact = template_service.add_artifact(
            template_id=template.id, artifact_type=ArtifactType.document, name='Design Doc'
        )
        source = repository_service.create_repository(
            name='Source', url='https://g.com/source',
            team_id=team.id, template_id=template.id,
            artifact_values={artifact.id: 'Yes'},
        )

        dup = repository_service.duplicate_repository(
            source_repo_id=source.id,
            name='Dup Repo',
            url='https://g.com/dup',
        )

        dup_av = RepositoryArtifactValue.query.filter_by(
            repository_id=dup.id, template_artifact_id=artifact.id
        ).first()
        assert dup_av is not None
        assert dup_av.value_text == 'Yes'

    def test_duplicate_copies_shared_attr_values(self, db, team, template):
        """TC-008-010: Duplicate copies all shared attribute values."""
        attr = SharedAttributeDefinition(name='Tech Stack 008', is_default=False, is_active=True)
        db.session.add(attr)
        db.session.commit()

        source = repository_service.create_repository(
            name='SharedSrc', url='https://g.com/shared-src',
            team_id=team.id, template_id=template.id,
            shared_attr_values={attr.id: 'Python'},
        )

        dup = repository_service.duplicate_repository(
            source_repo_id=source.id,
            name='SharedDup',
            url='https://g.com/shared-dup',
        )

        dup_sav = RepositorySharedAttributeValue.query.filter_by(
            repository_id=dup.id, attribute_id=attr.id
        ).first()
        assert dup_sav is not None
        assert dup_sav.value == 'Python'

    def test_duplicate_requires_unique_url(self, db, team, template):
        """TC-008-011: Duplicate fails if the URL already exists."""
        source = repository_service.create_repository(
            name='UniqueSource', url='https://g.com/unique-src',
            team_id=team.id, template_id=template.id,
        )
        with pytest.raises(RepositoryServiceError, match='already exists'):
            repository_service.duplicate_repository(
                source_repo_id=source.id,
                name='Dup',
                url='https://g.com/unique-src',  # same URL
            )

    def test_duplicate_uses_same_template(self, db, team, template):
        """TC-008-013: Duplicate inherits source template_id."""
        source = repository_service.create_repository(
            name='TmplSrc', url='https://g.com/tmpl-src',
            team_id=team.id, template_id=template.id,
        )
        dup = repository_service.duplicate_repository(
            source_repo_id=source.id,
            name='TmplDup',
            url='https://g.com/tmpl-dup',
        )
        assert dup.template_id == template.id

    def test_duplicate_source_not_found_raises(self, db):
        """TC-008-018: Source not found raises error."""
        with pytest.raises(RepositoryServiceError, match='not found'):
            repository_service.duplicate_repository(
                source_repo_id=99999,
                name='X',
                url='https://g.com/x',
            )

    def test_duplicate_empty_name_raises(self, db, team, template):
        """Duplicate with empty name raises error."""
        source = repository_service.create_repository(
            name='NameSrc', url='https://g.com/name-src',
            team_id=team.id, template_id=template.id,
        )
        with pytest.raises(RepositoryServiceError, match='required'):
            repository_service.duplicate_repository(
                source_repo_id=source.id,
                name='',
                url='https://g.com/name-dup',
            )

    def test_duplicate_empty_url_raises(self, db, team, template):
        """Duplicate with empty URL raises error."""
        source = repository_service.create_repository(
            name='URLSrc', url='https://g.com/url-src',
            team_id=team.id, template_id=template.id,
        )
        with pytest.raises(RepositoryServiceError, match='required'):
            repository_service.duplicate_repository(
                source_repo_id=source.id,
                name='URLDup',
                url='',
            )


# ---------------------------------------------------------------------------
# TC-008-014 to TC-008-018: Duplicate route tests
# ---------------------------------------------------------------------------

class TestDuplicateRoute:

    @pytest.fixture
    def repo(self, db, team, template):
        return repository_service.create_repository(
            name='Route Dup Source',
            url='https://g.com/route-dup-src',
            team_id=team.id,
            template_id=template.id,
        )

    def test_viewer_forbidden(self, auth_client, repo):
        """TC-008-015: Viewer gets 403."""
        resp = auth_client.get(f'/repositories/{repo.id}/duplicate')
        assert resp.status_code == 403

    def test_admin_can_view_duplicate_form(self, admin_client, repo):
        """TC-008-014: Admin can access duplicate form."""
        resp = admin_client.get(f'/repositories/{repo.id}/duplicate')
        assert resp.status_code == 200
        assert b'Duplicate' in resp.data

    def test_editor_can_view_duplicate_form(self, editor_client, repo):
        """TC-008-014: Editor can access duplicate form."""
        resp = editor_client.get(f'/repositories/{repo.id}/duplicate')
        assert resp.status_code == 200

    def test_form_prefills_name(self, admin_client, repo):
        """TC-008-016: Name pre-filled as 'Copy of <name>'."""
        resp = admin_client.get(f'/repositories/{repo.id}/duplicate')
        assert b'Copy of Route Dup Source' in resp.data

    def test_successful_duplicate_redirects_to_detail(self, editor_client, repo):
        """TC-008-017: Successful duplicate redirects to new repo detail."""
        csrf = _get_csrf(editor_client, repo.id)
        resp = editor_client.post(f'/repositories/{repo.id}/duplicate', data={
            'name': 'Duplicated Repo',
            'url': 'https://g.com/duplicated',
            'csrf_token': csrf,
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Duplicated Repo' in resp.data or b'successfully' in resp.data

    def test_unknown_repo_redirects(self, admin_client):
        """TC-008-018: Unknown source repo redirects with error."""
        resp = admin_client.get('/repositories/99999/duplicate', follow_redirects=True)
        assert resp.status_code == 200
        assert b'not found' in resp.data.lower()

    def test_duplicate_url_shows_error(self, editor_client, repo):
        """TC-008-011 via route: duplicate URL shows error."""
        csrf = _get_csrf(editor_client, repo.id)
        resp = editor_client.post(f'/repositories/{repo.id}/duplicate', data={
            'name': 'Another Repo',
            'url': repo.url,  # same URL as source
            'csrf_token': csrf,
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'already exists' in resp.data


# ---------------------------------------------------------------------------
# TC-008-019 to TC-008-020: List option deactivation (REQ-045)
# ---------------------------------------------------------------------------

class TestListOptionDeactivation:

    def test_deactivated_option_hidden_from_active_list(self, db):
        """TC-008-019: Deactivated option has is_active=False."""
        from app.models.template import ArtifactListOption
        tmpl = template_service.create_template(name='ListOptTmpl')
        artifact = template_service.add_artifact(
            template_id=tmpl.id,
            artifact_type=ArtifactType.other,
            name='Priority',
            value_type=ArtifactValueType.list,
        )
        opt = template_service.add_list_option(artifact_id=artifact.id, value='High')
        template_service.deactivate_list_option(opt.id)

        fetched_opt = db.session.get(ArtifactListOption, opt.id)
        assert fetched_opt.is_active is False

        active_opts = [o for o in artifact.list_options if o.is_active]
        assert opt not in active_opts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_csrf(client, repo_id):
    """Fetch a CSRF token from the duplicate form."""
    resp = client.get(f'/repositories/{repo_id}/duplicate')
    import re
    match = re.search(rb'name="csrf_token" value="([^"]+)"', resp.data)
    return match.group(1).decode() if match else ''
