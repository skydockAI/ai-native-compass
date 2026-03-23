"""Product management business logic (REQ-023–026, REQ-053, REQ-054)."""

from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models.product import Product
from ..models.repository import product_repository, Repository


class ProductServiceError(Exception):
    """Raised when a product operation fails with a user-facing message."""


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def get_products(include_archived=False):
    """Return products ordered by name, optionally including archived."""
    query = Product.query.order_by(Product.name)
    if not include_archived:
        query = query.filter_by(is_archived=False)
    return query.all()


def get_product_by_id(product_id):
    """Return a single Product by primary key or ``None``."""
    return db.session.get(Product, product_id)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_product(name, description=None):
    """Create a new product (REQ-023, REQ-024).

    Raises ``ProductServiceError`` on validation failure or duplicate name.
    """
    name = _validate_name(name)
    _check_name_unique(name, exclude_id=None)

    product = Product(name=name, description=description or None)
    try:
        db.session.add(product)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ProductServiceError(
            f'A product named "{name}" already exists.'
        )
    return product


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def update_product(product_id, name, description=None, expected_version=None):
    """Update an existing product (REQ-053).

    Raises ``ProductServiceError`` on validation or concurrency failure.
    """
    product = db.session.get(Product, product_id)
    if product is None:
        raise ProductServiceError('Product not found.')

    if expected_version is not None and product.version != int(expected_version):
        raise ProductServiceError(
            'This record has been modified by another user. '
            'Please reload and try again.'
        )

    name = _validate_name(name)
    _check_name_unique(name, exclude_id=product.id)

    product.name = name
    product.description = description or None
    product.version += 1

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ProductServiceError(
            f'A product named "{name}" already exists.'
        )
    return product


# ---------------------------------------------------------------------------
# Archive / Reactivate
# ---------------------------------------------------------------------------

def archive_product(product_id):
    """Soft-delete a product (REQ-026, REQ-046).

    Raises ``ProductServiceError`` if any linked active Repository would block
    the archive (REQ-026, REQ-049).
    """
    product = db.session.get(Product, product_id)
    if product is None:
        raise ProductServiceError('Product not found.')
    if product.is_archived:
        raise ProductServiceError('Product is already archived.')

    blocking = [r for r in product.repositories if not r.is_archived]
    if blocking:
        names = ', '.join(f'"{r.name}"' for r in blocking)
        raise ProductServiceError(
            f'Cannot archive this product because it is linked to active '
            f'{"repository" if len(blocking) == 1 else "repositories"}: '
            f'{names}. Please unlink or archive them first.'
        )

    product.is_archived = True
    product.is_active = False
    product.version += 1
    db.session.commit()
    return product


def reactivate_product(product_id):
    """Restore an archived product."""
    product = db.session.get(Product, product_id)
    if product is None:
        raise ProductServiceError('Product not found.')
    if not product.is_archived:
        raise ProductServiceError('Product is not archived.')

    product.is_archived = False
    product.is_active = True
    product.version += 1
    db.session.commit()
    return product


# ---------------------------------------------------------------------------
# Product-Repository Linking (REQ-025, REQ-054)
# ---------------------------------------------------------------------------

def link_repository(product_id, repo_id):
    """Add a product-repository link (REQ-025, REQ-054).

    Raises ``ProductServiceError`` if either entity does not exist or the
    link already exists.
    """
    product = db.session.get(Product, product_id)
    if product is None:
        raise ProductServiceError('Product not found.')

    repo = db.session.get(Repository, repo_id)
    if repo is None:
        raise ProductServiceError('Repository not found.')

    if repo in product.repositories:
        raise ProductServiceError(
            f'Repository "{repo.name}" is already linked to this product.'
        )

    product.repositories.append(repo)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ProductServiceError(
            f'Repository "{repo.name}" is already linked to this product.'
        )
    return product


def unlink_repository(product_id, repo_id):
    """Remove a product-repository link (REQ-025).

    Raises ``ProductServiceError`` if the link does not exist.
    """
    product = db.session.get(Product, product_id)
    if product is None:
        raise ProductServiceError('Product not found.')

    repo = db.session.get(Repository, repo_id)
    if repo is None:
        raise ProductServiceError('Repository not found.')

    if repo not in product.repositories:
        raise ProductServiceError(
            f'Repository "{repo.name}" is not linked to this product.'
        )

    product.repositories.remove(repo)
    db.session.commit()
    return product


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_name(name):
    name = name.strip() if name else ''
    if not name:
        raise ProductServiceError('Product name is required.')
    return name


def _check_name_unique(name, exclude_id):
    """Raise if name is already in use by any product (including archived)."""
    query = Product.query.filter(
        db.func.lower(Product.name) == name.lower()
    )
    if exclude_id is not None:
        query = query.filter(Product.id != exclude_id)
    if query.first() is not None:
        raise ProductServiceError(
            f'A product named "{name}" already exists.'
        )
