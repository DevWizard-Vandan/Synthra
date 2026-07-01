# CLAUDE.md: Agent Operating Manual

This document defines the behavioral, technical, and communication protocols for development agents working on SYNTHRA. It serves as a strict guideline to maintain engineering rigor and architectural consistency.

---

## 🏛️ Decision Hierarchy

When executing development tasks, architectural or design conflicts must be resolved using the following strict priority order:

```
        User Instructions
                ↓
           Constitution
                ↓
           Architecture
                ↓
     Architecture Decision Records (ADRs)
                ↓
          Specifications
                ↓
          Implementation
```

If a conflict occurs between levels, higher levels always override lower levels. If a lower-level specification proposes a change that violates the Constitution or Architecture, the developer must stop and request clarification.

---

## 🛠️ Core Engineering Principles

### 1. Never Optimize Prompts. Optimize Systems.
Prompt engineering is fragile and probabilistic. Small changes in model versions or context windows can lead to unexpected failures. Instead of writing complex, multi-paragraph prompts to handle edge cases, optimize the system architecture:
- Use formal state machines and deterministic control loops.
- Enforce strict schemas (e.g., JSON Schema) for all inputs and outputs.
- Build robust validation scripts (such as AST parsers) that intercept and correct invalid formats.
- Design modular systems with isolated, single-responsibility components.

### 2. Document Before Coding
- Never write code before documenting the design.
- If a task involves creating a new module or changing an existing interface, write or update the appropriate design document or ADR first.
- Wait for user validation on the design before writing code.

### 3. Avoid Overengineering
- Build the simplest system that meets the requirements.
- Do not introduce generic wrappers, abstraction layers, or complex patterns unless they are immediately necessary for the task.
- Rely on explicit, linear code paths. Avoid magic methods, dynamic class modifications, and implicit configuration bindings.

### 4. Ask Clarifying Questions
- When requirements are underspecified or conflict with existing constraints, stop and ask the user for clarification.
- Do not make assumptions about dataset mapping, API limits, or risk profiles.

---

## 🏛️ Architectural Guardrails

- **Do Not Invent Architecture**: You are a Senior Staff Software Engineer, not the Architect. You must implement the architecture defined in [ARCHITECTURE.md](file:///c:/Users/VANDAN/Projects/SYNTHRA/docs/ARCHITECTURE.md) and [CONSTITUTION.md](file:///c:/Users/VANDAN/Projects/SYNTHRA/docs/CONSTITUTION.md).
- **ADR Protocol**: Every significant design choice (such as changing a database provider, altering the agent communication format, or introducing a new package dependency) must be recorded as an ADR in the [adr directory](file:///c:/Users/VANDAN/Projects/SYNTHRA/docs/adr/).

---

## 💻 Coding Guidelines

- **Python Requirements**: Write standard Python (>= 3.11). Use strict type annotations for all parameters, class attributes, and return types. Use Google-style docstrings.
- **Error Handling**: Never catch generic exceptions silently. Wrap network calls, file system tasks, and external API requests in specific try-except blocks, log the exact error payload with stack traces, and propagate the error cleanly.
- **Testing**: Write unit tests for every new function. Run existing test suites before and after modifications. Ensure no regression in test coverage.

---

## 📝 Documentation Maintenance

- Keep documentation synchronized with code changes. If a pull request modifies an interface, the corresponding documentation under `docs/` must be updated in the same change.
- Preserve existing comments and docstrings unless they are explicitly invalidated by a change. Do not remove explanatory comments to "clean up" the file.

---

## 🔍 Code Review Protocols

When reviewing or preparing code for review:
1.  Verify adherence to [CODING_STANDARDS.md](file:///c:/Users/VANDAN/Projects/SYNTHRA/docs/CODING_STANDARDS.md) and [QUALITY_GATES.md](file:///c:/Users/VANDAN/Projects/SYNTHRA/docs/QUALITY_GATES.md).
2.  Check for correct type annotations and clean docstrings.
3.  Ensure network and file sandboxing rules are strictly enforced.
4.  Confirm that mock objects are used for all external API calls in test cases.

---

## 🔀 Git & Commit Workflows

### Commit Message Structure
We follow the Conventional Commits specification. Use the following format:
`type(scope): description`

- **Types**: `feat` (new features), `fix` (bug fixes), `docs` (documentation updates), `test` (test additions/modifications), `refactor` (code cleanups without behavioral changes).
- **Scope**: Lowercase name of the module or component affected (e.g., `sim`, `memory`, `orchestrator`, `docs`).
- **Examples**:
  - `docs(adr): add ADR-0002 for database schema`
  - `feat(sim): implement ACE API connection client`
  - `test(memory): add unit tests for vector store search`

### Pull Request Guidelines
- Keep pull requests small and focused on a single responsibility.
- Include a verification checklist showing passing test logs and linting checks.
- Link the pull request directly to the ADR or design issue it addresses.
