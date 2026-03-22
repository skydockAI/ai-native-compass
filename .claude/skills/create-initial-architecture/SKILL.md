---
name: create-initial-architecture
model: opus
effort: high
description: Creates intial architecture from structured requirements for new project
---

Create `docs/architecture.md` for this project.

Tasks:
1. Read `README.md`
2. Read `docs/raw-requirements.md`
3. Read `docs/requirements-index.md`
4. Read all files in `docs/requirements/`

Rules:
- Define the overall architecture and key design decisions
- Recommend the technology stack for each major layer of the system
- Describe the main components, data model, integrations, and end-to-end flows at a high level
- Cover backend, frontend, database, background jobs, AI integration, and external services as applicable
- Ensure the design is consistent with the requirements and suitable for incremental implementation
- Make assumptions only when necessary, and state them explicitly
- Write for both humans and AI agents who will later create delivery items and implement code

At the end, return a short summary of major design decisions, assumptions, and open questions