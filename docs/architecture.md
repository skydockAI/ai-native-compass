# AI Native Compass — Architecture

## 1. Architecture Overview

AI Native Compass (ANC) is a server-rendered web application for tracking AI Native Engineering adoption across products and code repositories. The architecture prioritizes simplicity, maintainability, and suitability for small internal teams (~20 users).

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Browser (Client)                   │
│   HTML pages rendered by Jinja2 + HTMX for interactivity│
└────────────────────────┬────────────────────────────────┘
                         │ HTTP (HTML + HTMX partial responses)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   Flask Application                      │
│                                                         │
│  ┌──────────┐  ┌───────────────────────────┐            │
│  │  Auth    │  │  Blueprints (Routes)      │            │
│  │  Module  │  │  - dashboard              │            │
│  │          │  │  - products               │            │
│  │ (swap-   │  │  - repositories           │            │
│  │  pable)  │  │  - templates              │            │
│  │          │  │  - teams                  │            │
│  └──────────┘  │  - users                  │            │
│                │  - audit                  │            │
│  ┌──────────┐  └───────────────────────────┘            │
│  │ Authz    │                                           │
│  │ (RBAC)   │  ┌───────────────────────────┐            │
│  └──────────┘  │ Services Layer            │            │
│                └───────────────────────────┘            │
│                                                         │
│                ┌───────────────────────────┐            │
│                │  Models (SQLAlchemy)      │            │
│                └───────────────────────────┘            │
└────────────────────────┬────────────────────────────────┘
                         │ SQL (via SQLAlchemy ORM)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   PostgreSQL Database                     │
│              (Docker container, host-mounted volume)      │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Architectural Style

**Server-side rendered monolith** using Flask with Jinja2 templates and HTMX for dynamic interactions. This avoids the complexity of a separate SPA framework while providing a modern, responsive dashboard experience suitable for the target user base.

### 1.3 Key Architectural Principles

- **Layered architecture**: Routes → Services → Models, with clear separation of concerns
- **Pluggable authentication**: Auth module is isolated so it can be replaced with SSO later (REQ-010)
- **Convention over configuration**: Standard Flask patterns, minimal custom abstractions
- **Soft delete everywhere**: All business entities use archive flags, never hard deletes (REQ-046)
- **Audit as a cross-cutting concern**: Audit logging is handled via explicit service calls, not embedded in route handlers

---

## 2. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Backend framework** | Python 3.12 + Flask 3.x | Specified in requirements. Mature, well-documented, simple |
| **ORM / Database** | SQLAlchemy 2.x + Alembic | Industry standard for Flask. Alembic for schema migrations |
| **Database** | PostgreSQL 16 | Specified in requirements. Excellent JSONB support for audit data |
| **Templating** | Jinja2 (built into Flask) | Server-side rendering, no separate frontend build step |
| **Frontend interactivity** | HTMX 2.x | Enables dynamic UI without a JavaScript framework. Partial page updates, form handling |
| **CSS framework** | Bootstrap 5 | Dashboard-ready components, responsive grid, minimal custom CSS needed |
| **Authentication** | Flask-Login + Werkzeug (password hashing) | Simple session management, secure password hashing |
| **Session storage** | Flask server-side sessions (filesystem or DB-backed) | Suitable for ~20 users; avoids Redis dependency |
| **Database migrations** | Alembic (via Flask-Migrate) | Version-controlled schema changes |
| **Form handling** | Flask-WTF | CSRF protection, form validation |
| **Containerization** | Docker + Docker Compose | Specified in requirements |
| **WSGI server** | Gunicorn | Production-grade, simple configuration |
| **Testing** | pytest + pytest-flask | Standard Flask testing stack |

### 2.1 Technology Decisions

**Why HTMX instead of React/Vue SPA:**
- Eliminates a separate frontend build pipeline
- No API serialization layer needed (Flask serves HTML directly)
- Sufficient for the dashboard-first UI with ~20 users
- Dramatically reduces codebase size and complexity
- Still allows dynamic interactions (partial page updates, inline editing, modal forms)

