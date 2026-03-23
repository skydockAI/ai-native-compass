"""Audit log routes — admin-only (REQ-061, REQ-062)."""

from datetime import datetime

from flask import Blueprint, request, render_template
from flask_login import login_required

from ..authz import role_required
from ..services import audit_service
from ..models.user import User

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

# Valid filter values for dropdowns
ENTITY_TYPES = ['user', 'team', 'product', 'repository', 'template', 'session']
ACTIONS = ['login', 'logout', 'create', 'update', 'archive', 'reactivate', 'role_change', 'template_change']


@audit_bp.route('/')
@login_required
@role_required('admin')
def index():
    """Audit log list with filtering, search and pagination (REQ-062)."""
    entity_type = request.args.get('entity_type', '')
    action = request.args.get('action', '')
    user_id_filter = request.args.get('user_id', '')
    date_from_str = request.args.get('date_from', '')
    date_to_str = request.args.get('date_to', '')
    q = request.args.get('q', '')
    try:
        page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        page = 1

    date_from = _parse_date(date_from_str)
    date_to = _parse_date(date_to_str)

    pagination = audit_service.get_audit_logs(
        entity_type=entity_type or None,
        action=action or None,
        user_id=user_id_filter or None,
        date_from=date_from,
        date_to=date_to,
        q=q or None,
        page=page,
    )

    users = User.query.filter_by(is_archived=False).order_by(User.full_name).all()

    ctx = dict(
        pagination=pagination,
        logs=pagination.items,
        entity_types=ENTITY_TYPES,
        actions=ACTIONS,
        users=users,
        entity_type_filter=entity_type,
        action_filter=action,
        user_id_filter=user_id_filter,
        date_from=date_from_str,
        date_to=date_to_str,
        q=q,
    )

    if request.headers.get('HX-Request'):
        return render_template('audit/partials/audit_table.html', **ctx)
    return render_template('audit/list.html', **ctx)


def _parse_date(date_str):
    """Parse a YYYY-MM-DD string to a datetime or None."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d')
    except ValueError:
        return None
