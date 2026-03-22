---
name: create-initial-structured-requirements
model: opus
effort: high
description: Creates intial structured requirements from raw requirements for new project
---


Create the initial structured requirements for this new project from `docs/raw-requirements.md`.

Instructions:
- Read `docs/raw-requirements.md`
- Create `docs/requirements-index.md`
- Create one file per requirement in `docs/requirements/REQ-XXX.md`
- Start IDs from `REQ-001`
- Write atomic, clear, testable, implementation-oriented requirements
- Keep each requirement focused on one capability, rule, or constraint
- Link related requirements when applicable
- Clearly flag ambiguity, missing details, conflicts, and assumptions

Each requirement file must include:
- Requirement ID
- Title
- Priority (High, Medium, Low)
- Description
- Acceptance Criteria
- Related requirements (optional)

At the end, return a short summary of created requirements, ambiguities, and assumptions.