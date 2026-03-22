---
name: fix-bug
model: opus
effort: high
description: Fixes one or more bugs
---

Follow the bug fix implementation workflow:
1. Create a new branch for the bug fix.
2. Review relevant documents (requirements, architecture, test suites, etc.) to understand the bug and the scope of work to fix it.
3. Identify root cause and plan the fix.
4. Review current test suites and test cases. Add or update test cases if needed.
5. Implement the fix
6. Run the relevant tests, then run the full test suite to validate the fix.
7. Update related documents (architecture, user guide, README) **only if needed**
8. Build and start the application with Docker Compose, verify that it runs successfully, and validate the health check endpoint.
   - Keep the Docker instance running after validation
9. Commit the changes only if:
   - the implementation is complete
   - all relevant tests pass
   - the full test suite passes
   - the containerized application starts successfully
   - the health check passes
10. Push the branch.
11. Merge the branch into `main` only if all validation steps above succeed. Never merge code with failing tests or a failing container startup.

If any step fails, fix the issues and repeat the necessary validation steps before committing or merging.