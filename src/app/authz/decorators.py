"""Role-based access control decorators (REQ-011 through REQ-015, REQ-018)."""

from functools import wraps

from flask import abort
from flask_login import current_user


def role_required(*roles):
    """Restrict access to users whose role value matches one of *roles*.

    Usage::

        @app.route('/admin')
        @login_required
        @role_required('admin')
        def admin_page():
            ...

    Must be applied **after** ``@login_required`` so that
    ``current_user`` is guaranteed to be authenticated.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.role.value not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
