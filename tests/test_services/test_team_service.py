"""Tests for team service business logic (TC-005-009 through TC-005-017)."""

import pytest

from app.services import team_service
from app.services.team_service import TeamServiceError


class TestGetTeams:
    """Team listing tests."""

    # TC-005-001
    def test_get_teams_excludes_archived(self, db):
        team_service.create_team(name='Active Team')
        active = team_service.get_teams(include_archived=False)
        # Create and then archive a second team
        t2 = team_service.create_team(name='Archived Team')
        t2.is_archived = True
        db.session.commit()

        result = team_service.get_teams(include_archived=False)
        names = [t.name for t in result]
        assert 'Active Team' in names
        assert 'Archived Team' not in names

    # TC-005-002
    def test_get_teams_includes_archived(self, db):
        team_service.create_team(name='Active Team')
        t2 = team_service.create_team(name='Archived Team')
        t2.is_archived = True
        db.session.commit()

        result = team_service.get_teams(include_archived=True)
        names = [t.name for t in result]
        assert 'Active Team' in names
        assert 'Archived Team' in names


class TestCreateTeam:
    """Team creation tests."""

    # TC-005-003 / TC-005-004
    def test_create_team_success(self, db):
        team = team_service.create_team(name='Engineering', description='Core eng team')
        assert team.id is not None
        assert team.name == 'Engineering'
        assert team.description == 'Core eng team'
        assert team.is_active is True
        assert team.is_archived is False

    def test_create_team_without_description(self, db):
        team = team_service.create_team(name='Platform')
        assert team.name == 'Platform'
        assert team.description is None

    # TC-005-009
    def test_duplicate_name_rejected(self, db):
        team_service.create_team(name='Alpha')
        with pytest.raises(TeamServiceError, match='already exists'):
            team_service.create_team(name='Alpha')

    # TC-005-009 (case-insensitive)
    def test_duplicate_name_case_insensitive(self, db):
        team_service.create_team(name='Alpha')
        with pytest.raises(TeamServiceError, match='already exists'):
            team_service.create_team(name='ALPHA')

    def test_empty_name_rejected(self, db):
        with pytest.raises(TeamServiceError, match='required'):
            team_service.create_team(name='')

    def test_whitespace_only_name_rejected(self, db):
        with pytest.raises(TeamServiceError, match='required'):
            team_service.create_team(name='   ')


class TestUpdateTeam:
    """Team update tests."""

    # TC-005-006 / TC-005-007
    def test_update_team_success(self, db):
        team = team_service.create_team(name='Old Name', description='Old desc')
        updated = team_service.update_team(
            team_id=team.id,
            name='New Name',
            description='New desc',
            expected_version=team.version,
        )
        assert updated.name == 'New Name'
        assert updated.description == 'New desc'
        assert updated.version == team.version  # version was incremented in place

    # TC-005-010
    def test_rename_to_existing_name_rejected(self, db):
        team_service.create_team(name='Alpha')
        beta = team_service.create_team(name='Beta')
        with pytest.raises(TeamServiceError, match='already exists'):
            team_service.update_team(
                team_id=beta.id,
                name='Alpha',
                description=None,
                expected_version=beta.version,
            )

    def test_rename_to_same_name_allowed(self, db):
        team = team_service.create_team(name='MyTeam')
        updated = team_service.update_team(
            team_id=team.id,
            name='MyTeam',
            description='Updated desc',
            expected_version=team.version,
        )
        assert updated.name == 'MyTeam'

    # TC-005-017
    def test_optimistic_locking_conflict(self, db):
        team = team_service.create_team(name='ConflictTeam')
        with pytest.raises(TeamServiceError, match='modified by another'):
            team_service.update_team(
                team_id=team.id,
                name='ConflictTeam',
                description=None,
                expected_version=team.version + 999,
            )

    def test_update_nonexistent_team(self, db):
        with pytest.raises(TeamServiceError, match='not found'):
            team_service.update_team(
                team_id=99999,
                name='Ghost',
                description=None,
                expected_version=1,
            )


class TestArchiveReactivate:
    """Archive and reactivate tests."""

    # TC-005-012
    def test_archive_team_no_blocking_repos(self, db):
        team = team_service.create_team(name='ArchiveMe')
        archived = team_service.archive_team(team.id)
        assert archived.is_archived is True
        assert archived.is_active is False

    # TC-005-014
    def test_reactivate_team(self, db):
        team = team_service.create_team(name='Reactivate Me')
        team_service.archive_team(team.id)
        restored = team_service.reactivate_team(team.id)
        assert restored.is_archived is False
        assert restored.is_active is True

    def test_archive_already_archived_raises(self, db):
        team = team_service.create_team(name='AlreadyGone')
        team_service.archive_team(team.id)
        with pytest.raises(TeamServiceError, match='already archived'):
            team_service.archive_team(team.id)

    def test_reactivate_active_team_raises(self, db):
        team = team_service.create_team(name='StillActive')
        with pytest.raises(TeamServiceError, match='not archived'):
            team_service.reactivate_team(team.id)

    def test_archive_nonexistent_team(self, db):
        with pytest.raises(TeamServiceError, match='not found'):
            team_service.archive_team(99999)

    def test_reactivate_nonexistent_team(self, db):
        with pytest.raises(TeamServiceError, match='not found'):
            team_service.reactivate_team(99999)
