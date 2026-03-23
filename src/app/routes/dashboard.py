from flask import Blueprint, render_template
from flask_login import login_required

from ..services import dashboard_service

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page with entity summary counts (REQ-055, REQ-057)."""
    counts = dashboard_service.get_dashboard_counts()
    return render_template('dashboard/index.html', counts=counts)
