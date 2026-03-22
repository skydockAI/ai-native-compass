# AI Native Compass (ANC)

AI Native Compass helps teams track and visualize AI Native Engineering adoption across products and code repositories.

## Quick Start

```bash
# 1. Configure environment
cp .env.sample .env
# Edit .env with your settings

# 2. Start the application
docker compose up -d

# 3. Open in browser
open http://localhost:5000
```

## Tech Stack

- **Backend**: Python 3.12, Flask 3.x, SQLAlchemy 2.x
- **Database**: PostgreSQL 16
- **Frontend**: Jinja2 templates, Bootstrap 5, HTMX 2.x
- **Deployment**: Docker Compose, Gunicorn

## Development

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest

# Run locally (requires PostgreSQL)
FLASK_ENV=development PYTHONPATH=src flask run
```

## Project Structure

```
ai-native-compass/
├── src/app/           # Flask application
│   ├── __init__.py    # App factory
│   ├── config.py      # Configuration
│   ├── extensions.py  # Flask extensions
│   ├── models/        # SQLAlchemy models
│   ├── routes/        # Flask blueprints
│   ├── services/      # Business logic
│   ├── templates/     # Jinja2 HTML templates
│   └── static/        # CSS, JS, images
├── tests/             # Test suite
├── migrations/        # Alembic migrations
├── docker-compose.yml # Docker Compose config
├── Dockerfile         # Container image
└── docs/              # Project documentation
```

## Documentation

- [User Guide](docs/user-guide.md)
- [Architecture](docs/architecture.md)
- [Requirements Index](docs/requirements-index.md)
- [Delivery Items](docs/delivery-items-index.md)
