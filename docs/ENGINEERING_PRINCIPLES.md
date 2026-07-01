# SYNTHRA Engineering Principles

This document defines the core technical and architectural tenets of SYNTHRA. All software construction, review, and design verification tasks must adhere to these principles.

---

## 🏛️ Core Architectural Tenets

### 1. Composition over Inheritance
- **Why**: Inheritance introduces tight coupling and deep class hierarchies that make refactoring and static code analysis difficult.
- **How**: Class behaviors should be constructed by combining small, decoupled instances (interfaces/dependencies) rather than subclassing.

### 2. Explicit over Implicit
- **Why**: Implicit configurations, magic constants, and reflection hide behavior and lead to unexpected runtime side effects.
- **How**: Code paths, variables, arguments, and module loading must be explicitly defined and traceable. Avoid magic decorators or hidden state injection.

### 3. Configuration over Hardcoding
- **Why**: Parameters (such as timeouts, rate limits, storage paths, and endpoints) change across campaign environments.
- **How**: Expose configurable attributes to the central Configuration Manager. No component should possess hardcoded operational settings.

### 4. Small Modules
- **Why**: Large code blocks are difficult to test, maintain, and audit.
- **How**: Restrict files to single logical concepts. Break functions exceeding 50 lines into smaller helper functions.

### 5. Single Responsibility Principle (SRP)
- **Why**: A class or module should have exactly one reason to change, minimizing downstream regressions.
- **How**: Ensure that an execution client handles transport, a validation parser handles AST checking, and an agent coordinator handles campaign schedules—never a combination of these.

### 6. Immutable Data
- **Why**: Shared mutable state introduces race conditions and bugs during parallel runs.
- **How**: Once objects (such as configurations, data assets, and messages) are loaded or compiled, they must be frozen/made read-only.

### 7. Events over Direct Coupling
- **Why**: Direct method invocation between layers (e.g., Execution calling Knowledge directly) creates tight coupling.
- **How**: Enable communication asynchronously by publishing structured events to the Event Bus. Components act as independent observers.

### 8. Simple Systems Win
- **Why**: Overly complex architectures with excessive abstraction layers increase latency and complicate debugging.
- **How**: Implement the simplest, most direct logical path that meets the functional requirements. Avoid premature generalization.

---

## ⚙️ Process & Validation Tenets

### 9. Document Before Coding
- **Why**: Code written without design blueprints leads to inconsistent interfaces and architectural drift.
- **How**: Design documents, ADRs, or SPECs must be written and approved before starting implementation.

### 10. Test Before Merge
- **Why**: Untested contributions introduce logic regressions.
- **How**: Maintain minimum test coverage requirements, including unit, integration, and failure path coverage. Execute all checks offline.

### 11. Fail Fast
- **Why**: Swallowing errors or delaying validation leads to silent failures and corrupts memory states.
- **How**: Validate inputs immediately at module boundaries. Raise exceptions and abort execution if invalid states occur.

### 12. Research Before Optimization
- **Why**: Premature code optimization wastes development resources on non-bottleneck components.
- **How**: Write clean, standard code first. Only optimize bottlenecks after collecting empirical latency and memory metrics.

### 13. Knowledge Before Automation
- **Why**: Automatically generating strategies without systematic tracking yields high-volume noise rather than compounded research.
- **How**: Build the database schema, logging pipelines, and classification structures before running campaign generation loops.

### 14. Humans Approve Critical Actions
- **Why**: Automated systems running on external platforms require strict containment to prevent resource exhaustion or policy violations.
- **How**: Require explicit human approval for actions such as submitting candidates or altering system permissions.

---

## 🔍 Observability & Lifecycle Tenets

### 15. Every Module Replaceable
- **Why**: Technology dependencies (such as models, databases, and APIs) evolve.
- **How**: Define clean interface abstractions so that components can be swapped without rewriting client code.

### 16. Everything Observable
- **Why**: Unobserved processes make diagnosing system failures impossible.
- **How**: Expose metrics, logging traces, and current state metrics across all modules.

### 17. Everything Traceable
- **Why**: To trust research findings, the lineage of every alpha candidate must be verifiable.
- **How**: Link every simulation variant back to its parent hypothesis, source dataset, campaign context, and generator model ID.

### 18. No Hidden State
- **Why**: Hidden static state across class instances breaks unit tests and complicates debugging.
- **How**: Maintain state explicitly within context containers passed between components.

### 19. No Magic
- **Why**: Custom meta-classes or dynamic patching reduce static type checking effectiveness.
- **How**: Write standard, typing-compliant classes and linear functions.

### 20. Everything Versioned
- **Why**: Tracking changes across software versions and data sets prevents environment drift.
- **How**: Attach explicit semantic version strings to all configurations, schemas, and specifications.
