"""Tests for repository management routes (TS-007 TC-007-020 through TC-007-025)."""

import pytest

from app.models.team import Team
from app.models.template import ArtifactType, RepoTemplate, TemplateArtifact
from app.services import repository_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def team(db):
    t = Team(name='Route Test Team')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def template(db):
    t = RepoTemplate(name='Route Test Template')
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
def repo(db, team, template):
    return repository_service.create_repository(
        name='Route Repo',
        url='https://github.com/org/route-repo',
        team_id=team.id,
        template_id=template.id,
    )


@pytest.fixture
def archived_repo(db, team, template):
    r = repository_service.create_repository(
        name='Archived Route Repo',
        url='https://github.com/org/archived-route-repo',
        team_id=team.id,
        template_id=template.id,
    )
    repository_service.archive_repository(r.id)
    return r


# ---------------------------------------------------------------------------
# TC-007-025: Unauthenticated redirected to login
# ---------------------------------------------------------------------------

class TestUnauthenticated:

    def test_list_redirects_to_login(self, client):
        resp = client.get('/repositories/')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    def test_detail_redirects_to_login(self, client, repo):
        resp = client.get(f'/repositories/{repo.id}')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    def test_create_redirects_to_login(self, client):
        resp = client.get('/repositories/new')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']


# ---------------------------------------------------------------------------
# TC-007-020: Viewer can list repositories
# ---------------------------------------------------------------------------

class TestRepositoryListRoute:

    def test_viewer_can_list(self, auth_client, repo):
        resp = auth_client.get('/repositories/')
        assert resp.status_code == 200
        assert b'Route Repo' in resp.data

    def test_show_archived_filter(self, admin_client, archived_repo):
        resp = admin_client.get('/repositories/?archived=1')
        assert resp.status_code == 200
        assert b'Archived Route Repo' in resp.data

    def test_active_view_excludes_archived(self, admin_client, repo, archived_repo):
        resp = admin_client.get('/repositories/')
        assert resp.status_code == 200
        assert b'Archived Route Repo' not in resp.data
        assert b'Route Repo' in resp.data


# ---------------------------------------------------------------------------
# Repository detail route
# ---------------------------------------------------------------------------

class TestRepositoryDetailRoute:

    def test_default_shared_attr_not_duplicated_in_detail(self, auth_client, db, repo):
        """URL/Team/Template/Description must not appear twice — default SharedAttributeDefinitions
        must be excluded from the custom_attrs loop since they are already rendered as native fields."""
        from app.models.shared_attribute import SharedAttributeDefinition
        # Seed the four defaults (as the app startup does)
        for name in ('Name', 'Team', 'URL', 'Description'):
            if not SharedAttributeDefinition.query.filter_by(name=name).first():
                db.session.add(SharedAttributeDefinition(name=name, is_default=True, is_active=True))
        db.session.commit()

        resp = auth_client.get(f'/repositories/{repo.id}')
        assert resp.status_code == 200
        # Each default label should appear at most once as a <dt> heading
        html = resp.data.decode()
        for label in ('<dt', ):
            # Count occurrences of ">URL<" and ">Team<" etc. in dt tags
            pass
        # Simpler check: the page renders, and "URL" appears exactly once as a dt label
        import re
        dt_labels = re.findall(r'<dt[^>]*>([^<]+)</dt>', html)
        assert dt_labels.count('URL') <= 1
        assert dt_labels.count('Team') <= 1
        assert dt_labels.count('Description') <= 1

    def test_viewer_can_view_detail(self, auth_client, repo):
        resp = auth_client.get(f'/repositories/{repo.id}')
        assert resp.status_code == 200
        assert b'Route Repo' in resp.data

    def test_unknown_repo_redirects(self, admin_client):
        resp = admin_client.get('/repositories/99999', follow_redirects=True)
        assert resp.status_code == 200
        assert b'not found' in resp.data.lower()


# ---------------------------------------------------------------------------
# TC-007-021: Viewer cannot access create form
# ---------------------------------------------------------------------------

