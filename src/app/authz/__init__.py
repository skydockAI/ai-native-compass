"""Authorization module — role-based access control."""

from .decorators import role_required

__all__ = ['role_required']
