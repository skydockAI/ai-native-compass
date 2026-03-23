"""WTForms form classes for route handlers."""

from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, IntegerField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


class UserCreateForm(FlaskForm):
    """Form for creating a new user (admin only)."""

    email = StringField('Email address', validators=[DataRequired(), Email()])
    full_name = StringField('Full name', validators=[DataRequired(), Length(max=255)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.'),
    ])
    confirm_password = PasswordField('Confirm password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.'),
    ])
    role = SelectField('Role', choices=[
        ('viewer', 'Viewer'),
        ('editor', 'Editor'),
        ('admin', 'Admin'),
    ], validators=[DataRequired()])
    submit = SubmitField('Create User')


class UserEditForm(FlaskForm):
    """Form for editing an existing user (admin only)."""

    email = StringField('Email address', validators=[DataRequired(), Email()])
    full_name = StringField('Full name', validators=[DataRequired(), Length(max=255)])
    role = SelectField('Role', choices=[
        ('viewer', 'Viewer'),
        ('editor', 'Editor'),
        ('admin', 'Admin'),
    ], validators=[DataRequired()])
    version = HiddenField('version')
    submit = SubmitField('Save Changes')


class ChangePasswordForm(FlaskForm):
    """Self-service password change form."""

    current_password = PasswordField('Current password', validators=[DataRequired()])
    new_password = PasswordField('New password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.'),
    ])
    confirm_password = PasswordField('Confirm new password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.'),
    ])
    submit = SubmitField('Change Password')


class AdminResetPasswordForm(FlaskForm):
    """Admin password reset form."""

    new_password = PasswordField('New password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.'),
    ])
    confirm_password = PasswordField('Confirm new password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.'),
    ])
    submit = SubmitField('Reset Password')


class TeamCreateForm(FlaskForm):
    """Form for creating a new team (Admin/Editor)."""

    name = StringField('Team name', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Create Team')


class TeamEditForm(FlaskForm):
    """Form for editing an existing team (Admin/Editor)."""

    name = StringField('Team name', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=2000)])
    version = HiddenField('version')
    submit = SubmitField('Save Changes')


class TemplateCreateForm(FlaskForm):
    """Form for creating a new repo template (Admin only)."""

    name = StringField('Template name', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Create Template')


class TemplateEditForm(FlaskForm):
    """Form for editing an existing repo template (Admin only)."""

    name = StringField('Template name', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=2000)])
    version = HiddenField('version')
    submit = SubmitField('Save Changes')


class ArtifactForm(FlaskForm):
    """Form for adding/editing a template artifact (Admin only)."""

    type = SelectField('Type', choices=[
        ('document', 'Document'),
        ('skill', 'Skill'),
        ('agent', 'Agent'),
        ('other', 'Other'),
    ], validators=[DataRequired()])
    name = StringField('Artifact name', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=2000)])
    value_type = SelectField('Value type', choices=[
        ('', '— select —'),
        ('text', 'Text'),
        ('number', 'Number'),
        ('boolean', 'Boolean (True/False/N/A)'),
        ('list', 'List'),
    ], validators=[Optional()])
    is_required = BooleanField('Required')
    display_order = IntegerField('Display order', default=0, validators=[Optional()])
    submit = SubmitField('Save Artifact')


class ListOptionForm(FlaskForm):
    """Form for adding/editing a list option (Admin only)."""

    value = StringField('Option value', validators=[DataRequired(), Length(max=255)])
    display_order = IntegerField('Display order', default=0, validators=[Optional()])
    submit = SubmitField('Save Option')


class RepositoryCreateForm(FlaskForm):
    """Form for creating a new repository (Admin/Editor).

    Dynamic artifact fields are not WTForms fields — they are read directly from
    request.form in the route handler after HTMX loads them.
    """

    template_id = SelectField('Template', coerce=int, validators=[DataRequired(message='Please select a template.')])
    name = StringField('Repository name', validators=[DataRequired(), Length(max=255)])
    url = StringField('Repository URL', validators=[DataRequired(), Length(max=2048)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=2000)])
    team_id = SelectField('Team', coerce=int, validators=[DataRequired(message='Please select a team.')])
    submit = SubmitField('Create Repository')


class RepositoryEditForm(FlaskForm):
    """Form for editing an existing repository (Admin/Editor).

    template_id is read-only — displayed in the form but not a WTForms field
    so it cannot be changed via form submission (REQ-029).
    """

    name = StringField('Repository name', validators=[DataRequired(), Length(max=255)])
    url = StringField('Repository URL', validators=[DataRequired(), Length(max=2048)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=2000)])
    team_id = SelectField('Team', coerce=int, validators=[DataRequired(message='Please select a team.')])
    version = HiddenField('version')
    submit = SubmitField('Save Changes')


class RepositoryDuplicateForm(FlaskForm):
    """Form for duplicating a repository with a new name and URL (REQ-052)."""

    name = StringField('Repository name', validators=[DataRequired(), Length(max=255)])
    url = StringField('Repository URL', validators=[DataRequired(), Length(max=2048)])
    submit = SubmitField('Duplicate Repository')


class SharedAttributeCreateForm(FlaskForm):
    """Form for creating a new custom shared attribute (Admin only)."""

    name = StringField('Attribute name', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Create Attribute')


class SharedAttributeEditForm(FlaskForm):
    """Form for renaming a custom shared attribute (Admin only)."""

    name = StringField('Attribute name', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Save Changes')
