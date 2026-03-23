"""Tests for template service business logic (TS-006)."""

import pytest

from app.models.template import ArtifactType, ArtifactValueType
from app.services import template_service
from app.services.template_service import TemplateServiceError


class TestGetTemplates:

    # TC-006-001
    def test_get_templates_excludes_archived(self, db):
        template_service.create_template(name='Active Template')
        t2 = template_service.create_template(name='Archived Template')
        t2.is_archived = True
        db.session.commit()

        result = template_service.get_templates(include_archived=False)
        names = [t.name for t in result]
        assert 'Active Template' in names
        assert 'Archived Template' not in names

    # TC-006-002
    def test_get_templates_includes_archived(self, db):
        template_service.create_template(name='Active Template')
        t2 = template_service.create_template(name='Archived Template')
        t2.is_archived = True
        db.session.commit()

        result = template_service.get_templates(include_archived=True)
        names = [t.name for t in result]
        assert 'Active Template' in names
        assert 'Archived Template' in names


class TestCreateTemplate:

    # TC-006-003
    def test_create_template_success(self, db):
        tmpl = template_service.create_template(name='Standard', description='Desc')
        assert tmpl.id is not None
        assert tmpl.name == 'Standard'
        assert tmpl.description == 'Desc'
        assert tmpl.is_active is True
        assert tmpl.is_archived is False

    def test_create_template_without_description(self, db):
        tmpl = template_service.create_template(name='No Desc')
        assert tmpl.description is None

    # TC-006-007
    def test_duplicate_name_rejected(self, db):
        template_service.create_template(name='Alpha')
        with pytest.raises(TemplateServiceError, match='already exists'):
            template_service.create_template(name='Alpha')

    def test_duplicate_name_case_insensitive(self, db):
        template_service.create_template(name='Alpha')
        with pytest.raises(TemplateServiceError, match='already exists'):
            template_service.create_template(name='ALPHA')

    def test_empty_name_rejected(self, db):
        with pytest.raises(TemplateServiceError, match='required'):
            template_service.create_template(name='')

    def test_whitespace_name_rejected(self, db):
        with pytest.raises(TemplateServiceError, match='required'):
            template_service.create_template(name='   ')


class TestUpdateTemplate:

    # TC-006-005
    def test_update_template_success(self, db):
        tmpl = template_service.create_template(name='Old', description='Old desc')
        updated = template_service.update_template(
            template_id=tmpl.id,
            name='New',
            description='New desc',
            expected_version=tmpl.version,
        )
        assert updated.name == 'New'
        assert updated.description == 'New desc'

    # TC-006-008
    def test_rename_to_existing_name_rejected(self, db):
        template_service.create_template(name='Alpha')
        beta = template_service.create_template(name='Beta')
        with pytest.raises(TemplateServiceError, match='already exists'):
            template_service.update_template(
                template_id=beta.id,
                name='Alpha',
                description=None,
                expected_version=beta.version,
            )

    def test_rename_to_same_name_allowed(self, db):
        tmpl = template_service.create_template(name='Same')
        updated = template_service.update_template(
            template_id=tmpl.id,
            name='Same',
            description='Updated',
            expected_version=tmpl.version,
        )
        assert updated.name == 'Same'

    # TC-006-013
    def test_optimistic_locking_conflict(self, db):
        tmpl = template_service.create_template(name='Conflict')
        with pytest.raises(TemplateServiceError, match='modified by another'):
            template_service.update_template(
                template_id=tmpl.id,
                name='Conflict',
                description=None,
                expected_version=tmpl.version + 999,
            )

    def test_update_nonexistent_template(self, db):
        with pytest.raises(TemplateServiceError, match='not found'):
            template_service.update_template(
                template_id=99999, name='Ghost', description=None, expected_version=1
            )


