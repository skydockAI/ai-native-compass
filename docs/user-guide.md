# AI Native Compass — User Guide

## Getting Started

### Prerequisites
- Docker and Docker Compose installed
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ai-native-compass
   ```

2. Create your environment file:
   ```bash
   cp .env.sample .env
   ```

3. Edit `.env` and set secure values:
   - `DB_PASSWORD` — PostgreSQL password
   - `FLASK_SECRET_KEY` — Flask session signing key
   - `ADMIN_SEEDS` — Comma-separated `email:password` pairs for initial admin users

4. Start the application:
   ```bash
   docker compose up -d
   ```

5. Access the application at [http://localhost:5005](http://localhost:5005)

### Stopping the Application

```bash
docker compose down
```

Data is persisted in `.data/postgres/` and survives container restarts.

### Running Tests

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest
```

## Authentication

### Signing In

Open [http://localhost:5005](http://localhost:5005) in your browser. You will be redirected to the Sign In page.

Enter your **email address** and **password**, then click **Sign In**.

- On success you are redirected to the Dashboard.
- On failure a generic error is shown — the message does not reveal whether the email or password was incorrect.

### Signing Out

Click the user icon in the top-right navbar area and select **Sign Out**, or navigate directly to [http://localhost:5005/logout](http://localhost:5005/logout).

### Initial Admin Account

The first admin user is created automatically on application startup from the `ADMIN_SEEDS` environment variable (see [Environment Variables](#environment-variables) below). No manual database setup is required.

Seeded admin accounts:
- Cannot be demoted to a lower role.
- Cannot be archived or deleted.

### Password Requirements

Passwords must be **at least 8 characters** long.

### Changing Your Password

Any authenticated user can change their own password:

1. Click your name in the top-right navbar and select **Change Password**.
2. Enter your **current password** and your **new password** (minimum 8 characters).
3. Confirm the new password and click **Change Password**.

### Access Control

All pages (except the login page) require authentication. If your session expires or your account is deactivated, you are redirected to the Sign In page immediately.

The system uses three roles with different permission levels:

| Action | Admin | Editor | Viewer |
|--------|-------|--------|--------|
| View dashboard and data | Yes | Yes | Yes |
| Manage products, repositories, teams | Yes | Yes | No |
| Manage users | Yes | No | No |
| Manage repo templates | Yes | No | No |
| View audit logs | Yes | No | No |

---

## Navigation

The application uses a sidebar navigation with the following sections:

- **Dashboard** — Overview with summary cards
- **Products** — Manage products
- **Repositories** — Manage code repositories
- **Templates** — Manage repo templates (Admin only)
- **Teams** — Manage teams
- **Users** — Manage users (Admin only)
- **Audit Log** — View audit history (Admin only)

The Administration section (Users, Audit Log) is only visible in the sidebar for Admin users.

---

## User Management (Admin Only)

### Viewing Users

Navigate to **Users** in the sidebar. The list defaults to showing **active** users. Click **Show Archived** to see archived users.

### Creating a User

1. Click **New User** on the user list page.
2. Fill in the email, full name, password (minimum 8 characters), and select a role.
3. Click **Create User**.

Email addresses must be unique across the system (case-insensitive). An email used by an archived user cannot be reused.

### Editing a User

Click the **pencil icon** next to a user in the list. Update the email, name, or role and click **Save Changes**.

Seeded admin accounts cannot have their role changed from Admin.

### Archiving a User

Click the **archive icon** next to a user. Archived users cannot log in and are hidden from the default user list. Seeded admin accounts cannot be archived.

### Reactivating a User

Switch to the archived users view, then click the **reactivate icon** next to the user.

### Resetting a User's Password

Click the **key icon** next to a user. Enter the new password (minimum 8 characters) and click **Reset Password**. The user can immediately log in with the new password.

## Team Management (Admin and Editor)

Teams are used to categorise code repositories. Each repository belongs to exactly one team.

### Viewing Teams

Navigate to **Teams** in the sidebar. The list defaults to showing **active** teams. Click **Show Archived** to see archived teams.

All authenticated users (Admin, Editor, Viewer) can view the team list.

### Creating a Team

1. Click **New Team** on the team list page (requires Admin or Editor role).
2. Enter a **team name** (required, must be unique) and an optional **description**.
3. Click **Create Team**.

Team names must be unique across the system. Attempting to create a team with a name already in use shows a clear error message.

### Editing a Team

Click the **pencil icon** next to a team in the list (Admin or Editor only). Update the name or description and click **Save Changes**.

### Archiving a Team

Click the **archive icon** next to a team and confirm (Admin or Editor only).

A team **cannot** be archived while it has active repositories assigned to it. The error message will list the blocking repositories. Archive or reassign those repositories first, then archive the team.

### Reactivating a Team

Switch to the archived teams view and click the **reactivate icon** next to a team (Admin or Editor only).

---

## Template Management (Admin Only)

Repo Templates define the set of artifacts (documents, skills, agents, and custom items) that repositories using the template are expected to track.

### Viewing Templates

Navigate to **Templates** in the sidebar. The list defaults to showing **active** templates. Click **Show Archived** to see archived templates.

All authenticated users can view the template list and template detail pages.

### Creating a Template

1. Click **New Template** on the template list page (Admin only).
2. Enter a **template name** (required, must be unique) and an optional **description**.
3. Click **Create Template**.

Template names must be unique across the system.

### Editing a Template

Click the **pencil icon** next to a template, or open the template detail page and click **Edit Template** (Admin only). Update the name or description and click **Save Changes**.

### Archiving a Template

Click the **archive icon** next to a template and confirm (Admin only).

A template **cannot** be archived while it has active repositories assigned to it. The error message will list the blocking repositories. Archive or reassign those repositories first, then archive the template.

### Reactivating a Template

Switch to the archived templates view and click the **reactivate icon** next to a template (Admin only).

---

## Artifact Management within Templates (Admin Only)

Each template contains a list of **artifacts** — items that repositories using the template are expected to track.

### Artifact Types

| Type | Value Options |
|------|--------------|
| **Document** | Yes / No / N/A |
| **Skill** | Yes / No / N/A |
| **Agent** | Yes / No / N/A |
| **Other** | text, number, boolean (True/False/N/A), or list |

### Adding an Artifact

1. Open a template's detail page.
2. Click **Add Artifact**.
3. Select the **type** (Document, Skill, Agent, or Other).
4. Enter a **name** and optional **description**.
5. For **Other** type: select a **value type** (text, number, boolean, or list) and optionally mark as **Required**.
6. Set a **display order** to control the artifact's position in the list.
7. Click **Save Artifact**.

Note: Artifact type and value type cannot be changed after creation.

### Editing an Artifact

Click the **pencil icon** next to an artifact on the template detail page. You can update the name, description, required flag, and display order.

### Removing an Artifact

Click the **trash icon** next to an artifact and confirm. This permanently removes the artifact definition from the template.

### Required Flag (Other type only)

When an Other-type artifact is marked **Required**, repositories using this template must provide a value for it when saving. The UI displays a "Required" badge to indicate this.

---

## List Option Management (Admin Only)

For **Other:list** artifacts, Admin users define the dropdown options available for selection.

### Adding a List Option

1. On the template detail page, click the **list icon** next to an Other:list artifact.
2. Enter the **option value** and an optional **display order**.
3. Click **Save Option**.

### Editing a List Option

Click the **pencil icon** next to an option on the template detail page to update its value or display order.

### Deactivating a List Option

Click the **dash-circle icon** next to an option to deactivate it. Deactivated options:
- Are hidden from new selections on repository edit pages.
- Are still displayed on repositories that already have them selected.
- Can be deactivated even if currently in use.

### Deleting a List Option

Click the **X icon** next to an option to permanently delete it. Deletion is only allowed if the option is **not currently selected by any repository**. If it is in use, deactivate it instead.

---

## Repository Management (Admin and Editor)

Repositories represent code repositories being tracked for AI Native adoption. Each repository is linked to one Team and one Repo Template, which determines which artifacts are tracked.

### Viewing Repositories

Navigate to **Repositories** in the sidebar. The list defaults to showing **active** repositories. Click **Show Archived** to see archived repositories.

All authenticated users (Admin, Editor, Viewer) can view the repository list and repository detail pages.

### Creating a Repository

Repository creation follows a **template-first** workflow:

1. Click **New Repository** on the repository list page (Admin or Editor only).
2. Select a **Template** from the dropdown. After selection, the artifact fields for that template are loaded automatically.
3. Fill in the default fields:
   - **Repository name** (required)
   - **Repository URL** (required, must be globally unique)
   - **Description** (optional)
   - **Team** (required — only active teams are shown)
4. Fill in any **custom shared attributes** (if configured by an Admin).
5. Fill in the **artifact values** loaded from the selected template:
   - Document / Skill / Agent: Yes / No / N/A
   - Other:text: free text
   - Other:number: numeric value
   - Other:boolean: True / False / N/A
   - Other:list: select from dropdown options
6. Click **Create Repository**.

**Important:**
- The template cannot be changed after creation.
- Repository URLs must be unique across all repositories, including archived ones.
- Required artifact fields (marked with a red asterisk) must be filled in before saving.

### Viewing Repository Details

Click on a repository name in the list, or click the **eye icon**, to open the detail page. The detail page shows:
- Repository details (URL, Team, Template, Description, custom shared attributes)
- All artifact values for the assigned template

### Editing a Repository

Click the **pencil icon** next to a repository in the list, or the **Edit** button on the detail page (Admin or Editor only).

On the edit form:
- The **Template** is shown as read-only and **cannot be changed**.
- Name, URL, Description, Team, custom shared attribute values, and artifact values can all be updated.
- The same validation rules apply (URL uniqueness, required artifacts).

### Archiving a Repository

Click the **archive icon** next to a repository and confirm (Admin or Editor only). Archived repositories are hidden from the default list but their data is preserved.

### Reactivating a Repository

Switch to the archived repositories view and click the **reactivate icon** next to a repository (Admin or Editor only).

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_PASSWORD` | PostgreSQL database password | `secure_password_here` |
| `FLASK_SECRET_KEY` | Secret key for Flask sessions | `random_secret_string` |
| `ADMIN_SEEDS` | Initial admin users (email:password pairs) | `admin@example.com:changeme123` |