**Why SQLAlchemy 2.x:**
- Type-safe query building
- Declarative model definitions map cleanly to the entity model
- Alembic integration for migration management
- Mature ecosystem with Flask-SQLAlchemy extension

**Why Bootstrap 5 instead of Tailwind:**
- Pre-built dashboard components (cards, tables, navbars, modals)
- Faster development for standard CRUD + dashboard UIs
- No build step required (CDN or static file)
- Consistent, professional look with minimal effort

---

## 3. Application Structure

```
ai-native-compass/
├── docker-compose.yml
├── Dockerfile
├── .env                          # Admin seed emails, DB credentials, Flask secret
├── .data/                        # Host-mounted PostgreSQL data (gitignored)
├── requirements.txt
├── migrations/                   # Alembic migration scripts
│   └── versions/
├── app/
│   ├── __init__.py               # Flask app factory
│   ├── config.py                 # Configuration from environment
│   ├── extensions.py             # SQLAlchemy, Login Manager, Migrate init
│   │
│   ├── auth/                     # Authentication module (swappable)
│   │   ├── __init__.py
│   │   ├── local.py              # Local email/password authentication
│   │   └── routes.py             # Login/logout routes
│   │
│   ├── authz/                    # Authorization module
│   │   ├── __init__.py
│   │   └── decorators.py         # @role_required, @admin_required, etc.
│   │
│   ├── models/                   # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── team.py
│   │   ├── product.py
│   │   ├── repository.py
│   │   ├── template.py
│   │   ├── shared_attribute.py
│   │   └── audit_log.py
│   │
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── team_service.py
│   │   ├── product_service.py
│   │   ├── repository_service.py
│   │   ├── template_service.py
│   │   └── audit_service.py
│   │
│   ├── routes/                   # Flask Blueprints (route handlers)
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   ├── products.py
│   │   ├── repositories.py
│   │   ├── templates.py
│   │   ├── teams.py
│   │   ├── users.py
│   │   └── audit.py
│   │
│   ├── templates/                # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── products/
│   │   ├── repositories/
│   │   ├── templates_admin/
│   │   ├── teams/
│   │   ├── users/
│   │   ├── audit/
│   │   └── components/           # Reusable HTMX partials
│   │
│   ├── static/                   # CSS, JS, images
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   │
│   └── utils/                    # Shared utilities
│       ├── __init__.py
│       ├── seed.py               # Admin seeding logic
│       └── filters.py            # Jinja2 custom filters
│
└── tests/
    ├── conftest.py
    ├── test_auth/
    ├── test_models/
    ├── test_services/
    └── test_routes/
```

### 3.1 Layer Responsibilities

**Routes (Blueprints):** Handle HTTP requests, parse form data, call services, render templates. No business logic.

**Services:** Contain all business logic — validation, dependency checks, archive rules, template propagation. Services call models and return results to routes.

**Models:** SQLAlchemy ORM classes. Define schema, relationships, and simple data-level constraints. No business logic beyond column defaults and basic validation.

**Auth module:** Encapsulates authentication strategy. The `local.py` module handles email/password auth. A future `sso.py` module can replace it without touching authorization or business logic.

**Authz module:** Role-based access control via decorators. Applied at the route level. Independent from the auth module.

---

## 4. Data Model

### 4.1 Entity-Relationship Diagram