class TestArchiveReactivateTemplate:

    # TC-006-009
    def test_archive_template_no_blocking_repos(self, db):
        tmpl = template_service.create_template(name='ToArchive')
        archived = template_service.archive_template(tmpl.id)
        assert archived.is_archived is True
        assert archived.is_active is False

    # TC-006-012
    def test_reactivate_template(self, db):
        tmpl = template_service.create_template(name='Restore Me')
        template_service.archive_template(tmpl.id)
        restored = template_service.reactivate_template(tmpl.id)
        assert restored.is_archived is False
        assert restored.is_active is True

    # TC-006-030
    def test_archive_already_archived_raises(self, db):
        tmpl = template_service.create_template(name='AlreadyGone')
        template_service.archive_template(tmpl.id)
        with pytest.raises(TemplateServiceError, match='already archived'):
            template_service.archive_template(tmpl.id)

    def test_reactivate_active_template_raises(self, db):
        tmpl = template_service.create_template(name='StillActive')
        with pytest.raises(TemplateServiceError, match='not archived'):
            template_service.reactivate_template(tmpl.id)

    def test_archive_nonexistent_template(self, db):
        with pytest.raises(TemplateServiceError, match='not found'):
            template_service.archive_template(99999)


class TestAddArtifact:

    def _make_template(self, db):
        return template_service.create_template(name='ArtT')

    # TC-006-015
    def test_add_document_artifact(self, db):
        tmpl = self._make_template(db)
        a = template_service.add_artifact(
            template_id=tmpl.id,
            artifact_type=ArtifactType.document,
            name='Architecture Doc',
        )
        assert a.id is not None
        assert a.type == ArtifactType.document
        assert a.value_type is None
        assert a.is_required is False

    # TC-006-016
    def test_add_skill_artifact(self, db):
        tmpl = self._make_template(db)
        a = template_service.add_artifact(
            template_id=tmpl.id,
            artifact_type=ArtifactType.skill,
            name='Python',
        )
        assert a.type == ArtifactType.skill

    # TC-006-017
    def test_add_agent_artifact(self, db):
        tmpl = self._make_template(db)
        a = template_service.add_artifact(
            template_id=tmpl.id,
            artifact_type=ArtifactType.agent,
            name='Code Review Agent',
        )
        assert a.type == ArtifactType.agent

    # TC-006-018
    def test_add_other_text_artifact(self, db):
        tmpl = self._make_template(db)
        a = template_service.add_artifact(
            template_id=tmpl.id,
            artifact_type=ArtifactType.other,
            name='Notes',
            value_type=ArtifactValueType.text,
        )
        assert a.value_type == ArtifactValueType.text

    # TC-006-019
    def test_add_other_list_artifact(self, db):
        tmpl = self._make_template(db)
        a = template_service.add_artifact(
            template_id=tmpl.id,
            artifact_type=ArtifactType.other,
            name='Priority',
            value_type=ArtifactValueType.list,
        )
        assert a.value_type == ArtifactValueType.list

    # TC-006-020
    def test_other_artifact_required_flag(self, db):
        tmpl = self._make_template(db)
        a = template_service.add_artifact(
            template_id=tmpl.id,
            artifact_type=ArtifactType.other,
            name='Score',
            value_type=ArtifactValueType.number,
            is_required=True,
        )
        assert a.is_required is True

    # TC-006-021
    def test_document_artifact_required_flag_ignored(self, db):
        tmpl = self._make_template(db)
        a = template_service.add_artifact(
            template_id=tmpl.id,
            artifact_type=ArtifactType.document,
            name='ADR',
            is_required=True,  # should be ignored for non-Other
        )
        assert a.is_required is False

    def test_other_artifact_without_value_type_raises(self, db):
        tmpl = self._make_template(db)
        with pytest.raises(TemplateServiceError, match='Value type is required'):
            template_service.add_artifact(
                template_id=tmpl.id,
                artifact_type=ArtifactType.other,
                name='Oops',
                value_type=None,
            )

    def test_add_artifact_to_nonexistent_template_raises(self, db):
        with pytest.raises(TemplateServiceError, match='not found'):
            template_service.add_artifact(
                template_id=99999,
                artifact_type=ArtifactType.document,
                name='X',
            )

    def test_empty_artifact_name_raises(self, db):
        tmpl = self._make_template(db)
        with pytest.raises(TemplateServiceError, match='required'):
            template_service.add_artifact(
                template_id=tmpl.id,
                artifact_type=ArtifactType.document,
                name='',
            )