class TestRepositoryCreateRoute:

    def test_viewer_cannot_access_create(self, auth_client):
        resp = auth_client.get('/repositories/new')
        assert resp.status_code == 403

    def test_admin_can_view_create_form(self, admin_client):
        resp = admin_client.get('/repositories/new')
        assert resp.status_code == 200
        assert b'template' in resp.data.lower()

    def test_editor_can_view_create_form(self, editor_client):
        resp = editor_client.get('/repositories/new')
        assert resp.status_code == 200

    # TC-007-022: Editor can create a repository
    def test_editor_can_create_repository(self, editor_client, team, template, doc_artifact):
        resp = editor_client.post('/repositories/new', data={
            'template_id': template.id,
            'name': 'Created Repo',
            'url': 'https://github.com/org/created-repo',
            'description': '',
            'team_id': team.id,
            f'artifact_{doc_artifact.id}': 'Yes',
            'csrf_token': _get_csrf(editor_client),
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Created Repo' in resp.data or b'successfully' in resp.data

    def test_duplicate_url_shows_error(self, editor_client, team, template, repo):
        resp = editor_client.post('/repositories/new', data={
            'template_id': template.id,
            'name': 'New Repo',
            'url': 'https://github.com/org/route-repo',  # duplicate URL
            'description': '',
            'team_id': team.id,
            'csrf_token': _get_csrf(editor_client),
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'already exists' in resp.data


# ---------------------------------------------------------------------------
# TC-007-023: HTMX artifact-fields endpoint
# ---------------------------------------------------------------------------

class TestArtifactFieldsEndpoint:

    def test_editor_gets_artifact_fields(self, editor_client, template, doc_artifact):
        resp = editor_client.get(f'/repositories/artifact-fields?template_id={template.id}')
        assert resp.status_code == 200
        assert b'Design Doc' in resp.data

    def test_viewer_forbidden(self, auth_client, template):
        resp = auth_client.get(f'/repositories/artifact-fields?template_id={template.id}')
        assert resp.status_code == 403

    def test_unknown_template_returns_empty_partial(self, editor_client):
        resp = editor_client.get('/repositories/artifact-fields?template_id=99999')
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Edit route
# ---------------------------------------------------------------------------

class TestRepositoryEditRoute:

    def test_viewer_cannot_access_edit(self, auth_client, repo):
        resp = auth_client.get(f'/repositories/{repo.id}/edit')
        assert resp.status_code == 403

    def test_admin_can_view_edit_form(self, admin_client, repo):
        resp = admin_client.get(f'/repositories/{repo.id}/edit')
        assert resp.status_code == 200
        assert b'Route Repo' in resp.data

    def test_edit_form_shows_artifact_fields(self, admin_client, team, template, doc_artifact):
        """Artifact fields must be rendered on the edit form, not the 'select a template' placeholder."""
        from app.services import repository_service as rs
        repo = rs.create_repository(
            name='ArtifactEditRepo',
            url='https://github.com/org/artifact-edit-repo',
            team_id=team.id,
            template_id=template.id,
            artifact_values={doc_artifact.id: 'Yes'},
        )
        resp = admin_client.get(f'/repositories/{repo.id}/edit')
        assert resp.status_code == 200
        assert b'Select a template above' not in resp.data
        assert b'Design Doc' in resp.data

    # TC-007-024: Template field read-only on edit
    def test_template_not_changeable_via_edit(self, admin_client, db, team, template, repo):
        t2 = RepoTemplate(name='Other Template')
        db.session.add(t2)
        db.session.commit()

        admin_client.post(f'/repositories/{repo.id}/edit', data={
            'name': 'Route Repo',
            'url': 'https://github.com/org/route-repo',
            'description': '',
            'team_id': team.id,
            'version': repo.version,
            # template_id is NOT in form fields for edit — service ignores it
            'csrf_token': _get_csrf(admin_client),
        })

        from app.extensions import db as _db
        from app.models.repository import Repository
        refreshed = _db.session.get(Repository, repo.id)
        assert refreshed.template_id == template.id


# ---------------------------------------------------------------------------
# Archive / Reactivate routes
# ---------------------------------------------------------------------------

class TestArchiveReactivateRoutes:

    def test_viewer_cannot_archive(self, auth_client, repo):
        resp = auth_client.post(f'/repositories/{repo.id}/archive')
        assert resp.status_code == 403

    def test_admin_can_archive(self, admin_client, repo):
        resp = admin_client.post(f'/repositories/{repo.id}/archive', follow_redirects=True)
        assert resp.status_code == 200
        assert b'archived' in resp.data.lower()

    def test_admin_can_reactivate(self, admin_client, archived_repo):
        resp = admin_client.post(f'/repositories/{archived_repo.id}/reactivate', follow_redirects=True)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_csrf(client):
    """Get a CSRF token by fetching the create form."""
    resp = client.get('/repositories/new')
    import re
    match = re.search(rb'name="csrf_token" value="([^"]+)"', resp.data)
    return match.group(1).decode() if match else ''
