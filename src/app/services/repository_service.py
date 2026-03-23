"""Repository management business logic (REQ-021, REQ-027–030, REQ-050, REQ-051)."""

from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models.repository import Repository, RepositoryArtifactValue, product_repository
from ..models.shared_attribute import RepositorySharedAttributeValue
from ..models.template import ArtifactType, ArtifactValueType


class RepositoryServiceError(Exception):
    """Raised when a repository operation fails with a user-facing message."""


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def get_repositories(include_archived=False, product_id=None, team_id=None, template_id=None):
    """Return repositories ordered by name with optional filters (REQ-027, REQ-058).

    Filters are applied additively (AND logic):
    - include_archived: include archived repositories
    - product_id: only repos linked to this product via product_repository table
    - team_id: only repos belonging to this team
    - template_id: only repos using this template
    """
    query = Repository.query.order_by(Repository.name)
    if not include_archived:
        query = query.filter_by(is_archived=False)
    if team_id:
        query = query.filter(Repository.team_id == team_id)
    if template_id:
        query = query.filter(Repository.template_id == template_id)
    if product_id:
        query = query.join(
            product_repository,
            Repository.id == product_repository.c.repository_id,
        ).filter(product_repository.c.product_id == product_id)
    return query.all()


def get_repository_by_id(repo_id):
    """Return a single Repository by primary key or ``None``."""
    return db.session.get(Repository, repo_id)


def get_artifact_values_map(repo_id):
    """Return dict mapping template_artifact_id → RepositoryArtifactValue for a repository."""
    values = RepositoryArtifactValue.query.filter_by(repository_id=repo_id).all()
    return {v.template_artifact_id: v for v in values}


def get_shared_attr_values_map(repo_id):
    """Return dict mapping attribute_id → RepositorySharedAttributeValue for a repository."""
    values = RepositorySharedAttributeValue.query.filter_by(repository_id=repo_id).all()
    return {v.attribute_id: v for v in values}


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_repository(name, url, team_id, template_id, description=None,
                      artifact_values=None, shared_attr_values=None):
    """Create a new repository using the template-first workflow (REQ-050).

    ``artifact_values`` is a dict mapping template_artifact_id (int) → raw form value (str).
    ``shared_attr_values`` is a dict mapping attribute_id (int) → str value.

    On success inserts:
    - One Repository row
    - One RepositoryArtifactValue row per active artifact in the template
    - One RepositorySharedAttributeValue row per active custom shared attribute

    Raises ``RepositoryServiceError`` on any validation failure.
    """
    artifact_values = artifact_values or {}
    shared_attr_values = shared_attr_values or {}

    name, url = _validate_name(name), _validate_url(url)
    team = _require_active_team(team_id)
    template = _require_active_template(template_id)

    _check_url_unique(url, exclude_id=None)

    # Gather active artifacts and validate required ones
    active_artifacts = [a for a in template.artifacts if a.is_active]
    _validate_required_artifacts(active_artifacts, artifact_values)

    repo = Repository(
        name=name,
        url=url,
        description=description or None,
        team_id=team.id,
        template_id=template.id,
    )
    try:
        db.session.add(repo)
        db.session.flush()  # get repo.id before inserting values
    except IntegrityError:
        db.session.rollback()
        raise RepositoryServiceError(
            f'A repository with URL "{url}" already exists.'
        )

    # Insert artifact value rows for all active artifacts
    for artifact in active_artifacts:
        raw = artifact_values.get(artifact.id, '')
        av = RepositoryArtifactValue(
            repository_id=repo.id,
            template_artifact_id=artifact.id,
        )
        _apply_artifact_value(av, artifact, raw)
        db.session.add(av)

    # Insert shared attribute value rows for all active custom attributes
    for attr_id_str, value in shared_attr_values.items():
        try:
            attr_id = int(attr_id_str)
        except (TypeError, ValueError):
            continue
        sav = RepositorySharedAttributeValue(
            repository_id=repo.id,
            attribute_id=attr_id,
            value=value.strip() if value else None,
        )
        db.session.add(sav)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise RepositoryServiceError(
            f'A repository with URL "{url}" already exists.'
        )
    return repo


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def update_repository(repo_id, name, url, team_id, description=None,
                      artifact_values=None, shared_attr_values=None,
                      expected_version=None):
    """Update an existing repository with optimistic locking (REQ-051).

    template_id is intentionally not a parameter — it is immutable (REQ-029).
    ``artifact_values`` dict maps template_artifact_id (int) → raw form value (str).
    ``shared_attr_values`` dict maps attribute_id (int) → str value.

    Raises ``RepositoryServiceError`` on validation or concurrency failure.
    """
    artifact_values = artifact_values or {}
    shared_attr_values = shared_attr_values or {}

    repo = db.session.get(Repository, repo_id)
    if repo is None:
        raise RepositoryServiceError('Repository not found.')

    if expected_version is not None and repo.version != int(expected_version):
        raise RepositoryServiceError(
            'This record has been modified by another user. '
            'Please reload and try again.'
        )

    name, url = _validate_name(name), _validate_url(url)
    team = _require_active_team(team_id)
    _check_url_unique(url, exclude_id=repo.id)

    template = repo.template
    active_artifacts = [a for a in template.artifacts if a.is_active]
    _validate_required_artifacts(active_artifacts, artifact_values)

    repo.name = name
    repo.url = url
    repo.description = description or None
    repo.team_id = team.id
    repo.version += 1

    # Upsert artifact values
    existing_avs = {av.template_artifact_id: av for av in repo.artifact_values}
    for artifact in active_artifacts:
        raw = artifact_values.get(artifact.id, '')
        if artifact.id in existing_avs:
            _apply_artifact_value(existing_avs[artifact.id], artifact, raw)
        else:
            av = RepositoryArtifactValue(
                repository_id=repo.id,
                template_artifact_id=artifact.id,
            )
            _apply_artifact_value(av, artifact, raw)
            db.session.add(av)

    # Upsert shared attribute values
    existing_savs = {sav.attribute_id: sav for sav in repo.shared_attr_values}
    for attr_id_str, value in shared_attr_values.items():
        try:
            attr_id = int(attr_id_str)
        except (TypeError, ValueError):
            continue
        clean_val = value.strip() if value else None
        if attr_id in existing_savs:
            existing_savs[attr_id].value = clean_val
        else:
            sav = RepositorySharedAttributeValue(
                repository_id=repo.id,
                attribute_id=attr_id,
                value=clean_val,
            )
            db.session.add(sav)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise RepositoryServiceError(
            f'A repository with URL "{url}" already exists.'
        )
    return repo


