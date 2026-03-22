import os

from flask import Flask

from .config import config_by_name
from .extensions import db, migrate, login_manager, csrf


def create_app(config_name=None):
    """Flask application factory."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['production']))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Placeholder user loader — will be replaced with real User model in DI-002
    @login_manager.user_loader
    def load_user(user_id):
        return None

    # Register blueprints
    from .routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from .routes.health import health_bp
    app.register_blueprint(health_bp)

    return app
