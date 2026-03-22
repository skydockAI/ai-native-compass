---
name: create-initial-delivery-plan
model: opus
effort: high
description: Creates intial delivery plan from structured requirements and architecture for new project
---

Create the initial incremental delivery plan for this project.

Tasks:
1. Read `docs/requirements-index.md`
2. Read all files in `docs/requirements/`
3. Read `docs/architecture.md`
4. Read all files in `docs/architecture-decisions/` if any exist

Output:
- Create or update `docs/delivery-items-index.md`
- Create one file per delivery item in `docs/delivery-items/DI-XXX.md`

Rules:
- Group structured requirements into delivery items
- Each delivery item must be a coherent, incremental, and releasable unit of delivery
- Consider dependencies, implementation sequence, and risk reduction
- Earlier delivery items should establish foundations needed by later items
- When appropriate, make the first delivery item a foundation delivery item that establishes the project skeleton and core setup required for subsequent delivery items, such as application structure, configuration, local run setup, test baseline, and Docker / Docker Compose setup.
- Keep delivery items reasonably sized for implementation by an AI coding agent
- Do not duplicate scope across delivery items
- Every structured requirement should be mapped to a delivery item, unless it is explicitly deferred
- Use 3-digit incremental IDs starting from the next available `DI-XXX`
- Maintain traceability from each delivery item to the requirement(s) it covers
- Clearly identify dependencies between delivery items
- Prefer a practical delivery sequence that leads to an early usable version of the system

Each delivery item file must include:
- Delivery Item ID
- Title
- Objective
- Included Requirements
- Scope
- Key Implementation Notes
- Dependencies
- Definition of Done

Also update `docs/delivery-items-index.md` so it lists all delivery items in planned implementation order.

At the end, provide a short summary of:
- delivery items created
- requirement-to-delivery-item mapping
- major sequencing decisions