"""Seeding utilities: admin users (REQ-008) and default shared attributes (REQ-034)."""

import logging
import os

logger = logging.getLogger(__name__)


def seed_admins() -> None:
    """Create admin users defined in ``ADMIN_SEEDS`` if they do not yet exist.

    ``ADMIN_SEEDS`` format: comma-separated ``email:password`` pairs, e.g.::

        admin@example.com:securepass,admin2@example.com:otherpass

    Skips gracefully when:
    - The env var is absent or empty.
    - The ``users`` table does not exist (e.g. before migrations run).
    - A DB connection cannot be established (e.g. during unit tests with an
      in-memory SQLite DB that has not yet had ``create_all()`` called).
    """
    seeds_str = os.environ.get('ADMIN_SEEDS', '').strip()
    if not seeds_str:
        return

    try:
        from sqlalchemy import inspect as sa_inspect

        from ..extensions import db
        from ..models.user import User, UserRole

        # Guard: users table may not exist yet (testing or pre-migration start-up)
        inspector = sa_inspect(db.engine)
        if 'users' not in inspector.get_table_names():
            logger.debug('Users table does not exist yet — skipping admin seeding.')
            return

        for entry in seeds_str.split(','):
            entry = entry.strip()
            if ':' not in entry:
                logger.warning('Invalid ADMIN_SEEDS entry (missing colon): %r', entry)
                continue

            email, _, password = entry.partition(':')
            email = User.normalize_email(email)
            password = password.strip()

            if not email or not password:
                logger.warning('Invalid ADMIN_SEEDS entry (empty email or password).')
                continue

            if len(password) < 8:
                logger.warning(
                    'Skipping admin seed for %s: password must be at least 8 characters.',
                    email,
                )
                continue

            existing = User.query.filter_by(email=email).first()
            if existing:
                logger.debug('Admin user already exists: %s', email)
                continue

            full_name = email.split('@')[0]
            user = User(
                email=email,
                full_name=full_name,
                role=UserRole.ADMIN,
                is_seeded=True,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            logger.info('Seeded admin user: %s', email)

    except Exception as exc:
        logger.debug('Admin seeding skipped: %s', exc)


# ---------------------------------------------------------------------------
# Default shared attribute seeding (REQ-034)
# ---------------------------------------------------------------------------

_DEFAULT_SHARED_ATTRIBUTES = ['Name', 'Team', 'URL', 'Description']


def seed_default_shared_attributes() -> None:
    """Create the four default shared attributes if they do not yet exist (REQ-034).

    Skips gracefully when the table does not exist (e.g. before migrations run).
    """
    try:
        from sqlalchemy import inspect as sa_inspect

        from ..extensions import db
        from ..models.shared_attribute import SharedAttributeDefinition

        inspector = sa_inspect(db.engine)
        if 'shared_attribute_definitions' not in inspector.get_table_names():
            logger.debug('shared_attribute_definitions table does not exist yet — skipping.')
            return

        for attr_name in _DEFAULT_SHARED_ATTRIBUTES:
            existing = SharedAttributeDefinition.query.filter_by(name=attr_name).first()
            if existing:
                logger.debug('Default shared attribute already exists: %s', attr_name)
                continue
            attr = SharedAttributeDefinition(name=attr_name, is_default=True, is_active=True)
            db.session.add(attr)
            logger.info('Seeded default shared attribute: %s', attr_name)

        db.session.commit()

    except Exception as exc:
        logger.debug('Default shared attribute seeding skipped: %s', exc)