```
┌──────────────┐       ┌───────────────────┐       ┌──────────────────┐
│    User      │       │  Product          │       │    Team          │
│──────────────│       │───────────────────│       │──────────────────│
│ id (PK)      │       │ id (PK)           │       │ id (PK)          │
│ email (UQ)   │       │ name (UQ)         │       │ name (UQ)        │
│ full_name    │       │ description       │       │ description      │
│ password_hash│       │ is_active         │       │ is_active        │
│ role         │       │ is_archived       │       │ is_archived      │
│ is_active    │       │ created_at        │       │ created_at       │
│ is_archived  │       │ updated_at        │       │ updated_at       │
│ is_seeded    │       └─────────┬─────────┘       └────────┬─────────┘
│ created_at   │                 │                           │
│ updated_at   │                 │ M:N                       │ 1:N
└──────────────┘                 │                           │
                     ┌───────────┴──────────┐                │
                     │ product_repository   │                │
                     │ (association table)  │                │
                     │─────────────────────│                │
                     │ product_id (FK)      │                │
                     │ repository_id (FK)   │                │
                     └───────────┬──────────┘                │
                                 │                           │
                     ┌───────────┴───────────────────────────┴──┐
                     │           Repository                      │
                     │───────────────────────────────────────────│
                     │ id (PK)                                   │
                     │ name                                      │
                     │ url (UQ)                                  │
                     │ description                               │
                     │ team_id (FK → Team)                       │
                     │ template_id (FK → RepoTemplate)           │
                     │ is_active                                 │
                     │ is_archived                               │
                     │ created_at                                │
                     │ updated_at                                │
                     └───────────────────────┬───────────────────┘
                                             │ 1:N
                                             │
┌────────────────────────┐       ┌───────────┴───────────────────┐
│    RepoTemplate        │       │  RepositoryArtifactValue      │
│────────────────────────│       │───────────────────────────────│
│ id (PK)                │       │ id (PK)                       │
│ name (UQ)              │       │ repository_id (FK)            │
│ description            │       │ template_artifact_id (FK)     │
│ is_active              │──┐    │ value_text                    │
│ is_archived            │  │    │ value_number                  │
│ created_at             │  │    │ value_boolean                 │
│ updated_at             │  │    │ value_list_option_id (FK)     │
└───────────┬────────────┘  │    └───────────────────────────────┘
            │ 1:N           │
            │               │ 1:N (Template → Repository)
┌───────────┴────────────┐  │
│  TemplateArtifact      │  │
│────────────────────────│  │
│ id (PK)                │  │  ┌─────────────────────────────────┐
│ template_id (FK)       │  │  │  SharedAttributeDefinition      │
│ type                   │  │  │─────────────────────────────────│
│ name                   │  │  │ id (PK)                         │
│ description            │  │  │ name (UQ)                       │
│ value_type             │  │  │ is_default                      │
│ is_required            │  │  │ is_active                       │
│ display_order          │  │  │ created_at                      │
│ is_active              │  │  │ updated_at                      │
│ created_at             │  │  └──────────────┬──────────────────┘
│ updated_at             │  │                  │ 1:N
└───────────┬────────────┘  │                  │
            │ 1:N           │  ┌───────────────┴──────────────────┐
            │               │  │  RepositorySharedAttributeValue  │
┌───────────┴────────────┐  │  │──────────────────────────────────│
│ ArtifactListOption     │  │  │ id (PK)                          │
│────────────────────────│  │  │ repository_id (FK)               │
│ id (PK)                │  │  │ attribute_id (FK)                │
│ artifact_id (FK)       │  │  │ value (text)                     │
│ value                  │  │  └──────────────────────────────────┘
│ display_order          │  │
│ is_active              │  │
│ created_at             │  │
└────────────────────────┘  │
                            │
                    ┌───────┴─────────────────┐
                    │      AuditLog           │
                    │─────────────────────────│
                    │ id (PK)                 │
                    │ timestamp               │
                    │ user_id (FK, nullable)  │
                    │ entity_type             │
                    │ entity_id               │
                    │ action                  │
                    │ before_value (JSONB)    │
                    │ after_value (JSONB)     │
                    └─────────────────────────┘
```

### 4.2 Model Details

#### User
- `role` is an enum: `admin`, `editor`, `viewer` (REQ-011, REQ-012)
- `is_seeded` flag marks env-seeded admins that cannot be demoted or deleted (REQ-009)
- `password_hash` stores securely hashed password (REQ-003)

