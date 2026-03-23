"""Product model (REQ-023, REQ-024, REQ-025)."""

from ..extensions import db
from . import BaseModel
from .repository import product_repository


class Product(BaseModel):
    """Product entity (REQ-023).

    Name is globally unique across active and archived products (REQ-024).
    Products have a many-to-many relationship with Repositories via the
    product_repository association table (REQ-025).
    """

    __tablename__ = 'products'

    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    repositories = db.relationship(
        'Repository',
        secondary=product_repository,
        lazy='select',
        backref=db.backref('products', lazy='select'),
    )

    def __repr__(self) -> str:
        return f'<Product {self.name}>'
