"""Audit logging service — explicit service-level calls (REQ-048, REQ-059, REQ-060).

All audit entries are permanent and are never deleted.
Callers pass optional user_id; None is valid for system-generated events.
"""

from ..extensions import db
from ..models.audit_log import AuditLog


def log(action, entity_type, entity_id, before=None, after=None, user_id=None):
    """Record a single audit event.

    Parameters
    ----------
    action:      str — one of: login, logout, create, update, archive,
                               reactivate, role_change, template_change
    entity_type: str — one of: user, team, product, repository, template, session
    entity_id:   int — primary key of the affected entity
    before:      dict | None — state before the change (None for create / login)
    after:       dict | None — state after the change (None for delete / logout)
    user_id:     int | None — acting user's id (None for system events)
    """
    entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_value=before,
        after_value=after,
        user_id=user_id,
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def get_audit_logs(
    entity_type=None,
    action=None,
    user_id=None,
    date_from=None,
    date_to=None,
    q=None,
    page=1,
    per_page=50,
):
    """Return a SQLAlchemy ``Pagination`` object of AuditLog entries.

    Filters are applied additively (AND logic).  Results are ordered newest first.
    """
    query = AuditLog.query.order_by(AuditLog.timestamp.desc())

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        try:
            query = query.filter(AuditLog.user_id == int(user_id))
        except (TypeError, ValueError):
            pass
    if date_from:
        query = query.filter(AuditLog.timestamp >= date_from)
    if date_to:
        query = query.filter(AuditLog.timestamp <= date_to)
    if q:
        # Text search against serialised JSON values and entity fields
        like_q = f'%{q}%'
        query = query.filter(
            db.or_(
                db.cast(AuditLog.before_value, db.Text).ilike(like_q),
                db.cast(AuditLog.after_value, db.Text).ilike(like_q),
                AuditLog.entity_type.ilike(like_q),
                AuditLog.action.ilike(like_q),
            )
        )

    return query.paginate(page=page, per_page=per_page, error_out=False)
