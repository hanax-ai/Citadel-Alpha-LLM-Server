# 🛡️ Citadel AI OS Plan B – Task Execution Rules

Read this before executing any task. It ensures structured, safe, and verifiable progress across the Citadel-Alpha-LLM-Server-1 deployment.

---

## 🔄 Project Awareness & Context

- **Always read** `/planning/README-ANALYSIS-ASSESSMENT.md` at the start of a work session for full context.
- **Check `TASK.md`** before starting:
  - If the task is missing, create an entry with a brief summary and today’s date.
- Maintain project-wide **naming, directory, and architecture consistency**.

---

## 🧱 Code Structure & Modularity

- **Keep individual source files under 500 lines.** If a file grows too large, refactor into helper modules.
- **Use object-oriented design principles:**
  - Create **as many classes as needed**, following the **single-responsibility principle (SRP)**.
  - Group related behaviors or logic into small, focused classes.
  - Use shared utility classes for reusable operations across modules.
  - Ensure that failures in one model/module **do not affect others**.
- **Rule of Thumb for Class Size:**
  - **100–300 lines per class** is optimal for readability, testing, and reusability.
  - If a class grows **over 500 lines**, it likely needs to be split into logical components or helpers.
- **Never hardcode configuration.** Always use:
  - `.env` for environment variables
  - `config.json` or `config.yaml` files in `/configs/` for structured config
- **Use relative imports** and group code by clear functional boundaries (models, services, utilities, etc.).

---

## 🧪 Testing & Reliability

- **Capture all validation results** in a dedicated task result file.
- Place test logic in `/validation/` or add new ones when needed.
- All tests must be:
  - Isolated and deterministic
  - Lightweight and easy to re-run
  - Aligned with production-like conditions

---

## ✅ Task Completion

- **Mark completed tasks in** `/tasks/task-tracker.md`
- **Log discoveries or new todos in** `/tasks/task-tracker-backlog.md`
- **Generate a result document for each task** and save it in:

Each result file must include:
- Tasks completed
- Deviations from plan
- Observations or anomalies
- File name format: `task-PLANB-XX-results.md`

- **Do not begin a new task** until the current one is fully completed, tested, and documented.

---

## 📎 Style & Conventions

- **Language:** Python 3.12
- **Formatter:** Use `black`
- **Typing & Linting:** Follow PEP8, use type hints, and validate with `mypy`
- **Shell Scripts:** Must be POSIX-compliant (`#!/bin/bash`) and live in `/scripts/`

---

## 📚 Documentation & Explainability

- Update `/README.md` if:
- Setup instructions change
- Dependencies or runtime conditions are updated
- Update `/planning/PLANB-05-IMPLEMENTATION-GUIDE.md` if model logic or architecture changes
- **Use comments intentionally**:
- Use `# Reason:` above non-obvious blocks to explain why
- Avoid redundant or obsolete comments

---

## 🧠 AI Behavior Rules

- **Never assume missing context — always ask.**
- **Do not hallucinate libraries or APIs.**
- Use only documented Python packages or ones installed in the environment.
- **Always verify that paths, modules, and files exist** before referencing them.
- **Never delete, rename, or overwrite files** unless:
- Explicitly required by the current task
- Approved by the operator
- **All code must be valid, testable, and executable** in the Ubuntu 24.04 LTS environment.

---

✅ When ready, execute the assigned task in `/tasks/`, validate it, document it in `/tasks/task-results/`, then move on.
