"""Tests for RepoTemplate, TemplateArtifact, and ArtifactListOption models."""

from app.models.template import (
    ArtifactListOption,
    ArtifactType,
    ArtifactValueType,
    RepoTemplate,
    TemplateArtifact,
)


class TestRepoTemplateModel:

    def test_create_template(self, db):
        tmpl = RepoTemplate(name='My Template', description='Test')
        db.session.add(tmpl)
        db.session.commit()
        assert tmpl.id is not None
        assert tmpl.name == 'My Template'
        assert tmpl.is_active is True
        assert tmpl.is_archived is False
        assert tmpl.version == 1

    def test_template_without_description(self, db):
        tmpl = RepoTemplate(name='No Desc')
        db.session.add(tmpl)
        db.session.commit()
        assert tmpl.description is None

    def test_template_repr(self, db):
        tmpl = RepoTemplate(name='Repr Test')
        assert '<RepoTemplate Repr Test>' in repr(tmpl)


class TestTemplateArtifactModel:

    def _make_template(self, db, name='T'):
        tmpl = RepoTemplate(name=name)
        db.session.add(tmpl)
        db.session.commit()
        return tmpl

    def test_create_document_artifact(self, db):
        tmpl = self._make_template(db, 'DocT')
        a = TemplateArtifact(
            template_id=tmpl.id,
            type=ArtifactType.document,
            name='Architecture Doc',
        )
        db.session.add(a)
        db.session.commit()
        assert a.id is not None
        assert a.type == ArtifactType.document
        assert a.value_type is None
        assert a.is_required is False

    def test_create_other_list_artifact(self, db):
        tmpl = self._make_template(db, 'OtherT')
        a = TemplateArtifact(
            template_id=tmpl.id,
            type=ArtifactType.other,
            name='Priority',
            value_type=ArtifactValueType.list,
            is_required=True,
        )
        db.session.add(a)
        db.session.commit()
        assert a.value_type == ArtifactValueType.list
        assert a.is_required is True

    def test_artifact_belongs_to_template(self, db):
        tmpl = self._make_template(db, 'RelT')
        a = TemplateArtifact(template_id=tmpl.id, type=ArtifactType.skill, name='S1')
        db.session.add(a)
        db.session.commit()
        assert a.template.id == tmpl.id
        assert a in tmpl.artifacts


class TestArtifactListOptionModel:

    def _make_artifact(self, db):
        tmpl = RepoTemplate(name='LT')
        db.session.add(tmpl)
        db.session.commit()
        a = TemplateArtifact(
            template_id=tmpl.id,
            type=ArtifactType.other,
            name='ListArt',
            value_type=ArtifactValueType.list,
        )
        db.session.add(a)
        db.session.commit()
        return a

    def test_create_list_option(self, db):
        a = self._make_artifact(db)
        opt = ArtifactListOption(artifact_id=a.id, value='Option A')
        db.session.add(opt)
        db.session.commit()
        assert opt.id is not None
        assert opt.value == 'Option A'
        assert opt.is_active is True

    def test_list_option_belongs_to_artifact(self, db):
        a = self._make_artifact(db)
        opt = ArtifactListOption(artifact_id=a.id, value='X')
        db.session.add(opt)
        db.session.commit()
        assert opt.artifact.id == a.id
        assert opt in a.list_options
