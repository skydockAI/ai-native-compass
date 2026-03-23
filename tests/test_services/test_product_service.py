"""Tests for product service business logic (TS-009)."""

import pytest

from app.models.product import Product
from app.models.team import Team
from app.models.template import RepoTemplate
from app.services import product_service, repository_service
from app.services.product_service import ProductServiceError
from app.services.repository_service import RepositoryServiceError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def team(db):
    t = Team(name='Prod Svc Team')
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def template(db):
    t = RepoTemplate(name='Prod Svc Template')
    db.session.add(t)
    db.session.commit()
    return t


def _make_product(name, description=None):
    return product_service.create_product(name=name, description=description)


def _make_repo(db, name, team, template):
    return repository_service.create_repository(
        name=name,
        url=f'https://github.com/org/{name.lower().replace(" ", "-")}',
        team_id=team.id,
        template_id=template.id,
    )


# ---------------------------------------------------------------------------
# TC-009-001 / TC-009-002: Create product
# ---------------------------------------------------------------------------

class TestCreateProduct:

    def test_create_product_with_description(self, db):
        p = _make_product('Alpha', 'Alpha product')
        assert p.id is not None
        assert p.name == 'Alpha'
        assert p.description == 'Alpha product'
        assert p.is_active is True
        assert p.is_archived is False

    def test_create_product_without_description(self, db):
        p = _make_product('Beta')
        assert p.description is None

    def test_create_product_name_required(self, db):
        with pytest.raises(ProductServiceError, match='required'):
            _make_product('')

    def test_create_product_name_stripped(self, db):
        p = _make_product('  Gamma  ')
        assert p.name == 'Gamma'


# ---------------------------------------------------------------------------
# TC-009-003 / TC-009-004: Name uniqueness
# ---------------------------------------------------------------------------

class TestProductNameUniqueness:

    def test_duplicate_name_raises(self, db):
        _make_product('Unique')
        with pytest.raises(ProductServiceError, match='already exists'):
            _make_product('Unique')

    def test_duplicate_name_case_insensitive(self, db):
        _make_product('MyProduct')
        with pytest.raises(ProductServiceError, match='already exists'):
            _make_product('myproduct')

    def test_rename_to_duplicate_raises(self, db):
        _make_product('Alpha')
        beta = _make_product('Beta')
        with pytest.raises(ProductServiceError, match='already exists'):
            product_service.update_product(beta.id, name='Alpha')


# ---------------------------------------------------------------------------
# TC-009-005: Update product
# ---------------------------------------------------------------------------

class TestUpdateProduct:

    def test_update_name_and_description(self, db):
        p = _make_product('Old Name', 'Old desc')
        updated = product_service.update_product(p.id, name='New Name', description='New desc')
        assert updated.name == 'New Name'
        assert updated.description == 'New desc'
        assert updated.version == 2

    def test_update_with_correct_version(self, db):
        p = _make_product('VersionTest')
        product_service.update_product(p.id, name='VersionTest', expected_version=1)

    def test_update_with_stale_version_raises(self, db):
        p = _make_product('StaleTest')
        with pytest.raises(ProductServiceError, match='modified by another user'):
            product_service.update_product(p.id, name='StaleTest', expected_version=99)

    def test_update_not_found_raises(self, db):
        with pytest.raises(ProductServiceError, match='not found'):
            product_service.update_product(9999, name='X')


# ---------------------------------------------------------------------------
# TC-009-007: Archive product with no active links
# ---------------------------------------------------------------------------

class TestArchiveProduct:

    def test_archive_product_no_links(self, db):
        p = _make_product('Archive Me')
        archived = product_service.archive_product(p.id)
        assert archived.is_archived is True
        assert archived.is_active is False

    def test_reactivate_product(self, db):
        p = _make_product('Reactivate Me')
        product_service.archive_product(p.id)
        reactivated = product_service.reactivate_product(p.id)
        assert reactivated.is_archived is False
        assert reactivated.is_active is True

    def test_archive_already_archived_raises(self, db):
        p = _make_product('Already Archived')
        product_service.archive_product(p.id)
        with pytest.raises(ProductServiceError, match='already archived'):
            product_service.archive_product(p.id)

    def test_reactivate_not_archived_raises(self, db):
        p = _make_product('Not Archived')
        with pytest.raises(ProductServiceError, match='not archived'):
            product_service.reactivate_product(p.id)

    def test_archive_product_not_found_raises(self, db):
        with pytest.raises(ProductServiceError, match='not found'):
            product_service.archive_product(9999)


# ---------------------------------------------------------------------------
# TC-009-008: Archive product blocked by active repo link
# ---------------------------------------------------------------------------

