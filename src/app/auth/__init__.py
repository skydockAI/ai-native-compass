"""Authentication module.

``authenticate_user`` is the single entry point for authentication.
Replacing this function with an SSO implementation is all that is required
to switch authentication strategies (REQ-010).
"""

from .local import authenticate_user

__all__ = ['authenticate_user']
