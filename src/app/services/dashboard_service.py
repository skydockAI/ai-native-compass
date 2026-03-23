"""Dashboard aggregation service (REQ-057)."""

from ..models.product import Product
from ..models.repository import Repository
from ..models.team import Team
from ..models.template import RepoTemplate
from ..models.user import User


def get_dashboard_counts():
    """Return counts of active (non-archived) entities for the dashboard summary cards.

    Returns a dict with keys: products, repositories, templates, teams, users.
    Counts exclude archived entities per REQ-057.
    """
    return {
        'products': Product.query.filter_by(is_archived=False).count(),
        'repositories': Repository.query.filter_by(is_archived=False).count(),
        'templates': RepoTemplate.query.filter_by(is_archived=False).count(),
        'teams': Team.query.filter_by(is_archived=False).count(),
        'users': User.query.filter_by(is_archived=False).count(),
    }
