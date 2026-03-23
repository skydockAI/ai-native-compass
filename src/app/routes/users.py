"""User management routes — admin-only CRUD + self-service password change (REQ-018)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..authz import role_required
from ..services import user_service
from ..services.user_service import UserServiceError
from .forms import (
    AdminResetPasswordForm,
    ChangePasswordForm,
    UserCreateForm,
    UserEditForm,
)

users_bp = Blueprint('users', __name__, url_prefix='/users')


# --------------------------------------------------------------------------
# User list (admin only)
# --------------------------------------------------------------------------

@users_bp.route('/')
@login_required
@role_required('admin')
def index():
    """User list with active/archived filter (REQ-047)."""
    show_archived = request.args.get('archived', '0') == '1'
    users = user_service.get_users(include_archived=True) if show_archived else user_service.get_users()
    return render_template(
        'users/list.html',
        users=users,
        show_archived=show_archived,
    )


# --------------------------------------------------------------------------
# Create user (admin only)
# --------------------------------------------------------------------------

@users_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create():
    """Display and process new-user form."""
    form = UserCreateForm()
    if form.validate_on_submit():
        try:
            user_service.create_user(
                email=form.email.data,
                full_name=form.full_name.data,
                password=form.password.data,
                role_value=form.role.data,
            )
            flash('User created successfully.', 'success')
            return redirect(url_for('users.index'))
        except UserServiceError as exc:
            flash(str(exc), 'danger')

    return render_template('users/form.html', form=form, is_edit=False)


# --------------------------------------------------------------------------
# Edit user (admin only)
# --------------------------------------------------------------------------

@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit(user_id):
    """Display and process edit-user form."""
    user = user_service.get_user_by_id(user_id)
    if user is None:
        flash('User not found.', 'danger')
        return redirect(url_for('users.index'))

    form = UserEditForm(obj=user)

    if request.method == 'GET':
        form.email.data = user.email
        form.full_name.data = user.full_name
        form.role.data = user.role.value
        form.version.data = user.version

    if form.validate_on_submit():
        try:
            user_service.update_user(
                user_id=user_id,
                email=form.email.data,
                full_name=form.full_name.data,
                role_value=form.role.data,
                expected_version=int(form.version.data),
            )
            flash('User updated successfully.', 'success')
            return redirect(url_for('users.index'))
        except UserServiceError as exc:
            flash(str(exc), 'danger')

    return render_template('users/form.html', form=form, is_edit=True, user=user)


# --------------------------------------------------------------------------
# Archive / Reactivate user (admin only)
# --------------------------------------------------------------------------

@users_bp.route('/<int:user_id>/archive', methods=['POST'])
@login_required
@role_required('admin')
def archive(user_id):
    """Archive a user account."""
    try:
        user_service.archive_user(user_id)
        flash('User archived successfully.', 'success')
    except UserServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('users.index'))


@users_bp.route('/<int:user_id>/reactivate', methods=['POST'])
@login_required
@role_required('admin')
def reactivate(user_id):
    """Reactivate an archived user account."""
    try:
        user_service.reactivate_user(user_id)
        flash('User reactivated successfully.', 'success')
    except UserServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('users.index', archived='1'))


# --------------------------------------------------------------------------
# Self-service password change (any authenticated user)
# --------------------------------------------------------------------------

@users_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Self-service password change (REQ-005)."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        try:
            user_service.change_password(
                user_id=current_user.id,
                current_password=form.current_password.data,
                new_password=form.new_password.data,
            )
            flash('Password changed successfully.', 'success')
            return redirect(url_for('dashboard.index'))
        except UserServiceError as exc:
            flash(str(exc), 'danger')

    return render_template('users/change_password.html', form=form)


# --------------------------------------------------------------------------
# Admin password reset (admin only)
# --------------------------------------------------------------------------

@users_bp.route('/<int:user_id>/reset-password', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def reset_password(user_id):
    """Admin password reset for any user (REQ-006)."""
    user = user_service.get_user_by_id(user_id)
    if user is None:
        flash('User not found.', 'danger')
        return redirect(url_for('users.index'))

    form = AdminResetPasswordForm()
    if form.validate_on_submit():
        try:
            user_service.admin_reset_password(
                user_id=user_id,
                new_password=form.new_password.data,
            )
            flash(f'Password reset successfully for {user.full_name}.', 'success')
            return redirect(url_for('users.index'))
        except UserServiceError as exc:
            flash(str(exc), 'danger')

    return render_template('users/reset_password.html', form=form, user=user)