# ---------------------------------------------------------------------------
# Duplicate
# ---------------------------------------------------------------------------

def duplicate_repository(source_repo_id, name, url):
    """Duplicate a repository with a new name and URL (REQ-052).

    Copies all ``RepositoryArtifactValue`` and ``RepositorySharedAttributeValue`` rows
    from the source repository to the new one.  The new repository uses the same
    ``team_id`` and ``template_id`` as the source.

    Product links (``product_repository``) are NOT copied.

    Raises ``RepositoryServiceError`` on any validation failure.
    """
    source = db.session.get(Repository, source_repo_id)
    if source is None:
        raise RepositoryServiceError('Source repository not found.')

    name = _validate_name(name)
    url = _validate_url(url)
    _check_url_unique(url, exclude_id=None)

    dup = Repository(
        name=name,
        url=url,
        description=source.description,
        team_id=source.team_id,
        template_id=source.template_id,
    )
    try:
        db.session.add(dup)
        db.session.flush()  # get dup.id
    except Exception:
        db.session.rollback()
        raise RepositoryServiceError(f'A repository with URL "{url}" already exists.')

    # Copy artifact values
    for av in source.artifact_values:
        new_av = RepositoryArtifactValue(
            repository_id=dup.id,
            template_artifact_id=av.template_artifact_id,
            value_text=av.value_text,
            value_number=av.value_number,
            value_boolean=av.value_boolean,
            value_list_option_id=av.value_list_option_id,
        )
        db.session.add(new_av)

    # Copy shared attribute values
    for sav in source.shared_attr_values:
        new_sav = RepositorySharedAttributeValue(
            repository_id=dup.id,
            attribute_id=sav.attribute_id,
            value=sav.value,
        )
        db.session.add(new_sav)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise RepositoryServiceError(f'A repository with URL "{url}" already exists.')

    return dup


# ---------------------------------------------------------------------------
# Archive / Reactivate
# ---------------------------------------------------------------------------

