import os

from flask import Flask, redirect, request, url_for
from flask_login import current_user, logout_user

from .config import config_by_name
from .extensions import csrf, db, login_manager, migrate


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

    # Flask-Login configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User
        return db.session.get(User, int(user_id))

    # Register blueprints
    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    from .routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from .routes.health import health_bp
    app.register_blueprint(health_bp)

    from .routes.users import users_bp
    app.register_blueprint(users_bp)

    from .routes.teams import teams_bp
    app.register_blueprint(teams_bp)

    # Before-request: enforce active/archived check on every authenticated
    # request so that deactivated users lose access immediately (REQ-007).
    @app.before_request
    def enforce_user_active():
        if request.path.startswith('/static'):
            return
        if current_user.is_authenticated:
            if not current_user.is_active or current_user.is_archived:
                logout_user()
                return redirect(url_for('auth.login'))

    # Seed admin users defined in ADMIN_SEEDS on startup (REQ-008).
    # Wrapped in try/except so that test environments or pre-migration starts
    # do not raise an error when the users table does not yet exist.
    try:
        with app.app_context():
            from .utils.seed import seed_admins
            seed_admins()
    except Exception:
        pass

    return app
