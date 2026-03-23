"""Tests for product routes (TS-009 RBAC and HTTP behaviour)."""

import pytest

from app.models.team import Team
from app.models.template import RepoTemplate
from app.services import product_service, repository_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def team(db):
    t = Team(name='Route Prod Team')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def template(db):
    t = RepoTemplate(name='Route Prod Template')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def product(db):
    return product_service.create_product('Route Test Product', 'A test product')


@pytest.fixture
def archived_product(db):
    p = product_service.create_product('Archived Route Product')
    product_service.archive_product(p.id)
    return p


@pytest.fixture
def repo(db, team, template):
    return repository_service.create_repository(
        name='Route Product Repo',
        url='https://github.com/org/route-product-repo',
        team_id=team.id,
        template_id=template.id,
    )


# ---------------------------------------------------------------------------
# Unauthenticated access
# ---------------------------------------------------------------------------

class TestUnauthenticated:

    def test_list_redirects_to_login(self, client):
        resp = client.get('/products/')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    def test_detail_redirects_to_login(self, client, product):
        resp = client.get(f'/products/{product.id}')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    def test_create_redirects_to_login(self, client):
        resp = client.get('/products/new')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']


# ---------------------------------------------------------------------------
# TC-009-006: Viewer access (read-only)
# ---------------------------------------------------------------------------

class TestViewerAccess:

    def test_viewer_can_see_list(self, auth_client, product):
        resp = auth_client.get('/products/')
        assert resp.status_code == 200
        assert b'Route Test Product' in resp.data

    def test_viewer_can_see_detail(self, auth_client, product):
        resp = auth_client.get(f'/products/{product.id}')
        assert resp.status_code == 200

    def test_viewer_cannot_access_create(self, auth_client):
        resp = auth_client.get('/products/new')
        assert resp.status_code == 403

    def test_viewer_cannot_access_edit(self, auth_client, product):
        resp = auth_client.get(f'/products/{product.id}/edit')
        assert resp.status_code == 403

    def test_viewer_cannot_archive(self, auth_client, product):
        resp = auth_client.post(f'/products/{product.id}/archive')
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# TC-009-001: Admin can create product
# ---------------------------------------------------------------------------

