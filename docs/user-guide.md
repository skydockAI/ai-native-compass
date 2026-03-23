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

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_PASSWORD` | PostgreSQL database password | `secure_password_here` |
| `FLASK_SECRET_KEY` | Secret key for Flask sessions | `random_secret_string` |
| `ADMIN_SEEDS` | Initial admin users (email:password pairs) | `admin@example.com:changeme123` |
