🛡️ Citadel AI OS Plan B – Task Execution Rules
Read this before executing any task. It ensures structured, safe, and verifiable progress across the Citadel-Alpha-LLM-Server-1 deployment.

🔄 Project Awareness & Context
Rule: (1) Always read /planning/README-ANALYSIS-ASSESSMENT.md at the start of a work session for full context.

Rule: (2) Check TASK.md before starting. If the task is missing, create an entry with a brief summary and today’s date.

Rule: (3) Maintain project-wide naming, directory, and architecture consistency.

🧱 Code Structure & Modularity
Rule: (4) Refactor for Maintainability. Any script that grows too large (over ~150 lines) or contains complex, embedded logic (like multi-line Python in a shell script) must be refactored.

Extract Logic: Move complex logic into dedicated, single-purpose helper scripts or Python modules.

Use Utility Classes: Group common, reusable functions (like running system commands or file I/O) into utility classes.

Apply OOP: Use object-oriented design and classes to model complex data and behavior, following the single-responsibility principle.

Rule: (5) Keep individual source files under 500 lines. If a file grows too large, refactor into helper modules.

Rule: (6) Rule of Thumb for Class Size:

100–300 lines per class is optimal for readability, testing, and reusability.

If a class grows over 350 lines, it likely needs to be split into logical components or helpers.

Rule: (7) Never hardcode configuration. Always use one of the following supported methods for loading configuration:

Use the dotenv package to load environment variables from a .env file.

Use a pydantic-based settings class for configuration validation and management.

For structured config, load config.json or config.yaml files from /configs/ into Python dataclasses or pydantic models.
This ensures all configuration is centralized, validated, and managed in a consistent, testable way across the project.

Rule: (8) Use relative imports and group code by clear functional boundaries (models, services, utilities, etc.).

🧪 Testing & Reliability
Rule: (9) Capture all validation results in a dedicated task result file.

Rule: (10) Place all test code in the canonical tests/ directory. Use semantic tags, labels, or naming conventions (e.g., test_validation_*.py) to categorize tests (such as "validation" or "integration") instead of creating separate directories like /validation/.

Rule: (11) All tests must be:

Isolated and deterministic

Lightweight and easy to re-run

Aligned with production-like conditions

✅ Task Completion
Rule: (12) Mark completed tasks in /tasks/task-tracker.md.

Rule: (13) Log discoveries or new todos in /tasks/task-tracker-backlog.md.

Rule: (14) Generate a result document for each task and save it in /tasks/task-results/. Each result file must include:

Tasks completed

Deviations from plan

Observations or anomalies

File name format: task-PLANB-XX-results.md

Rule: (15) Do not begin a new task until the current one is fully completed, tested, and documented.

📎 Style & Conventions
Rule: (16) Language: Python 3.12

Rule: (17) Formatter: Use black.

Rule: (18) Typing & Linting: Follow PEP8, use type hints, and validate with mypy.

Rule: (19) Shell Scripts: Must be POSIX-compliant (#!/bin/bash) and live in /scripts/.

📚 Documentation & Explainability
Rule: (20) Update /README.md if setup instructions change or dependencies/runtime conditions are updated.

Rule: (21) Update /planning/PLANB-05-IMPLEMENTATION-GUIDE.md if model logic or architecture changes.

Rule: (22) Use comments intentionally. Use # Reason: above non-obvious blocks to explain why and avoid redundant comments.

🧠 AI Behavior Rules
Rule: (23) Never assume missing context — always ask.

Rule: (24) Do not hallucinate libraries or APIs. Use only documented Python packages or ones installed in the environment.

Rule: (25) Always verify that paths, modules, and files exist before referencing them.

Rule: (26) Never delete, rename, or overwrite files unless explicitly required by the current task and approved by the operator.

Rule: (27) All code must be valid, testable, and executable in the Ubuntu 24.04 LTS environment.

Rule: (28) Do not close a task until all sub-tasks have been implemented and tested.

Rule: (29) Test results must be approved by the user.

Rule: (30) Do not fix and retry more than 3 times; before the fourth attempt, ask for help.

✅ When ready, execute the assigned task in /tasks/, validate it, document it in /tasks/task-results/, then wait for user.