#### Repository ↔ Template Relationship
- `template_id` is set at creation time and is immutable (REQ-029)
- The foreign key constraint ensures referential integrity
- Template-derived artifact values are stored in `RepositoryArtifactValue` — one row per artifact per repository

#### Template Artifact Value Storage Strategy

Rather than storing all artifact values in a single JSONB column, ANC uses a **relational EAV (Entity-Attribute-Value) approach** with typed columns:

- `value_text` — for `Document`/`Skill`/`Agent` artifacts (Yes/No/N/A) and `Other:text` artifacts
- `value_number` — for `Other:number` artifacts
- `value_boolean` — for `Other:boolean` artifacts (nullable tri-state: True/False/N/A via NULL)
- `value_list_option_id` — FK to `ArtifactListOption` for `Other:list` artifacts

**Rationale:** This approach provides proper type safety, enables SQL-level filtering and aggregation (needed for dashboard and filtering features — REQ-057, REQ-058), and makes template change propagation straightforward (adding/removing artifacts maps directly to inserting/deleting rows).

#### Shared Attributes

Custom shared attributes (REQ-035) use a separate EAV pair:
- `SharedAttributeDefinition` — Admin-managed attribute definitions
- `RepositorySharedAttributeValue` — Per-repository text values

The four default shared attributes (Name, Team, URL, Description) are native columns on `Repository`, not EAV rows. The `is_default` flag on `SharedAttributeDefinition` protects the defaults from deletion (REQ-036).

#### Audit Log
- `before_value` and `after_value` use PostgreSQL JSONB to store flexible snapshots of entity state
- `user_id` is nullable to handle system-generated events (e.g., startup seeding)
- `entity_type` is a string enum (user, team, product, repository, template, session)
- `action` is a string enum (login, logout, create, update, archive, role_change, template_change)

### 4.3 Optimistic Locking

All mutable business entities (User, Team, Product, Repository, RepoTemplate, TemplateArtifact) include a `version` integer column that is incremented on every update. Edit forms include the current version as a hidden field. On save, the service layer checks that the version in the request matches the current database version. If a mismatch is detected (another user modified the record), the update is rejected with a conflict error message.

### 4.4 Indexes

Beyond primary keys and unique constraints, the following indexes improve query performance:

| Table | Column(s) | Rationale |
|-------|-----------|-----------|
| `repository` | `team_id` | Filter repositories by team |
| `repository` | `template_id` | Filter repositories by template |
| `repository` | `is_archived` | Exclude archived from default queries |
| `product_repository` | `(product_id, repository_id)` | Unique composite, fast lookups |
| `repository_artifact_value` | `(repository_id, template_artifact_id)` | Unique composite, fast artifact lookups |
| `template_artifact` | `template_id` | Load all artifacts for a template |
| `audit_log` | `timestamp` | Chronological listing |
| `audit_log` | `entity_type, entity_id` | Filter audit by entity |
| `audit_log` | `user_id` | Filter audit by user |

---

## 5. Authentication and Authorization

### 5.1 Authentication Architecture

Authentication is isolated in `app/auth/` to enable future SSO replacement (REQ-010).

```
app/auth/
├── __init__.py          # Exports authenticate_user(), current auth strategy
├── local.py             # Local email/password: verify_password(), hash_password()
└── routes.py            # /login, /logout endpoints
```

**Flow:**
1. User submits email + password to `/login`
2. `routes.py` calls `authenticate_user(email, password)` from the auth module
3. `local.py` looks up user by email, verifies password hash, checks `is_active` and `is_archived`
4. On success, Flask-Login creates a session; user is redirected to dashboard
5. On failure, generic error message is returned (REQ-001: no field-specific error)

**Session management:**
- Flask-Login manages user sessions via secure, signed cookies
- Session checks verify `is_active` and `is_archived` on every request (REQ-007)
- Flask's built-in `before_request` hook validates the session on each request

**Admin seeding (REQ-008):**
- On app startup, `app/utils/seed.py` reads `ADMIN_SEEDS` from `.env` (comma-separated `email:password` pairs)
- For each email not in the database, creates an admin user with `is_seeded=True` and the provided password (hashed)
- Seeded admins cannot be demoted or deleted (REQ-009), enforced in `user_service.py`

