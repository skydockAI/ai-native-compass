"""WTForms form classes for route handlers."""

from flask_wtf import FlaskForm
from wtforms import HiddenField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
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