class TestUpdateArtifact:

    # TC-006-023
    def test_update_artifact(self, db):
        tmpl = template_service.create_template(name='UpdT')
        a = template_service.add_artifact(
            template_id=tmpl.id,
            artifact_type=ArtifactType.document,
            name='Old Name',
        )
        updated = template_service.update_artifact(
            artifact_id=a.id,
            name='New Name',
            description='Updated desc',
        )
        assert updated.name == 'New Name'
        assert updated.description == 'Updated desc'

    def test_update_nonexistent_artifact_raises(self, db):
        with pytest.raises(TemplateServiceError, match='not found'):
            template_service.update_artifact(artifact_id=99999, name='X')


class TestRemoveArtifact:

    # TC-006-024 / TC-008-004: remove_artifact soft-deletes (is_active=False), row preserved
    def test_remove_artifact_soft_deletes(self, db):
        tmpl = template_service.create_template(name='DelT')
        a = template_service.add_artifact(
            template_id=tmpl.id,
            artifact_type=ArtifactType.skill,
            name='To Remove',
        )
        artifact_id = a.id
        template_service.remove_artifact(artifact_id)

        from app.models.template import TemplateArtifact
        fetched = db.session.get(TemplateArtifact, artifact_id)
        assert fetched is not None
        assert fetched.is_active is False

    def test_remove_nonexistent_artifact_raises(self, db):
        with pytest.raises(TemplateServiceError, match='not found'):
            template_service.remove_artifact(99999)


class TestListOptions:

    def _make_list_artifact(self, db):
        tmpl = template_service.create_template(name='LT')
        return template_service.add_artifact(
            template_id=tmpl.id,
            artifact_type=ArtifactType.other,
            name='Priority',
            value_type=ArtifactValueType.list,
        )

    # TC-006-025
    def test_add_list_option(self, db):
        a = self._make_list_artifact(db)
        opt = template_service.add_list_option(artifact_id=a.id, value='High')
        assert opt.id is not None
        assert opt.value == 'High'
        assert opt.is_active is True

    # TC-006-026
    def test_update_list_option(self, db):
        a = self._make_list_artifact(db)
        opt = template_service.add_list_option(artifact_id=a.id, value='Old')
        updated = template_service.update_list_option(option_id=opt.id, value='New')
        assert updated.value == 'New'

    # TC-006-027
    def test_deactivate_list_option(self, db):
        a = self._make_list_artifact(db)
        opt = template_service.add_list_option(artifact_id=a.id, value='Active')
        deactivated = template_service.deactivate_list_option(opt.id)
        assert deactivated.is_active is False

    # TC-006-028
    def test_delete_unused_list_option(self, db):
        a = self._make_list_artifact(db)
        opt = template_service.add_list_option(artifact_id=a.id, value='Deletable')
        option_id = opt.id
        template_service.delete_list_option(option_id)

        from app.models.template import ArtifactListOption
        assert db.session.get(ArtifactListOption, option_id) is None

    def test_add_list_option_to_non_list_artifact_raises(self, db):
        tmpl = template_service.create_template(name='NLAT')
        a = template_service.add_artifact(
            template_id=tmpl.id,
            artifact_type=ArtifactType.document,
            name='Doc',
        )
        with pytest.raises(TemplateServiceError, match='Other:list'):
            template_service.add_list_option(artifact_id=a.id, value='Bad')

    def test_add_empty_option_value_raises(self, db):
        a = self._make_list_artifact(db)
        with pytest.raises(TemplateServiceError, match='required'):
            template_service.add_list_option(artifact_id=a.id, value='')

    def test_update_nonexistent_option_raises(self, db):
        with pytest.raises(TemplateServiceError, match='not found'):
            template_service.update_list_option(option_id=99999, value='X')

    def test_deactivate_nonexistent_option_raises(self, db):
        with pytest.raises(TemplateServiceError, match='not found'):
            template_service.deactivate_list_option(99999)

    def test_delete_nonexistent_option_raises(self, db):
        with pytest.raises(TemplateServiceError, match='not found'):
            template_service.delete_list_option(99999)