### 5.2 Authorization Architecture

Authorization is fully separate from authentication and implemented in `app/authz/`.

```python
# app/authz/decorators.py

@login_required           # Flask-Login: must be authenticated
@role_required('admin')   # Custom: must have admin role
@role_required('admin', 'editor')  # Custom: must have admin or editor role
```

**Enforcement points:**
- Route-level: decorators on every route handler
- Service-level: critical operations double-check role in service methods
- Template-level: Jinja2 templates conditionally render UI elements based on `current_user.role`

**Role permissions matrix:**

| Action | Admin | Editor | Viewer |
|--------|-------|--------|--------|
| Manage users | Yes | No | No |
| Manage repo templates | Yes | No | No |
| Manage shared attributes | Yes | No | No |
| View audit logs | Yes | No | No |
| Create/edit/archive products | Yes | Yes | No |
| Create/edit/archive repositories | Yes | Yes | No |
| Create/edit/archive teams | Yes | Yes | No |
| Edit artifact values | Yes | Yes | No |
| Change repo template assignment | No | No | No |
| View dashboard and data | Yes | Yes | Yes |

---

## 6. Key Application Flows

### 6.1 Repository Creation Flow

```
User (Admin/Editor)                Flask Route                    Service Layer                  Database
       │                               │                               │                            │
       │  GET /repositories/new        │                               │                            │
       │──────────────────────────────>│                               │                            │
       │                               │  get active templates         │                            │
       │                               │──────────────────────────────>│                            │
       │  Render template selector     │<──────────────────────────────│                            │
       │<──────────────────────────────│                               │                            │
       │                               │                               │                            │
       │  Select template (HTMX)      │                               │                            │
       │──────────────────────────────>│                               │                            │
       │                               │  get template artifacts       │                            │
       │                               │  get shared attributes        │                            │
       │                               │  get active teams             │                            │
       │                               │──────────────────────────────>│                            │
       │  Render full form (partial)   │<──────────────────────────────│                            │
       │<──────────────────────────────│                               │                            │
       │                               │                               │                            │
       │  POST /repositories          │                               │                            │
       │──────────────────────────────>│                               │                            │
       │                               │  create_repository(data)      │                            │
       │                               │──────────────────────────────>│  Validate URL uniqueness   │
       │                               │                               │─────────────────────────── >│
       │                               │                               │  Insert repository         │
       │                               │                               │─────────────────────────── >│
       │                               │                               │  Insert artifact values    │
       │                               │                               │─────────────────────────── >│
       │                               │                               │  Insert shared attr values │
       │                               │                               │─────────────────────────── >│
       │                               │                               │  Write audit log           │
       │                               │                               │─────────────────────────── >│
       │  Redirect to repo detail      │<──────────────────────────────│                            │
       │<──────────────────────────────│                               │                            │
```

### 6.2 Template Change Propagation Flow

When an Admin modifies a template's artifacts (REQ-042 through REQ-045):

**Adding an artifact:**
1. Admin adds artifact definition to template via UI
2. `template_service.add_artifact()` inserts new `TemplateArtifact` row
3. For all active repositories using this template, inserts a `RepositoryArtifactValue` row with NULL/empty value
4. Audit log records the template change

**Removing an artifact:**
1. Admin removes artifact from template via UI
2. `template_service.remove_artifact()` marks `TemplateArtifact.is_active = False`
3. Existing `RepositoryArtifactValue` rows remain in DB but are excluded from active UI queries (filtered by `template_artifact.is_active`)
4. Historical values remain accessible through audit log

**Renaming an artifact:**
1. Admin renames artifact name
2. `template_service.update_artifact()` updates the `TemplateArtifact.name`
3. All repository values remain attached via foreign key — no data migration needed

### 6.3 Archive Flow with Dependency Checking