class TestAdminCreateProduct:

    def test_get_create_form(self, admin_client):
        resp = admin_client.get('/products/new')
        assert resp.status_code == 200
        assert b'New Product' in resp.data

    def test_post_create_valid(self, admin_client, db):
        resp = admin_client.post(
            '/products/new',
            data={'name': 'Admin Created Product', 'description': 'Test', 'submit': '1'},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        p = product_service.get_products()[0]
        assert p.name == 'Admin Created Product'

    def test_post_create_missing_name(self, admin_client, db):
        resp = admin_client.post(
            '/products/new',
            data={'name': '', 'description': '', 'submit': '1'},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'This field is required' in resp.data

    def test_post_create_duplicate_name(self, admin_client, product, db):
        resp = admin_client.post(
            '/products/new',
            data={'name': product.name, 'description': '', 'submit': '1'},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'already exists' in resp.data


# ---------------------------------------------------------------------------
# TC-009-005: Admin can edit product
# ---------------------------------------------------------------------------

class TestAdminEditProduct:

    def test_get_edit_form(self, admin_client, product):
        resp = admin_client.get(f'/products/{product.id}/edit')
        assert resp.status_code == 200
        assert b'Edit Product' in resp.data

    def test_post_edit_valid(self, admin_client, product, db):
        resp = admin_client.post(
            f'/products/{product.id}/edit',
            data={
                'name': 'Updated Name',
                'description': 'Updated desc',
                'version': str(product.version),
                'submit': '1',
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302
        db.session.refresh(product)
        assert product.name == 'Updated Name'


# ---------------------------------------------------------------------------
# TC-009-007: Admin can archive and reactivate product
# ---------------------------------------------------------------------------

class TestAdminArchiveProduct:

    def test_archive_product(self, admin_client, product, db):
        resp = admin_client.post(f'/products/{product.id}/archive', follow_redirects=False)
        assert resp.status_code == 302
        db.session.refresh(product)
        assert product.is_archived is True

    def test_reactivate_product(self, admin_client, archived_product, db):
        resp = admin_client.post(f'/products/{archived_product.id}/reactivate', follow_redirects=False)
        assert resp.status_code == 302
        db.session.refresh(archived_product)
        assert archived_product.is_archived is False


# ---------------------------------------------------------------------------
# TC-009-012 / TC-009-013: Linking and unlinking from product edit page
# ---------------------------------------------------------------------------

class TestProductLinking:

    def test_link_repo_from_product(self, admin_client, product, repo, db):
        resp = admin_client.post(
            f'/products/{product.id}/link-repo',
            data={'repo_id': str(repo.id)},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        db.session.refresh(product)
        assert repo in product.repositories

    def test_unlink_repo_from_product(self, admin_client, product, repo, db):
        product_service.link_repository(product.id, repo.id)
        resp = admin_client.post(
            f'/products/{product.id}/unlink-repo',
            data={'repo_id': str(repo.id)},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        db.session.refresh(product)
        assert repo not in product.repositories

    def test_link_without_repo_id_flashes_error(self, admin_client, product, db):
        resp = admin_client.post(
            f'/products/{product.id}/link-repo',
            data={},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'select a repository' in resp.data


# ---------------------------------------------------------------------------
# TC-009-017: List active/archived toggle
# ---------------------------------------------------------------------------

class TestProductListFilter:

    def test_default_shows_active_only(self, auth_client, product, archived_product):
        resp = auth_client.get('/products/')
        assert resp.status_code == 200
        assert b'Route Test Product' in resp.data
        assert b'Archived Route Product' not in resp.data

    def test_archived_toggle_shows_archived(self, auth_client, product, archived_product):
        # ?archived=1 shows all products (active + archived), like the repository list pattern
        resp = auth_client.get('/products/?archived=1')
        assert resp.status_code == 200
        assert b'Archived Route Product' in resp.data


# ---------------------------------------------------------------------------
# TC-009-018: Detail page shows linked repos
# ---------------------------------------------------------------------------

class TestProductDetail:

    def test_detail_shows_linked_repos(self, auth_client, product, repo, db):
        product_service.link_repository(product.id, repo.id)
        resp = auth_client.get(f'/products/{product.id}')
        assert resp.status_code == 200
        assert b'Route Product Repo' in resp.data

    def test_detail_has_no_link_unlink_controls(self, admin_client, product, repo, db):
        """Detail page must be read-only — no link/unlink forms."""
        product_service.link_repository(product.id, repo.id)
        resp = admin_client.get(f'/products/{product.id}')
        assert resp.status_code == 200
        assert b'unlink-repo' not in resp.data
        assert b'link-repo' not in resp.data

    def test_edit_page_shows_link_management(self, admin_client, product, repo, db):
        """Edit page must show the repo link management section."""
        resp = admin_client.get(f'/products/{product.id}/edit')
        assert resp.status_code == 200
        assert b'Linked Repositories' in resp.data
        assert b'Link a repository' in resp.data

    def test_edit_page_link_footer_visible_after_all_repos_linked(self, admin_client, product, repo, db):
        """Footer must stay visible even when all repos are already linked (no dropdown but info message)."""
        product_service.link_repository(product.id, repo.id)
        resp = admin_client.get(f'/products/{product.id}/edit')
        assert resp.status_code == 200
        # Footer is always rendered — shows info message instead of form
        assert b'already linked' in resp.data
        # The link form's submit button must NOT be shown (no repos left to pick)
        assert b'Link a repository' not in resp.data

    def test_detail_not_found_redirects(self, auth_client):
        resp = auth_client.get('/products/9999', follow_redirects=True)
        assert resp.status_code == 200
        assert b'not found' in resp.data


# ---------------------------------------------------------------------------
# TC-009-014: Managing links from repository edit page
# ---------------------------------------------------------------------------

class TestRepoSideLinking:

    def test_link_product_to_repo(self, admin_client, product, repo, db):
        resp = admin_client.post(
            '/products/link-to-repo',
            data={'product_id': str(product.id), 'repo_id': str(repo.id)},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        db.session.refresh(product)
        assert repo in product.repositories

    def test_unlink_product_from_repo(self, admin_client, product, repo, db):
        product_service.link_repository(product.id, repo.id)
        resp = admin_client.post(
            '/products/unlink-from-repo',
            data={'product_id': str(product.id), 'repo_id': str(repo.id)},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        db.session.refresh(product)
        assert repo not in product.repositories
