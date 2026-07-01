# SYNTHRA Architecture Specification

This document defines the high-level system design of SYNTHRA. The architecture is organized around a centralized governing and planning system that orchestrates functional departments.

---

## 🗺️ System Hierarchy

In SYNTHRA, orchestration and enforcement are decoupled from functional execution. The Governor serves as the system's "CEO" (resource allocator and constraint enforcer), while the Research Planner serves as the "brain" (the centralized coordinator).

```
                    SYNTHRA

                    GOVERNOR (CEO)
                        │
                 Research Planner (Brain)
                        │
        ┌───────────────┼────────────────┐
        │               │                │
 Research Dept    Knowledge Dept   Execution Dept
        │               │                │
 Learning Dept    Portfolio Dept   Infrastructure Dept
```

---

## 🏛️ System Core

### 1. The Governor
The Governor acts as the highest authority (the "CEO") of the system. All planned actions, resource requests, and boundary checks must pass through the Governor.
- **Responsibilities**:
  - Enforces safety boundaries, rate limits, and compliance constraints defined in the [Constitution](file:///c:/Users/VANDAN/Projects/SYNTHRA/docs/CONSTITUTION.md).
  - Arbitrates resource allocation, including token budgets, API request limits, and computation time.
  - Reviews proposed backtests and denies executions that represent duplicate paths or violate campaign parameters.
  - Human-in-the-loop validation: Intercepts high-risk tasks and prompts for human review before proceeding.

### 2. The Research Planner
The Research Planner serves as the orchestrating engine (the "brain") of SYNTHRA. It sits below the Governor and coordinates all system departments.
- **Responsibilities**:
  - Receives high-level campaign configurations and generates a structured schedule of tasks.
  - Assigns sub-tasks to the Research, Knowledge, Execution, Learning, and Portfolio departments.
  - Monitors the state of active agents, tracks task dependencies, and manages the execution flow.
  - Orchestrates recovery loops when tasks fail or timeout.

---

## 🏢 Functional Departments

### 1. Research Department
- **Responsibilities**: Generates economic hypotheses and compiles them into syntactically valid alpha expressions (Fast Expression or Python formats).
- **Core Components**: Hypothesis Engine, Code Synthesizer, LLM Router.

### 2. Knowledge Department
- **Responsibilities**: Accumulates, organizes, and link-indexes research findings.
- **Core Concepts**:
  - **Research Memory**: A queryable database storing past campaign configurations, logs, and outputs.
  - **Knowledge Graph**: Maps relationships between datasets, operators, themes, and their empirical performance.
  - **Experiment Graph**: Relates hypotheses to their expression variants, simulation attempts, and outcome metadata.

### 3. Execution Department
- **Responsibilities**: Interfaces directly with external sandboxes and platforms.
- **Core Components**: Simulation Client (ACE API wrapper), Runtime Sandbox.

### 4. Learning Department
- **Responsibilities**: Analyzes successes and failures to refine campaign heuristics.
- **Core Components**: Failure Classifier.

### 5. Portfolio Department
- **Responsibilities**: Evaluates cross-strategy correlation profiles and ensures strategy diversification.
- **Core Concepts**: Portfolio Intelligence.

### 6. Infrastructure Department
- **Responsibilities**: Coordinates physical resources, file persistence, network configurations, and database connectivity.