```
Admin/Editor                       Service Layer                         Database
     │                                  │                                    │
     │  archive_team(team_id)           │                                    │
     │─────────────────────────────────>│                                    │
     │                                  │  Check: any active repos           │
     │                                  │  with this team_id?                │
     │                                  │───────────────────────────────────>│
     │                                  │<───────────────────────────────────│
     │                                  │                                    │
     │                     [If active repos exist]                           │
     │  Error: "Cannot archive,         │                                    │
     │   used by N active repos"        │                                    │
     │<─────────────────────────────────│                                    │
     │                                  │                                    │
     │                     [If no active repos]                              │
     │                                  │  Set is_archived = True            │
     │                                  │───────────────────────────────────>│
     │                                  │  Write audit log                   │
     │                                  │───────────────────────────────────>│
     │  Success                         │                                    │
     │<─────────────────────────────────│                                    │
```

---

## 7. UI Architecture

### 7.1 Rendering Strategy

**Server-side rendering with HTMX enhancement:**

- Base pages are fully rendered server-side via Jinja2
- HTMX handles dynamic interactions without full page reloads:
  - Template selection on repository create (loads form fields dynamically)
  - Inline editing of artifact values
  - Filtering and search on list pages
  - Modal dialogs for confirmations (archive, link/unlink)
  - Dashboard card updates

### 7.2 Template Structure

```
templates/
├── base.html                    # Master layout: navbar, sidebar, flash messages
├── components/
│   ├── pagination.html          # Reusable pagination partial
│   ├── filter_bar.html          # Reusable filter bar partial
│   ├── confirm_modal.html       # Archive/delete confirmation modal
│   ├── flash_messages.html      # Toast/alert notifications
│   └── summary_card.html        # Dashboard summary card component
├── auth/
│   └── login.html
├── dashboard/
│   └── index.html               # Summary cards + filtered overview
├── products/
│   ├── list.html
│   ├── detail.html
│   └── form.html                # Create/edit form
├── repositories/
│   ├── list.html
│   ├── detail.html
│   ├── form.html                # Create/edit with dynamic artifact fields
│   └── partials/
│       ├── artifact_fields.html # HTMX partial: loaded after template selection
│       └── product_links.html   # HTMX partial: manage product associations
├── templates_admin/             # Named to avoid conflict with Jinja2 templates dir
│   ├── list.html
│   ├── detail.html
│   └── form.html
├── teams/
│   ├── list.html
│   └── form.html
├── users/
│   ├── list.html
│   └── form.html
└── audit/
    └── list.html                # Filterable, searchable audit log
```

### 7.3 Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Navbar: Logo | App Name               User Menu | Logout   │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                  │
│ Sidebar  │  Page Content                                    │
│          │                                                  │
│ Dashboard│  ┌─────────────────────────────────────────────┐ │
│ Products │  │  Page Header + Breadcrumbs                  │ │
│ Repos    │  ├─────────────────────────────────────────────┤ │
│ Templates│  │  Filter Bar (HTMX-driven)                   │ │
│ Teams    │  ├─────────────────────────────────────────────┤ │
│ Users*   │  │  Content Area                               │ │
│ Audit*   │  │  (tables, forms, cards, detail views)       │ │
│          │  │                                             │ │
│ *Admin   │  │                                             │ │
│  only    │  ├─────────────────────────────────────────────┤ │
│          │  │  Pagination                                 │ │
│          │  └─────────────────────────────────────────────┘ │
└──────────┴──────────────────────────────────────────────────┘
```

- Sidebar navigation is role-aware: Admin-only items (Users, Audit) are hidden for Editor/Viewer
- Active page is highlighted in the sidebar

---

## 8. Audit Logging Design

### 8.1 Implementation Approach

Audit logging is implemented as a **service-level concern** using explicit calls in service methods. This provides better control over what gets logged and ensures before/after snapshots are captured accurately.

```python
# Example pattern in service methods:
def update_product(product_id, data, current_user):
    product = Product.query.get_or_404(product_id)
    before = product.to_audit_dict()

    # ... apply changes ...

    after = product.to_audit_dict()
    audit_service.log(
        user=current_user,
        entity_type='product',
        entity_id=product.id,
        action='update',
        before_value=before,
        after_value=after
    )
