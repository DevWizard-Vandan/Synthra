# SYNTHRA Coding Standards

This document establishes the code quality, design, and execution standards for the SYNTHRA project. All contributors and development agents must conform to these rules.

---

## 🐍 Python Standards

### Language Baseline
- All code must target **Python >= 3.11**.
- Code formatting is enforced using **Black** and linting via **Flake8**.
- Maximum line length is **88 characters**.

### Type Hints
- All variables, function arguments, class properties, and return types must be explicitly annotated.
- Avoid the use of `Any` where possible. Prefer narrow types, generic parameters, or custom TypeVars.

```python
from typing import Sequence, Mapping

def process_metrics(
    raw_scores: Sequence[float], 
    config: Mapping[str, float]
) -> dict[str, float]:
    # Type hints are mandatory
    ...
```

---

## 📂 Folder Structure

The project code must be organized into decoupled modules under the main `synthra` directory:

```
synthra/
├── __init__.py
├── core/                     # Orchestration and system scheduling
│   ├── orchestrator.py
│   └── scheduler.py
├── agents/                   # Agent profile implementations
│   ├── base.py
│   ├── hypothesis.py
│   ├── synthesizer.py
│   └── evaluator.py
├── memory/                   # Database interfaces and vector wrappers
│   ├── db.py
│   └── vector_store.py
├── execution/                # Outer interface controllers
│   ├── sandbox.py
│   └── simulation.py
└── utils/                    # Helper packages
    ├── config.py
    └── logger.py
```

---

## 🏷️ Naming Conventions

- **Classes**: PascalCase (`SimulationClient`, `HypothesisEngine`).
- **Functions & Methods**: snake_case (`execute_backtest`, `get_dataset_metadata`).
- **Variables & Attributes**: snake_case (`auth_token`, `retry_count`).
- **Constants**: UPPERCASE_SNAKE_CASE (`MAX_RETRY_ATTEMPTS`, `TIMEOUT_SECONDS`).
- **Private properties**: Prefixed with a single underscore (`_session_context`).

---

## 📝 Logging & Diagnostics

- Do not use print statements for debugging or operational messages.
- Use Python's standard `logging` library. All modules must instantiate a logger using `logging.getLogger(__name__)`.
- Log levels:
  - `DEBUG`: Verbose diagnostics (e.g., token responses, raw JSON).
  - `INFO`: Normal operational milestones (e.g., task started, simulation finished).
  - `WARNING`: Recoverable issues (e.g., API retry, config fallback).
  - `ERROR`: Unrecoverable failures in a module (e.g., database connection loss, authentication failure).

---

## 🧪 Testing Protocol

- **Unit Tests**: Every public function and class method must have corresponding unit tests.
- **Framework**: Use `pytest` for executing unit tests.
- **Mocking**: All network calls (primarily calls to the WorldQuant BRAIN APIs) must be mocked using `pytest-mock` or standard `unittest.mock`. Running tests must require zero internet connectivity.
- **Location**: Test files must reside in a `tests/` directory at the root, duplicating the structure of the `synthra/` folder:
  ```
  tests/
  ├── core/
  ├── agents/
  ├── memory/
  └── execution/
  ```

---

## ⚠️ Error Handling

- Never catch generic exceptions silently:
  ```python
  # INCORRECT
  try:
      client.connect()
  except Exception:
      pass
  ```
- Catch narrow exceptions, log the detailed payload, and propagate or handle cleanly:
  ```python
  # CORRECT
  import logging
  from synthra.utils.exceptions import APIConnectionError

  logger = logging.getLogger(__name__)

  try:
      client.connect()
  except ConnectionTimeoutException as err:
      logger.error("API connection timed out: %s", err, exc_info=True)
      raise APIConnectionError("Failed to connect to the simulation server.") from err
  ```

---

## 📝 Documentation & Comments

- **Docstrings**: Every class, method, module, and public function must have a Google-style docstring.
- **Code Comments**:
  - Explain *why* a code path exists, not *what* it does.
  - Never strip out comments or docstrings from existing files unless rewriting the function behavior.
  - Keep comments concise and close to the code they describe.

---

## 🔀 Git & Code Review Standards

### Commit Structure
All commits must follow the Conventional Commits specification:
`<type>(<scope>): <description>`

- **Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.
- **Scope**: Matches the module directory (e.g., `sim`, `memory`, `core`, `docs`).
- **Description**: Present-tense, active verb (e.g., `implement connection pooling`).

### Code Review Checklist
Before any pull request is merged, it must meet the following criteria:
1.  All static analysis checks pass (linter clean, zero type checking errors from `mypy`).
2.  All unit tests pass.
3.  Coverage remains above `80%`.
4.  Documentation updates are included if API boundaries were modified.
5.  No hard-coded secrets or credentials exist.
