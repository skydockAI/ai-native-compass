"""Shared attribute management routes (REQ-034, REQ-035, REQ-036)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from ..authz import role_required
from ..services import shared_attribute_service
from ..services.shared_attribute_service import SharedAttributeServiceError
from .forms import SharedAttributeCreateForm, SharedAttributeEditForm

shared_attributes_bp = Blueprint('shared_attributes', __name__, url_prefix='/shared-attributes')


# --------------------------------------------------------------------------
# List (Admin only)
# --------------------------------------------------------------------------

@shared_attributes_bp.route('/')
@login_required
@role_required('admin')
def index():
    """List all shared attribute definitions."""
    show_inactive = request.args.get('inactive', '0') == '1'
    attributes = shared_attribute_service.get_attributes(include_inactive=show_inactive)
    return render_template(
        'shared_attributes/list.html',
        attributes=attributes,
        show_inactive=show_inactive,
    )


# --------------------------------------------------------------------------
# Create (Admin only)
# --------------------------------------------------------------------------

@shared_attributes_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create():
    """Display and process new-attribute form."""
    form = SharedAttributeCreateForm()
    if form.validate_on_submit():
        try:
            shared_attribute_service.create_attribute(name=form.name.data)
            flash('Shared attribute created successfully.', 'success')
            return redirect(url_for('shared_attributes.index'))
        except SharedAttributeServiceError as exc:
            flash(str(exc), 'danger')

    return render_template('shared_attributes/form.html', form=form, is_edit=False)


# --------------------------------------------------------------------------
# Edit (Admin only, custom attributes only)
# --------------------------------------------------------------------------

@shared_attributes_bp.route('/<int:attr_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit(attr_id):
    """Display and process edit-attribute form."""
    attr = shared_attribute_service.get_attribute_by_id(attr_id)
    if attr is None:
        flash('Shared attribute not found.', 'danger')
        return redirect(url_for('shared_attributes.index'))

    if attr.is_default:
        flash('Default attributes cannot be renamed.', 'danger')
        return redirect(url_for('shared_attributes.index'))

    form = SharedAttributeEditForm()
    if request.method == 'GET':
        form.name.data = attr.name

    if form.validate_on_submit():
        try:
            shared_attribute_service.update_attribute(attr_id=attr_id, name=form.name.data)
            flash('Shared attribute updated successfully.', 'success')
            return redirect(url_for('shared_attributes.index'))
        except SharedAttributeServiceError as exc:
            flash(str(exc), 'danger')

    return render_template('shared_attributes/form.html', form=form, is_edit=True, attribute=attr)


# --------------------------------------------------------------------------
# Deactivate / Reactivate (Admin only, custom attributes only)
# --------------------------------------------------------------------------

@shared_attributes_bp.route('/<int:attr_id>/deactivate', methods=['POST'])
@login_required
@role_required('admin')
def deactivate(attr_id):
    """Deactivate a custom shared attribute."""
    try:
        shared_attribute_service.deactivate_attribute(attr_id)
        flash('Shared attribute deactivated.', 'success')
    except SharedAttributeServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('shared_attributes.index'))


@shared_attributes_bp.route('/<int:attr_id>/reactivate', methods=['POST'])
@login_required
@role_required('admin')
def reactivate(attr_id):
    """Reactivate a previously deactivated custom shared attribute."""
    try:
        shared_attribute_service.reactivate_attribute(attr_id)
        flash('Shared attribute reactivated.', 'success')
    except SharedAttributeServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('shared_attributes.index', inactive='1'))
