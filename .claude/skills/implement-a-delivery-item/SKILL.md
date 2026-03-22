---
name: implement-a-delivery-item
model: sonnet
effort: high
argument-hint: [delivery-item-id]
description: Implements a single delivery item for the project
---


Follow the delivery item implementation workflow:
1. Create a new branch for the implementation. Include the delivery item ID in the branch name.
2. Read `docs/delivery-items/<delivery-item-id>.md` and related documents (`docs/requirements/`, etc.) and identify the scope of work to implement.
3. Read `docs/architecture.md` to ensure the implementation aligns with the overall architecture.
4. Create an execution plan for this specific delivery item in `docs/execution-plans/<delivery-item-id>.md`.
5. Update `docs/architecture.md` and create `docs/architecture-decisions/ADR-XXX.md` only if architectural changes are required.
6. Define test cases for the requirement(s) in a new test suite file in `docs/test-suites/`.
   - Create one test suite file per delivery item, named `TS-<suite-id>.md` (e.g., `TS-001.md`) using the next available sequential ID
   - Avoid creating duplicate test cases. Before adding new test cases, review existing files in `docs/test-suites/` and reuse or reference existing test cases whenever they already cover the same requirement or validation scenario.
   - Assign each test case a unique ID in the format `TC-<test-suite-id-number>-<sequential-id>` (e.g., `TC-001-001`, `TC-001-002`)
   - The suite file must declare the Delivery Item ID and Requirements ID(s) it covers
   - Update `docs/test-suites-index.md` to include the new test suite
7. Implement the delivery item in `src/`
   - Keep the code modular, maintainable, and consistent with the project structure and architecture
   - Follow best practices and avoid unnecessary complexity
   - Ensure data migration scripts are created and executed for any database schema changes
8. Add or update automated tests for the implementation in `tests/`
   - Tests must cover core business logic
   - Tests should cover API routes where applicable
9. Run the relevant tests, then run the full test suite to validate the solution.
10. Update `docs/user-guide.md` with any user-facing changes introduced by the implementation.
11. Update `README.md` if needed to reflect the final implementation
12. Build and start the application with Docker Compose, verify that it runs successfully, and validate the health check endpoint.
   - Keep the Docker instance running after validation
13. Commit the changes only if:
   - the implementation is complete
   - all relevant tests pass
   - the full test suite passes
   - the containerized application starts successfully
   - the health check passes
14. Push the branch.
15. Merge the branch into `main` only if all validation steps above succeed. Never merge code with failing tests or a failing container startup.

If any step fails, fix the issues and repeat the necessary validation steps before committing or merging.