"""Tests for user service business logic (TC-004-005 through TC-004-024)."""

import pytest

from app.models.user import UserRole
from app.services import user_service
from app.services.user_service import UserServiceError


class TestGetUsers:
    """User listing tests."""

    # TC-004-005 / TC-004-025
    def test_get_users_excludes_archived(self, db, admin_user, test_user):
        # Archive test_user
        test_user.is_archived = True
        db.session.commit()

        users = user_service.get_users(include_archived=False)
        emails = [u.email for u in users]
        assert admin_user.email in emails
        assert test_user.email not in emails

    # TC-004-026
    def test_get_users_includes_archived(self, db, admin_user, test_user):
        test_user.is_archived = True
        db.session.commit()

        users = user_service.get_users(include_archived=True)
        emails = [u.email for u in users]
        assert admin_user.email in emails
        assert test_user.email in emails


class TestCreateUser:
    """User creation tests."""

    # TC-004-006
    def test_create_user_success(self, db):
        user = user_service.create_user(
            email='newuser@example.com',
            full_name='New User',
            password='password123',
            role_value='editor',
        )
        assert user.id is not None
        assert user.email == 'newuser@example.com'
        assert user.role == UserRole.EDITOR

    # TC-004-011
    def test_create_user_all_roles(self, db):
        for role in ['admin', 'editor', 'viewer']:
            user = user_service.create_user(
                email=f'{role}test@example.com',
                full_name=f'{role} Test',
                password='password123',
                role_value=role,
            )
            assert user.role.value == role

    # TC-004-015
    def test_duplicate_email_rejected(self, db, test_user):
        with pytest.raises(UserServiceError, match='already exists'):
            user_service.create_user(
                email=test_user.email,
                full_name='Duplicate',
                password='password123',
                role_value='viewer',
            )

    # TC-004-016
    def test_case_insensitive_email_rejected(self, db, test_user):
        with pytest.raises(UserServiceError, match='already exists'):
            user_service.create_user(
                email=test_user.email.upper(),
                full_name='Duplicate',
                password='password123',
                role_value='viewer',
            )

    # TC-004-017
    def test_archived_user_email_still_unique(self, db, test_user):
        test_user.is_archived = True
        db.session.commit()

        with pytest.raises(UserServiceError, match='already exists'):
            user_service.create_user(
                email=test_user.email,
                full_name='Duplicate',
                password='password123',
                role_value='viewer',
            )

    def test_create_user_short_password(self, db):
        with pytest.raises(UserServiceError, match='8 characters'):
            user_service.create_user(
                email='short@example.com',
                full_name='Short',
                password='short',
                role_value='viewer',
            )

    def test_create_user_invalid_role(self, db):
        with pytest.raises(UserServiceError, match='Invalid role'):
            user_service.create_user(
                email='invalid@example.com',
                full_name='Invalid',
                password='password123',
                role_value='superadmin',
            )


class TestUpdateUser:
    """User update tests."""

    # TC-004-007
    def test_update_user_success(self, db, test_user):
        updated = user_service.update_user(
            user_id=test_user.id,
            email='updated@example.com',
            full_name='Updated Name',
            role_value='editor',
            expected_version=test_user.version,
        )
        assert updated.email == 'updated@example.com'
        assert updated.full_name == 'Updated Name'
        assert updated.role == UserRole.EDITOR

    # TC-004-012
    def test_change_role(self, db, test_user):
        updated = user_service.update_user(
            user_id=test_user.id,
            email=test_user.email,
            full_name=test_user.full_name,
            role_value='editor',
            expected_version=test_user.version,
        )
        assert updated.role == UserRole.EDITOR

    # TC-004-013
    def test_seeded_admin_cannot_be_demoted(self, db, seeded_admin):
        with pytest.raises(UserServiceError, match='cannot be demoted'):
            user_service.update_user(
                user_id=seeded_admin.id,
                email=seeded_admin.email,
                full_name=seeded_admin.full_name,
                role_value='viewer',
                expected_version=seeded_admin.version,
            )

    def test_optimistic_locking_conflict(self, db, test_user):
        with pytest.raises(UserServiceError, match='modified by another'):
            user_service.update_user(
                user_id=test_user.id,
                email=test_user.email,
                full_name='Conflict',
                role_value='viewer',
                expected_version=test_user.version + 999,
            )


class TestArchiveReactivate:
    """Archive and reactivate tests."""

    # TC-004-008
    def test_archive_user(self, db, test_user):
        user = user_service.archive_user(test_user.id)
        assert user.is_archived is True
        assert user.is_active is False

    # TC-004-009
    def test_reactivate_user(self, db, test_user):
        user_service.archive_user(test_user.id)
        user = user_service.reactivate_user(test_user.id)
        assert user.is_archived is False
        assert user.is_active is True

    # TC-004-014
    def test_seeded_admin_cannot_be_archived(self, db, seeded_admin):
        with pytest.raises(UserServiceError, match='cannot be archived'):
            user_service.archive_user(seeded_admin.id)


class TestChangePassword:
    """Password change tests."""

    # TC-004-018
    def test_change_password_success(self, db, test_user):
        user = user_service.change_password(
            user_id=test_user.id,
            current_password='password123',
            new_password='newpassword456',
        )
        assert user.check_password('newpassword456')

    # TC-004-019
    def test_wrong_current_password(self, db, test_user):
        with pytest.raises(UserServiceError, match='incorrect'):
            user_service.change_password(
                user_id=test_user.id,
                current_password='wrongpassword',
                new_password='newpassword456',
            )

    # TC-004-020
    def test_short_new_password(self, db, test_user):
        with pytest.raises(UserServiceError, match='8 characters'):
            user_service.change_password(
                user_id=test_user.id,
                current_password='password123',
                new_password='short',
            )


class TestAdminResetPassword:
    """Admin password reset tests."""

    # TC-004-022
    def test_admin_reset_password(self, db, test_user):
        user = user_service.admin_reset_password(
            user_id=test_user.id,
            new_password='resetpass123',
        )
        assert user.check_password('resetpass123')

    # TC-004-024
    def test_admin_reset_short_password(self, db, test_user):
        with pytest.raises(UserServiceError, match='8 characters'):
            user_service.admin_reset_password(
                user_id=test_user.id,
                new_password='short',
            )
