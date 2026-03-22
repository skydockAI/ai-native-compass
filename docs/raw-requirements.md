# AI Native Compass (ANC)
## Requirements Document

## 1. Overview

### 1.1 Purpose
AI Native Compass (ANC) is a web application used to track AI Native Engineering adoption across Products and Code Repositories.

The system allows authorized users to manage Products, Repositories, Repo Templates, Users, Teams, and template-driven adoption data in a centralized way. It also provides audit logging for key system activities.

### 1.2 Goals
The goals of ANC are:
- Track AI Native Engineering adoption at the repository level
- Link repositories to one or more products
- Standardize repository tracking using reusable Repo Templates
- Support role-based access control
- Maintain an audit trail of important activities
- Provide a dashboard-first UI for visibility and management
- Support simple authentication for initial development, with future migration to SSO

### 1.3 Technology Direction
- Application type: Web application
- Backend framework: Python Flask
- Database: PostgreSQL
- Deployment: Docker Compose
- Persistent storage: Host-mounted storage under `.data` in the project directory

---

## 2. Authentication Approach

For initial development and quick testing, the system will use a simple local authentication mechanism based on email and password.

Characteristics:
- Admin creates users in the database first
- Only users existing in the database can log in
- One role per user
- At least one Admin user must be seeded from `.env` if missing

Support for SSO will be added in the future.

---

## 3. User Roles

The system supports exactly one role per user.

### 3.1 Admin
Admin has full access to the system.

Permissions include:
- Manage users
- Manage Products
- Manage Repositories
- Manage Repo Templates
- Manage Repo shared attributes
- Manage Teams
- View audit logs
- Perform all actions available to Editors and Viewers

### 3.2 Editor
Editor can manage operational tracking data but cannot manage system configuration.

Permissions include:
- Create, update, archive Products
- Create, update, archive Repositories
- Create, update, archive Teams
- Edit template-derived values for Repositories
- Duplicate Repositories
- View dashboard and data pages

Restrictions:
- Cannot manage users
- Cannot manage Repo Templates
- Cannot change a Repository’s assigned template
- Cannot view audit logs

### 3.3 Viewer
Viewer has read-only access.

Permissions include:
- View dashboard
- View Products
- View Repositories
- View template-derived data

Restrictions:
- Cannot create, edit, delete, or archive any entity
- Cannot view audit logs

---

## 4. Authentication and Authorization

### 4.1 Initial Authentication
The initial version will use a simple built-in authentication system.

Requirements:
- User logs in using email and password
- User account must already exist in the database
- Only active users may log in
- Password must be hashed and stored securely
- User can change their own password after login (need to provide current password and new password)
- If a user is removed or archived, access must be denied on the next request
- Session-based authentication is acceptable for Flask

### 4.2 Admin Seeding
- A list of Admin email addresses is stored in `.env`
- On application startup, the system checks whether each configured Admin exists in the database
- If an Admin does not exist, the system creates the Admin user automatically
- Admin users created from `.env` cannot be demoted or deleted by another Admin
- Admin can set new password for users

### 4.3 Future SSO Integration
The system must be designed so local authentication can later be replaced or extended with SSO.

Future requirements:
- Match authenticated email exactly with an active user in the database
- Preserve the same role model and authorization logic already implemented in the application

---

## 5. Core Entities

### 5.1 User
A User represents a person allowed to access the system.

Fields:
- Email
- Full name
- Role
- Active status
- Created timestamp
- Updated timestamp
- Archived status

Rules:
- Email must be unique
- One user can have only one role
- User must be created by Admin before login
- Archived users cannot log in

### 5.2 Team
A Team is a managed list value used by Repositories.

Fields:
- Name
- Description
- Active status
- Created timestamp
- Updated timestamp
- Archived status

Rules:
- Team name must be unique
- One Repository belongs to exactly one Team
- Team is required for every Repository
- Team cannot be archived if used by an active Repository

### 5.3 Product
A Product is a business-level entity that can be linked to one or more Repositories.

Fields:
- Name
- Description
- Active status
- Created timestamp
- Updated timestamp
- Archived status

Rules:
- Product name should be unique
- Products are independent of Repositories
- Product can not be archived if linked to an active Repository