```

### 8.2 Audit Events Captured

| Event | Entity Type | Trigger |
|-------|-------------|---------|
| Login | session | Successful authentication |
| Logout | session | User logout |
| Create | user, team, product, repository, template | Entity creation |
| Update | user, team, product, repository, template | Field changes |
| Archive | user, team, product, repository, template | Soft delete |
| Role change | user | Role field modified |
| Template change | template | Artifact add/rename/remove affecting live repos |

### 8.3 Audit Query Patterns

The audit log UI (REQ-062) supports:
- Filter by entity type
- Filter by action
- Filter by user
- Filter by date range
- Free text search (across entity identifiers and JSONB values)
- Chronological ordering (newest first)

---

## 9. Deployment Architecture

### 9.1 Docker Compose Services

```yaml
# docker-compose.yml (illustrative)
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://anc:${DB_PASSWORD}@db:5432/anc
      - FLASK_SECRET_KEY=${FLASK_SECRET_KEY}
      - ADMIN_SEEDS=${ADMIN_SEEDS}
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    volumes:
      - ./.data/postgres:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=anc
      - POSTGRES_USER=anc
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U anc"]
      interval: 5s
      timeout: 5s
      retries: 5
```

### 9.2 Dockerfile

```dockerfile
# Dockerfile (illustrative)
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:create_app()"]
```

### 9.3 Persistence

- PostgreSQL data: `.data/postgres/` bind mount on host (REQ-065)
- No container-local storage for persistent data
- `.data/` directory is gitignored

### 9.4 Startup Sequence

1. Docker Compose starts PostgreSQL, waits for healthcheck
2. Flask application starts
3. `create_app()` runs:
   a. Loads config from environment
   b. Initializes extensions (SQLAlchemy, Flask-Login, Flask-Migrate)
   c. Registers blueprints
   d. Runs database migrations (Alembic `upgrade head`)
   e. Executes admin seeding (`seed.py`) — creates any missing seeded admins
4. Gunicorn serves the application

---

## 10. Security Considerations

### 10.1 Authentication Security
- Passwords hashed with `werkzeug.security.generate_password_hash` (pbkdf2 by default; configurable for bcrypt) (REQ-003)
- Minimum password length of 8 characters enforced on all password operations
- Login errors do not reveal whether email or password was incorrect (REQ-001)
- Sessions use Flask's signed cookies with `FLASK_SECRET_KEY`
- No session timeout in v1; sessions persist until logout or user deactivation
- Session validated on every request; archived/inactive users denied immediately (REQ-007)

### 10.2 Authorization Security
- All routes enforce role checks server-side via decorators (REQ-068)
- UI element visibility is a convenience — authorization is always enforced at the route/service level
- Seeded admin protection enforced in service layer, not just UI (REQ-009)

### 10.3 General Security
- CSRF protection via Flask-WTF on all forms
- SQL injection prevented by SQLAlchemy parameterized queries
- XSS prevented by Jinja2 auto-escaping (enabled by default)
- `SECRET_KEY` and `DB_PASSWORD` stored in `.env`, never committed to git

---

## 11. Database Migration Strategy

### 11.1 Approach
- Alembic (via Flask-Migrate) manages all schema changes
- Migrations are version-controlled in `migrations/versions/`
- Auto-migration on app startup (`flask db upgrade` in entrypoint)

### 11.2 Migration Workflow
1. Modify SQLAlchemy model
2. Generate migration: `flask db migrate -m "description"`
3. Review generated migration script
4. Apply: `flask db upgrade`
5. Commit migration file to git

---

## 12. Testing Strategy

### 12.1 Test Layers

| Layer | Scope | Tools |
|-------|-------|-------|
| **Unit tests** | Service methods, model logic, utility functions | pytest |
| **Integration tests** | Route handlers with database | pytest-flask, test PostgreSQL |
| **End-to-end tests** | Full user flows via browser | Optional: Playwright (future) |

### 12.2 Test Database
- Tests use a separate PostgreSQL database (or SQLite for fast unit tests)
- Each test runs in a transaction that is rolled back after completion
- Fixtures provide common test data (users with each role, sample templates, etc.)

---

## 13. Assumptions

1. **No API layer needed in v1.** All interaction is through the server-rendered UI. If a REST API is needed later, Flask Blueprints can expose JSON endpoints alongside HTML routes.

2. **HTMX is sufficient for all v1 interactivity.** The requirements describe standard CRUD workflows and dashboard views that do not require complex client-side state management.

3. **~20 concurrent users does not require caching.** No Redis or Memcached is included. Flask server-side sessions and direct database queries are sufficient.

4. **Admin seeding credentials are provided via `.env`.** Each seeded admin has their email and initial password configured in the `.env` file. A `.env.sample` is provided as a template.

5. **Alembic migrations run automatically on startup.** This is acceptable for a small internal deployment. For larger teams, migrations might be run manually as a separate step.

6. **Bootstrap 5 CDN or bundled static files.** No frontend build pipeline is required. HTMX and Bootstrap are included as static files or CDN references.

7. **File-based or database-backed sessions (not Redis).** Flask's default session handling is sufficient for ~20 users.

---

## 14. Resolved Design Decisions

The following questions were raised during architecture design and have been resolved:

1. **Password policy:** Minimum password length is **8 characters**. Enforced on all password creation and change operations (user creation, self-service change, admin reset).

2. **Session timeout:** **No session timeout** for v1. Sessions persist until explicit logout or user archive/deactivation.

3. **Concurrent template editing:** **Optimistic locking** is supported. Template and other entity edit forms include a version check to detect concurrent modifications and alert the user rather than silently overwriting.

4. **Audit log retention:** **No archival strategy** for v1. Audit logs are preserved permanently per REQ-048 with no practical size limit.

5. **Admin seeding password delivery:** Seeded admin **email and initial password are both provided via the `.env` file**. Each seeded admin is configured as a pair (email + password). A `.env.sample` file is provided as a reference template.

6. **Repository archive vs. Product-Repository link removal:** **Manual unlinking is required.** Users must explicitly remove Product-Repository links before archiving a Repository that is linked to active Products. The UI displays the blocking dependencies but does not auto-remove them.

---

## 15. Requirements Traceability

| Architecture Area | Key Requirements Covered |
|-------------------|--------------------------|
| Authentication module | REQ-001, REQ-002, REQ-003, REQ-004, REQ-007, REQ-008, REQ-009, REQ-010 |
| Authorization (RBAC) | REQ-011, REQ-012, REQ-013, REQ-014, REQ-015 |
| User entity & management | REQ-005, REQ-006, REQ-016, REQ-017, REQ-018 |
| Team entity | REQ-019, REQ-020, REQ-021, REQ-022 |
| Product entity | REQ-023, REQ-024, REQ-025, REQ-026 |
| Repository entity | REQ-027, REQ-028, REQ-029, REQ-030 |
| Template entity & artifacts | REQ-031, REQ-032, REQ-033, REQ-037, REQ-038, REQ-039, REQ-040, REQ-041 |
| Shared attributes | REQ-034, REQ-035, REQ-036 |
| Template propagation | REQ-042, REQ-043, REQ-044, REQ-045 |
| Archive behavior | REQ-046, REQ-047, REQ-048, REQ-049 |
| Repository workflows | REQ-050, REQ-051, REQ-052 |
| Product management | REQ-053, REQ-054 |
| Dashboard & UI | REQ-055, REQ-056, REQ-057, REQ-058 |
| Audit logging | REQ-059, REQ-060, REQ-061, REQ-062 |
| Deployment | REQ-063, REQ-064, REQ-065 |
| Non-functional | REQ-066, REQ-067, REQ-068, REQ-069 |