class TestArchiveProductProtection:

    def test_archive_blocked_by_active_repo(self, db, team, template):
        p = _make_product('BlockedProduct')
        repo = _make_repo(db, 'BlockedRepo', team, template)
        product_service.link_repository(p.id, repo.id)
        with pytest.raises(ProductServiceError, match='active'):
            product_service.archive_product(p.id)

    def test_archive_allowed_after_unlinking(self, db, team, template):
        p = _make_product('UnlinkFirst')
        repo = _make_repo(db, 'ToUnlinkRepo', team, template)
        product_service.link_repository(p.id, repo.id)
        product_service.unlink_repository(p.id, repo.id)
        archived = product_service.archive_product(p.id)
        assert archived.is_archived is True

    def test_archive_allowed_when_linked_repo_is_archived(self, db, team, template):
        """Product can be archived if all linked repos are themselves archived."""
        p = _make_product('ArchiveIfRepoArchived')
        repo = _make_repo(db, 'RepoToArchive', team, template)
        product_service.link_repository(p.id, repo.id)
        # Archive the repo first (no active products blocking it once we don't block repo here)
        # Directly archive via model to bypass archive protection
        repo.is_archived = True
        repo.is_active = False
        db.session.commit()
        archived = product_service.archive_product(p.id)
        assert archived.is_archived is True


# ---------------------------------------------------------------------------
# TC-009-010 / TC-009-011: Repository archive protection by product links
# ---------------------------------------------------------------------------

class TestArchiveRepositoryProtection:

    def test_archive_repo_blocked_by_active_product(self, db, team, template):
        p = _make_product('ActiveProduct')
        repo = _make_repo(db, 'ProtectedRepo', team, template)
        product_service.link_repository(p.id, repo.id)
        with pytest.raises(RepositoryServiceError, match='active'):
            repository_service.archive_repository(repo.id)

    def test_archive_repo_allowed_after_unlinking(self, db, team, template):
        p = _make_product('ProductToUnlink')
        repo = _make_repo(db, 'RepoToArchive2', team, template)
        product_service.link_repository(p.id, repo.id)
        product_service.unlink_repository(p.id, repo.id)
        archived = repository_service.archive_repository(repo.id)
        assert archived.is_archived is True

    def test_archive_repo_no_products(self, db, team, template):
        repo = _make_repo(db, 'NoProductRepo', team, template)
        archived = repository_service.archive_repository(repo.id)
        assert archived.is_archived is True


# ---------------------------------------------------------------------------
# TC-009-012 / TC-009-013: Linking and unlinking
# ---------------------------------------------------------------------------

class TestLinking:

    def test_link_repository(self, db, team, template):
        p = _make_product('LinkTest')
        repo = _make_repo(db, 'LinkRepo', team, template)
        product_service.link_repository(p.id, repo.id)
        assert repo in p.repositories

    def test_unlink_repository(self, db, team, template):
        p = _make_product('UnlinkTest')
        repo = _make_repo(db, 'UnlinkRepo', team, template)
        product_service.link_repository(p.id, repo.id)
        product_service.unlink_repository(p.id, repo.id)
        assert repo not in p.repositories

    def test_link_already_linked_raises(self, db, team, template):
        p = _make_product('DupLink')
        repo = _make_repo(db, 'DupLinkRepo', team, template)
        product_service.link_repository(p.id, repo.id)
        with pytest.raises(ProductServiceError, match='already linked'):
            product_service.link_repository(p.id, repo.id)

    def test_unlink_not_linked_raises(self, db, team, template):
        p = _make_product('NoLink')
        repo = _make_repo(db, 'NoLinkRepo', team, template)
        with pytest.raises(ProductServiceError, match='not linked'):
            product_service.unlink_repository(p.id, repo.id)

    def test_link_product_not_found_raises(self, db, team, template):
        repo = _make_repo(db, 'OrphanRepo', team, template)
        with pytest.raises(ProductServiceError, match='not found'):
            product_service.link_repository(9999, repo.id)

    def test_link_repo_not_found_raises(self, db):
        p = _make_product('OrphanProduct')
        with pytest.raises(ProductServiceError, match='not found'):
            product_service.link_repository(p.id, 9999)


# ---------------------------------------------------------------------------
# TC-009-015 / TC-009-016: Independent creation
# ---------------------------------------------------------------------------

class TestIndependentCreation:

    def test_product_created_without_repos(self, db):
        p = _make_product('Standalone')
        assert p.repositories == []

    def test_many_to_many_both_directions(self, db, team, template):
        p1 = _make_product('Prod1')
        p2 = _make_product('Prod2')
        repo = _make_repo(db, 'SharedRepo', team, template)
        product_service.link_repository(p1.id, repo.id)
        product_service.link_repository(p2.id, repo.id)
        assert repo in p1.repositories
        assert repo in p2.repositories
        assert p1 in repo.products
        assert p2 in repo.products


# ---------------------------------------------------------------------------
# TC-009-017: Get products with filter
# ---------------------------------------------------------------------------

class TestGetProducts:

    def test_get_active_only(self, db):
        p1 = _make_product('Active1')
        p2 = _make_product('Active2')
        product_service.archive_product(p1.id)
        active = product_service.get_products(include_archived=False)
        names = [p.name for p in active]
        assert 'Active2' in names
        assert 'Active1' not in names

    def test_get_including_archived(self, db):
        p1 = _make_product('AllActive')
        p2 = _make_product('AllArchived')
        product_service.archive_product(p2.id)
        all_products = product_service.get_products(include_archived=True)
        names = [p.name for p in all_products]
        assert 'AllActive' in names
        assert 'AllArchived' in names
