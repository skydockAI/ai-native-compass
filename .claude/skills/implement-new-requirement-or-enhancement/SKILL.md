---
name: implement-new-requirement-or-enhancement
model: sonnet
effort: high
description: Implements one or more new requirements or enhancements
---

Follow the new requirement or enhancement implementation workflow:
1. Create a new branch for the new requirement or enhancement.
2. Review `docs/requirements-index.md` and `docs/requirements/` to determine whether one or more requirements should be added or updated.
3. Update `docs/requirements-index.md` and `docs/requirements/` if any changes are needed.
4. Read `docs/architecture.md` to ensure the implementation aligns with the overall architecture.
5. Create a new delivery item for the changes in `docs/delivery-items/` and update `docs/delivery-items-index.md`. Use the next available sequential ID.
6. Create an execution plan for the new delivery item in `docs/execution-plans/<delivery-item-id>.md`.
7. Basing on the execution plan, update `docs/architecture.md` and create `docs/architecture-decisions/ADR-XXX.md` only if architectural changes are required.
8. Define test cases for the requirement(s) in a new test suite file in `docs/test-suites/`.
   - Create one test suite file per delivery item, named `TS-<suite-id>.md` (e.g., `TS-001.md`) using the next available sequential ID
   - Avoid creating duplicate test cases. Before adding new test cases, review existing files in `docs/test-suites/` and reuse or reference existing test cases whenever they already cover the same requirement or validation scenario.
   - Assign each test case a unique ID in the format `TC-<test-suite-id-number>-<sequential-id>` (e.g., `TC-001-001`, `TC-001-002`)
   - The suite file must declare the Delivery Item ID and Requirements ID(s) it covers
   - Update `docs/test-suites-index.md` to include the new test suite
9. Implement the delivery item in `src/`
   - Keep the code modular, maintainable, and consistent with the project structure and architecture
   - Follow best practices and avoid unnecessary complexity
   - Ensure data migration scripts are created and executed for any database schema changes
10. Add or update automated tests for the implementation in `tests/`
   - Tests must cover core business logic
   - Tests should cover API routes where applicable
11. Run the relevant tests, then run the full test suite to validate the solution.
12. Update `docs/user-guide.md` with any user-facing changes introduced by the implementation.
13. Update `README.md` if needed to reflect the final implementation
14. Build and start the application with Docker Compose, verify that it runs successfully, and validate the health check endpoint.
   - Keep the Docker instance running after validation
15. Commit the changes only if:
   - the implementation is complete
   - all relevant tests pass
   - the full test suite passes
   - the containerized application starts successfully
   - the health check passes
16. Push the branch.
17. Merge the branch into `main` only if all validation steps above succeed. Never merge code with failing tests or a failing container startup.

If any step fails, fix the issues and repeat the necessary validation steps before committing or merging.