### 5.4 Repository
A Repository is a global shared entity representing a code repository.

Fields:
- Name
- Team
- URL
- Description
- Template
- Additional shared attributes
- Template-derived values
- Active status
- Created timestamp
- Updated timestamp
- Archived status

Rules:
- Repository URL must be unique
- Repository can exist without being linked to any Product
- One Repository can belong to multiple Products
- Template-derived data is shared consistently across all linked Products
- Each Repository uses exactly one Template
- Template cannot be changed after Repository creation

### 5.5 Product-Repository Relationship
Products and Repositories have a many-to-many relationship.

Rules:
- One Product can link to many Repositories
- One Repository can link to many Products
- Repository adoption data is stored once and shared across all linked Products
- Product can not be archived if linked to an active Repository
- Removing a Repository removes only the relationship links, not audit history

### 5.6 Repo Template
A Repo Template defines the structure used by Repositories assigned to that template.

Fields:
- Name
- Description
- Artifacts
- Active status
- Created timestamp
- Updated timestamp
- Archived status

Rules:
- Template name must be unique
- A Repository must select a Template when created
- Template cannot be changed after Repository creation
- Template cannot be archived if used by active Repositories

---

## 6. Repo Template Structure

Each Repo Template defines a flat list of artifacts alongside a set of shared Repository attributes.

### 6.1 Shared Repository Attributes
These are fields that exist across all templates.

Default shared attributes:
- Name
- Team
- URL
- Description

Rules:
- These fields are mandatory for every Repository
- Admin can add more shared attributes
- Shared attributes are text fields only
- Shared attributes are used for data entry, filtering, and reporting
- Admin can add shared attributes, but cannot remove or rename the default shared attributes

### 6.2 Template Artifacts
Each artifact in a Template defines one item that Repositories using that template are expected to have.

Each artifact contains:
- **Type** (required): `Document`, `Skill`, `Agent`, or `Other`
- **Name** (required): text
- **Value** (required):
  - For `Document`, `Skill` and `Agent`: the allowed values per Repository are `Yes`, `No`, or `N/A`
  - For `Other`: specifies the value type — `text`, `number`, `boolean`, or `list`
- **Description** (optional): text

Rules:
- Artifacts are displayed as a single unified list on Repository detail and edit pages
- Admin manages artifact definitions as part of the Template
- Editors can update artifact values for Repositories using the Template
- For `Document`, `Skill` and `Agent` artifacts, each Repository stores one of: Yes, No, N/A
- For `Other` artifacts with value type `text`, the field supports multiline text
- For `Other` artifacts with value type `number`, number fields do not require min/max validation in v1
- For `Other` artifacts with value type `boolean`, the allowed values are True, False, or N/A
- For `Other` artifacts with value type `list`, the field is single-select only with Admin-defined options
- Admin can mark an `Other` artifact as required
- A list option that is currently used by an active Repository cannot be deleted, but may be deactivated

---

## 7. Template Change Propagation

Template changes must be reflected in all active Repositories using that Template.

Rules:
- If a new artifact is added to a Template, it appears automatically in all linked Repositories with empty or null value
- If an artifact is renamed, existing Repository values remain attached to that artifact
- If an artifact is removed from a Template, it disappears from active Repository UI
- Removed values remain available only through audit history, not active UI
- List options for Other-type artifacts may be edited
- A list option that is currently used by an active Repository cannot be deleted, but may be deactivated

---

## 8. CRUD and Archive Behavior

### 8.1 General Rules
Business entities use soft delete through archive behavior.

Applies to:
- Users
- Teams
- Products
- Repositories
- Repo Templates

Rules:
- Archived entities are not shown in normal active UI views
- Archived entities remain in history and audit logs
- Audit history is preserved permanently unless future retention rules are added

### 8.2 Dependency Rules
Archiving may be blocked when active dependencies exist.

Rules:
- Team cannot be archived if used by an active Repository
- Template cannot be archived if used by an active Repository
- Repository cannot be archived while linked to active Products, unless those links are removed first
- Product may be archived without archiving or removing linked active Repositories
- User may be archived even if audit history exists

When archive is blocked:
- The UI must show the dependency reason clearly

---

## 9. Repository Creation and Editing Workflow

