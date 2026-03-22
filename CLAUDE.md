# Repository and Python Environment
- This project follows the standard structure:
  - `src/` for application source code
  - `tests/` for test code and test scripts
  - `docs/` for project documentation
- Always use the project virtual environment at `.venv` when running Python commands or scripts.
- If `.venv` does not exist, create it before running any Python-related command:
  1. Try `python3 -m venv .venv`
  2. If that fails, try `python -m venv .venv`
- After creating or activating `.venv`, install required dependencies from `requirements.txt` if needed.
- Do not rely on the system-wide Python environment unless explicitly required.

# Project Documentation Structure
This project uses the following documentation and repository structure:

- `README.md`: Project overview and general repository entry point.
- `docs/raw-requirements.md`: Raw, unstructured requirements and notes.
- `docs/requirements-index.md`: Index of all structured requirements.
- `docs/requirements/REQ-XXX.md`: One file per structured requirement.
- `docs/architecture.md`: Overall system architecture.
- `docs/architecture-decisions/ADR-XXX.md`: One file per architecture decision record.
- `docs/delivery-items-index.md`: Index of all delivery items.
- `docs/delivery-items/DI-XXX.md`: One file per delivery item. A delivery item is a releasable unit of work that may cover one or more requirements.
- `docs/execution-plans/DI-XXX.md`: One file per delivery item. Defines the detailed execution plan for implementing that delivery item before making code changes.
- `docs/test-suites-index.md`: Index of all test suites.
- `docs/test-suites/TS-XXX.md`: One file per test suite. Each test suite contains one or more test cases.
- `docs/user-guide.md`: End-user documentation.

## ID Conventions
All IDs use a 3-digit incremental number format: `XXX`.
- Requirements: `REQ-XXX`. Example: `REQ-001`
- Architecture Decision Records: `ADR-XXX`. Example: `ADR-001`
- Delivery Items: `DI-XXX`. Example: `DI-001`
- Test Suites: `TS-XXX`. Example: `TS-001`
- Test Cases: `TC-<test suite number>-XXX`. Example: `TC-001-001`

## Traceability
When applicable, maintain traceability across artifacts:
- `docs/requirements/REQ-XXX.md` links to related delivery items, architecture, and test suites
- `docs/delivery-items/DI-XXX.md` links to covered requirements
- `docs/execution-plans/DI-XXX.md` links to the corresponding delivery item
- `docs/test-suites/TS-XXX.md` links to covered requirements and/or delivery items
- Each test case in `docs/test-suites/TS-XXX.md` should link to the requirement(s) it validates