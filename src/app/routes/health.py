from flask import Blueprint, jsonify

from ..extensions import db

health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health_check():
    """Health check endpoint for container orchestration."""
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy'}), 200
    except Exception:
        return jsonify({'status': 'unhealthy'}), 503
