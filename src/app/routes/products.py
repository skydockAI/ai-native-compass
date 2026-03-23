"""Product management routes (REQ-023–026, REQ-053, REQ-054)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from ..authz import role_required
from ..services import product_service, repository_service
from ..services.product_service import ProductServiceError
from .forms import ProductCreateForm, ProductEditForm

products_bp = Blueprint('products', __name__, url_prefix='/products')


# ---------------------------------------------------------------------------
# Product list
# ---------------------------------------------------------------------------

@products_bp.route('/')
@login_required
def index():
    """Product list with active/archived filter (REQ-058)."""
    show_archived = request.args.get('archived', '0') == '1'
    products = product_service.get_products(include_archived=show_archived)
    ctx = dict(products=products, show_archived=show_archived)
    if request.headers.get('HX-Request'):
        return render_template('products/partials/product_list.html', **ctx)
    return render_template('products/list.html', **ctx)


# ---------------------------------------------------------------------------
# Product detail
# ---------------------------------------------------------------------------

@products_bp.route('/<int:product_id>')
@login_required
def detail(product_id):
    """Product detail page showing linked repositories."""
    product = product_service.get_product_by_id(product_id)
    if product is None:
        flash('Product not found.', 'danger')
        return redirect(url_for('products.index'))

    return render_template('products/detail.html', product=product)


# ---------------------------------------------------------------------------
# Create product (Admin + Editor)
# ---------------------------------------------------------------------------

@products_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'editor')
def create():
    """Display and process new-product form."""
    form = ProductCreateForm()

    if form.validate_on_submit():
        try:
            product = product_service.create_product(
                name=form.name.data,
                description=form.description.data,
            )
            flash('Product created successfully.', 'success')
            return redirect(url_for('products.detail', product_id=product.id))
        except ProductServiceError as exc:
            flash(str(exc), 'danger')

    return render_template('products/create.html', form=form)


# ---------------------------------------------------------------------------
# Edit product (Admin + Editor)
# ---------------------------------------------------------------------------

@products_bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'editor')
def edit(product_id):
    """Display and process edit-product form."""
    product = product_service.get_product_by_id(product_id)
    if product is None:
        flash('Product not found.', 'danger')
        return redirect(url_for('products.index'))

    form = ProductEditForm(obj=product)

    if request.method == 'GET':
        form.name.data = product.name
        form.description.data = product.description
        form.version.data = product.version

    if form.validate_on_submit():
        try:
            product_service.update_product(
                product_id=product_id,
                name=form.name.data,
                description=form.description.data,
                expected_version=int(form.version.data),
            )
            flash('Product updated successfully.', 'success')
            return redirect(url_for('products.detail', product_id=product_id))
        except ProductServiceError as exc:
            flash(str(exc), 'danger')

    active_repos = repository_service.get_repositories(include_archived=False)
    linked_repo_ids = {r.id for r in product.repositories}
    available_repos = [r for r in active_repos if r.id not in linked_repo_ids]

    return render_template('products/edit.html', form=form, product=product, available_repos=available_repos)


# ---------------------------------------------------------------------------
# Archive / Reactivate
# ---------------------------------------------------------------------------

@products_bp.route('/<int:product_id>/archive', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def archive(product_id):
    """Archive a product."""
    try:
        product_service.archive_product(product_id)
        flash('Product archived successfully.', 'success')
    except ProductServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('products.index'))


@products_bp.route('/<int:product_id>/reactivate', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def reactivate(product_id):
    """Reactivate an archived product."""
    try:
        product_service.reactivate_product(product_id)
        flash('Product reactivated successfully.', 'success')
    except ProductServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('products.index', archived='1'))


# ---------------------------------------------------------------------------
# Product-Repository Linking (HTMX endpoints)
# ---------------------------------------------------------------------------

@products_bp.route('/<int:product_id>/link-repo', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def link_repo(product_id):
    """Link a repository to a product (REQ-025, REQ-054)."""
    repo_id = request.form.get('repo_id', type=int)
    if not repo_id:
        flash('Please select a repository to link.', 'danger')
        return redirect(url_for('products.edit', product_id=product_id))

    try:
        product_service.link_repository(product_id, repo_id)
        flash('Repository linked successfully.', 'success')
    except ProductServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('products.edit', product_id=product_id))


@products_bp.route('/<int:product_id>/unlink-repo', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def unlink_repo(product_id):
    """Unlink a repository from a product (REQ-025)."""
    repo_id = request.form.get('repo_id', type=int)
    if not repo_id:
        flash('Repository not specified.', 'danger')
        return redirect(url_for('products.edit', product_id=product_id))

    try:
        product_service.unlink_repository(product_id, repo_id)
        flash('Repository unlinked successfully.', 'success')
    except ProductServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('products.edit', product_id=product_id))


# ---------------------------------------------------------------------------
# Repository-side product linking (called from repository edit page)
# ---------------------------------------------------------------------------

@products_bp.route('/link-to-repo', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def link_to_repo():
    """Link a product to a repository (from repository edit page)."""
    product_id = request.form.get('product_id', type=int)
    repo_id = request.form.get('repo_id', type=int)
    if not product_id or not repo_id:
        flash('Invalid product or repository.', 'danger')
        return redirect(url_for('repositories.edit', repo_id=repo_id) if repo_id
                        else url_for('repositories.index'))

    try:
        product_service.link_repository(product_id, repo_id)
        flash('Product linked successfully.', 'success')
    except ProductServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('repositories.edit', repo_id=repo_id))


@products_bp.route('/unlink-from-repo', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def unlink_from_repo():
    """Unlink a product from a repository (from repository edit page)."""
    product_id = request.form.get('product_id', type=int)
    repo_id = request.form.get('repo_id', type=int)
    if not product_id or not repo_id:
        flash('Invalid product or repository.', 'danger')
        return redirect(url_for('repositories.index'))

    try:
        product_service.unlink_repository(product_id, repo_id)
        flash('Product unlinked successfully.', 'success')
    except ProductServiceError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('repositories.edit', repo_id=repo_id))
