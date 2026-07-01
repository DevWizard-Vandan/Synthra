# Synthra Coding Standards & Guidelines

> **Version:** 1.0.0  
> **Target Languages:** Python, TypeScript/JavaScript  

---

## 💡 Core Principles

1.  **Readability Over Cleverness**: Code is read much more often than it is written. Keep expressions clear and simple.
2.  **Explicit is Better than Implicit**: Avoid hidden magic or dynamic class definitions that make static analysis difficult for AI agents.
3.  **Strict Type Annotations**: All new files must use type annotations to enforce design clarity and assist model autocomplete tools.
4.  **Preserve Comments**: Never strip existing comments or docstrings from files unless explicitly rewriting the functionality.

---

## 🐍 Python Guidelines

### Code Formatting
- Follow **PEP 8** style guidelines.
- Use **Black** for auto-formatting and **Flake8** for linting.
- Max line length is **88 characters** (matching Black's default).

### Types & Docstrings
- Every function must contain type hints for all parameters and return types.
- Follow the Google Style Python Docstrings convention:

```python
def calculate_metrics(data: list[float], threshold: float = 0.5) -> dict[str, float]:
    """Computes basic performance metrics for the agent output.

    Args:
        data: A list of confidence ratings or scores.
        threshold: The value below which scores are ignored.

    Returns:
        A dictionary containing average and peak scores.

    Raises:
        ValueError: If data is empty.
    """
    if not data:
        raise ValueError("Data list cannot be empty.")
    ...
```

---

##  TypeScript & JavaScript Guidelines

### Standards
- Prefer **TypeScript** (`strict: true`) over vanilla JavaScript.
- Format code using **Prettier** and lint with **ESLint**.
- Use ES6+ modules (`import/export`) exclusively.

### Code Style
- Use `const` by default; use `let` only if variable reassignment is required.
- Do not use `any` types; define `interface` or `type` contracts explicitly.
- Use async/await over raw Promises or callbacks.

---

## 🧪 Testing Requirements

- **Unit Tests**: Every public function or method must have corresponding unit tests.
- **Coverage**: Aim for at least **80% code coverage** on all core components.
- **Frameworks**:
  - Python: Use `pytest` for unit testing and assertion blocks.
  - TypeScript: Use `jest` or `vitest` for test execution.
- **Execution**: Tests must run locally without external network calls (mock all APIs).

---

## 🔀 Git & Pull Request Protocol

### Branch Naming Conventions
- `feat/feature-name` (new features)
- `fix/bug-name` (bug fixes)
- `docs/doc-name` (documentation edits)
- `refactor/refactor-name` (code optimization, no behavior change)

### Commit Messages
We enforce **Conventional Commits**:
- `feat(sandbox): add file system read restrictions`
- `fix(bus): resolve event emitter memory leak`
- `docs(constitution): clarify user approval limits`

### Pull Request Checklist
Before submitting a PR, make sure:
1. All linting checks pass.
2. All unit tests pass locally.
3. Documentation is updated to match code modifications.
4. If a core API changes, a corresponding ADR entry is logged.
