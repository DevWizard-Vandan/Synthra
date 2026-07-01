# SYNTHRA Quality Gates

This document defines the strict quality gates and verification checklists that must be satisfied before any branch is merged into the main line of the SYNTHRA repository.

---

## 🏛️ Quality Gate Checklists

### 1. Architecture
- The change must conform to the layered architecture defined in [ARCHITECTURE.md](file:///c:/Users/VANDAN/Projects/SYNTHRA/docs/ARCHITECTURE.md).
- Any modifications to component boundaries or interfaces must have an approved Architecture Decision Record (ADR) in the [adr directory](file:///c:/Users/VANDAN/Projects/SYNTHRA/docs/adr/).
- No circular dependencies are allowed between departments or system layers.

### 2. Documentation
- API changes must be documented in [CLAUDE.md](file:///c:/Users/VANDAN/Projects/SYNTHRA/CLAUDE.md) or corresponding specification documents.
- New public methods, classes, and modules must include complete Google-style docstrings.
- Explanatory inline comments must accompany any non-obvious logic. Existing comments must be preserved unless their code is deleted.

### 3. Testing
- Unit tests must be written for all new functions, methods, and classes.
- Overall codebase test coverage must not decrease and must maintain a minimum of **80% coverage**.
- All tests must run successfully in an offline environment (no external network dependencies allowed; mock all API connections).

### 4. Typing
- Explicit type annotations are required for all parameters, class properties, and return types.
- Static analysis checks run with `mypy` must return zero type errors. Use of the `Any` type is restricted to scenarios where generic specifications are impossible.

### 5. Logging
- Use Python's standard `logging` library. Direct print statements are prohibited.
- Operational actions must be logged at `INFO`. Diagnostic data (such as raw API payloads) must use `DEBUG`.
- Error paths must log exceptions with `logger.error(..., exc_info=True)` to preserve stack traces.

### 6. Error Handling
- Generic exceptions (e.g., catching `Exception` or `BaseException`) must never be swallowed silently.
- Network and API operations must define timeout parameters and handle connection failures cleanly.
- Errors crossing layer boundaries must be caught, logged, and re-thrown as custom system exceptions.

### 7. Performance
- Core database transactions must utilize indices for key-based lookups.
- Large collection retrievals must utilize pagination to avoid memory bloat.
- The LLM Router must optimize cost and latency, falling back to smaller models for simpler classification tasks.

### 8. Security
- API keys, credentials, and session tokens must never be committed to source control. Use environment variable lookups.
- System execution commands must validate argument syntax against a strict whitelist to prevent injection vulnerabilities.
- File operations must remain bounded within the workspace sandbox directory.

### 9. Maintainability
- Follow standard formatting and linting rules enforced by Black and Flake8.
- Classes must adhere to the Single Responsibility Principle. Long functions (exceeding 50 lines) should be refactored into smaller, testable units.

### 10. Code Review
- Every pull request must be reviewed and approved by at least one maintainer or the lead architect.
- Reviews must verify that the proposed changes do not introduce regressions in existing campaign performance.

---

## 🏁 Acceptance Criteria Checklist

Before submitting a Pull Request, run this script/validation checklist:

```bash
# 1. Format verification
black --check synthra/ tests/

# 2. Lint verification
flake8 synthra/ tests/

# 3. Static Type checks
mypy synthra/

# 4. Test suite run
pytest tests/ --cov=synthra --cov-fail-under=80
```