def archive_repository(repo_id):
    """Soft-delete a repository (REQ-046, REQ-049).

    Raises ``RepositoryServiceError`` if any linked active Product would block
    the archive (REQ-049).
    """
    repo = db.session.get(Repository, repo_id)
    if repo is None:
        raise RepositoryServiceError('Repository not found.')
    if repo.is_archived:
        raise RepositoryServiceError('Repository is already archived.')

    blocking = [p for p in repo.products if not p.is_archived]
    if blocking:
        names = ', '.join(f'"{p.name}"' for p in blocking)
        raise RepositoryServiceError(
            f'Cannot archive this repository because it is linked to active '
            f'{"product" if len(blocking) == 1 else "products"}: '
            f'{names}. Please unlink or archive them first.'
        )

    repo.is_archived = True
    repo.is_active = False
    repo.version += 1
    db.session.commit()
    return repo


def reactivate_repository(repo_id):
    """Restore an archived repository."""
    repo = db.session.get(Repository, repo_id)
    if repo is None:
        raise RepositoryServiceError('Repository not found.')
    if not repo.is_archived:
        raise RepositoryServiceError('Repository is not archived.')

    repo.is_archived = False
    repo.is_active = True
    repo.version += 1
    db.session.commit()
    return repo


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_name(name):
    name = name.strip() if name else ''
    if not name:
        raise RepositoryServiceError('Repository name is required.')
    return name


def _validate_url(url):
    url = url.strip() if url else ''
    if not url:
        raise RepositoryServiceError('Repository URL is required.')
    return url


def _require_active_team(team_id):
    if not team_id:
        raise RepositoryServiceError('Team is required.')
    from ..models.team import Team
    team = db.session.get(Team, int(team_id))
    if team is None:
        raise RepositoryServiceError('Team not found.')
    if team.is_archived:
        raise RepositoryServiceError(
            f'Team "{team.name}" is archived. Only active teams can be assigned.'
        )
    return team


def _require_active_template(template_id):
    if not template_id:
        raise RepositoryServiceError('Template is required.')
    from ..models.template import RepoTemplate
    template = db.session.get(RepoTemplate, int(template_id))
    if template is None:
        raise RepositoryServiceError('Template not found.')
    if template.is_archived:
        raise RepositoryServiceError(
            f'Template "{template.name}" is archived. Only active templates can be selected.'
        )
    return template


def _check_url_unique(url, exclude_id):
    """Raise if URL is already in use by any repository (including archived) (REQ-028)."""
    query = Repository.query.filter(
        db.func.lower(Repository.url) == url.lower()
    )
    if exclude_id is not None:
        query = query.filter(Repository.id != exclude_id)
    if query.first() is not None:
        raise RepositoryServiceError(
            f'A repository with URL "{url}" already exists. '
            'Repository URLs must be unique across active and archived repositories.'
        )


def _validate_required_artifacts(active_artifacts, artifact_values):
    """Raise if any required Other-type artifact has no value."""
    for artifact in active_artifacts:
        if artifact.type == ArtifactType.other and artifact.is_required:
            raw = artifact_values.get(artifact.id, '')
            if not str(raw).strip():
                raise RepositoryServiceError(
                    f'Artifact "{artifact.name}" is required.'
                )


def _apply_artifact_value(av, artifact, raw):
    """Set the correct typed column on *av* based on *artifact* type and *raw* value."""
    # Reset all typed columns first
    av.value_text = None
    av.value_number = None
    av.value_boolean = None
    av.value_list_option_id = None

    if artifact.type in (ArtifactType.document, ArtifactType.skill, ArtifactType.agent):
        # Yes / No / N/A stored as text
        val = str(raw).strip() if raw else ''
        av.value_text = val if val in ('Yes', 'No', 'N/A') else None

    elif artifact.type == ArtifactType.other:
        if artifact.value_type == ArtifactValueType.text:
            av.value_text = str(raw).strip() if raw else None
            if av.value_text == '':
                av.value_text = None

        elif artifact.value_type == ArtifactValueType.number:
            try:
                av.value_number = float(raw) if str(raw).strip() else None
            except (TypeError, ValueError):
                av.value_number = None

        elif artifact.value_type == ArtifactValueType.boolean:
            val = str(raw).strip().lower() if raw else ''
            if val == 'true':
                av.value_boolean = True
            elif val == 'false':
                av.value_boolean = False
            else:
                av.value_boolean = None  # N/A

        elif artifact.value_type == ArtifactValueType.list:
            try:
                opt_id = int(raw) if str(raw).strip() else None
                av.value_list_option_id = opt_id
            except (TypeError, ValueError):
                av.value_list_option_id = None