### 9.1 Create Repository
Repository creation flow:
1. User opens create Repository page
2. User selects Template first
3. System displays shared fields and template artifacts
4. User completes required fields
5. User saves Repository
6. System validates data and creates the record

Rules:
- Repository URL must be unique
- Team is required
- Template is required
- Template cannot be changed later

### 9.2 Edit Repository
Editors and Admins may:
- Update shared Repository values
- Update artifact values
- Update Product links

They may not:
- Change the assigned Template

### 9.3 Duplicate Repository
Editors and Admins can duplicate an existing Repository.

Rules:
- Duplicate copies all shared and template-derived values
- Duplicate does not copy Product links by default
- User must enter a new unique Repository URL before save

---

## 10. Product Management

Rules:
- Products can be created independently
- Repositories can be created independently
- Products and Repositories can be linked later
- Product editing occurs on separate pages
- Product fields are fixed in v1:
  - Name
  - Description

---

## 11. User Management

Admin can manage non-admin users.

Supported actions:
- Create user
- Edit user
- Archive user
- Assign role
- Reactivate user if supported in implementation

Rules:
- Only Admin can manage users
- Non-admin users must be explicitly created before first login
- Admin users from `.env` must exist in database
- Seeded Admin user from `.env` cannot be deleted or demoted

---

## 12. Dashboard and UI

### 12.1 UI Style
The application should be dashboard-first rather than admin-console-first.

### 12.2 Core UI Areas
The v1 UI should include:
- Login page
- Dashboard
- Products list and detail pages
- Repositories list and detail pages
- Repository create/edit pages
- Repo Templates list and detail pages
- User management pages
- Team management pages
- Audit log page

### 12.3 Dashboard v1
The homepage dashboard should include:
- Summary cards
  - Total active Products
  - Total active Teams
  - Total active Repositories
  - Total active Templates
  - Total active Users
- Basic filtering widgets where practical

### 12.4 Search and Filtering
v1 requirements:
- Filtering by Product
- Filtering by Team
- Filtering by Template
- Filtering by status where applicable

Later enhancements:
- Full search
- CSV export
- Excel export
- Advanced charts and analytics

---

## 13. Audit Logging

The system must maintain an audit log for important actions.

### 13.1 Logged Events
The audit log must include:
- Login
- Logout
- Create
- Update
- Archive
- Role changes
- Template changes affecting live Repositories

### 13.2 Audit Data
Each log entry should store:
- Timestamp
- User
- Entity type
- Entity identifier
- Action
- Before value
- After value

### 13.3 Access
- Only Admin can view audit logs

### 13.4 Audit Log UI
The audit log UI must support:
- Filtering
- Search
- View-only access

Audit logs do not support restore in v1.

---

## 14. Data Storage and Deployment

### 14.1 Database
- PostgreSQL is the system of record
- Database runs in Docker Compose

### 14.2 Persistence
- Persistent data must be stored on the host machine
- Docker volumes or bind mounts must map to `.data` under the project folder
- Data must not depend on container-local storage

### 14.3 Deployment Model
- Application runs as containerized service(s) with Docker Compose
- Suitable for small internal team usage
- Expected concurrent usage is low to moderate, up to about 20 users

---

## 15. Out of Scope for v1

The following are explicitly out of scope for the initial version:
- SSO
- File uploads
- Email notifications
- GitHub integration
- Azure DevOps integration
- Jira integration
- Automatic metadata extraction from Repository URL
- Advanced analytics and progress scoring
- Export to CSV or Excel
- Bulk import
- Bulk update actions
- Clone Template feature
- Template versioning
- Attachments or evidence files

---

## 16. Non-Functional Requirements

### 16.1 Simplicity
The solution should prioritize simplicity and maintainability for internal use.

### 16.2 Usability
- UI should be clear, modern, and business-friendly
- Data entry should be straightforward for Admin and Editor users
- Dashboard should make key information visible quickly

### 16.3 Security
For v1:
- Passwords must be stored securely using hashing
- Session handling must follow standard Flask security practices
- Authorization must be enforced server-side on every request

For later:
- Authentication must be replaceable or extendable to SSO

### 16.4 Data Integrity
- Unique constraints must be enforced where defined
- Dependency rules must be enforced consistently
- Archived entities must not appear in active workflows
