# SYNTHRA Agent & Department Specifications

This document defines the organizational structure of SYNTHRA's agentic systems, grouping active agents into specialized Departments and mapping them to the system core.

---

## 🏛️ System Structure

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

The System Core is responsible for global system coordination, resource allocation, and safety enforcement. It is not comprised of standard reasoning agents but of deterministic control engines:
- **Governor**: Evaluates task bounds, arbitrates token budgets, checks for duplicate strategies, and halts execution for human validation on high-risk tasks.
- **Research Planner**: Manages campaign state schedules, routes messages, spawns agents, and runs recovery flows.

---

## 🏢 Functional Departments

### 1. Research Department
The Research Department translates economic concepts into testable code.

#### Profile: Hypothesis Generator Agent
*   **Department**: Research Department
*   **Responsibilities**:
    - Review available datasets and campaign theme constraints.
    - Generate economically sound hypotheses explaining targeted market anomalies.
    - Output a structured research brief.
*   **Interfaces & Data Flow**:
    - *Inputs*: Campaign parameters, dataset metadata profiles.
    - *Outputs*: Structured research brief (economic rationale, target variables, math operators).
*   **Memory & Tools**: Read-only access to Research Memory; dataset catalog query tool.
*   **Failure Modes & Mitigations**:
    - *Failure Mode*: Generating hypotheses that cannot be translated to expressions.
      - *Mitigation*: Schema validation matching variable types.

#### Profile: Code Synthesizer Agent
*   **Department**: Research Department
*   **Responsibilities**:
    - Translate research briefs into syntactically correct expressions (Fast Expression or Python formats).
    - Perform initial AST validation on code.
*   **Interfaces & Data Flow**:
    - *Inputs*: Research brief, syntax templates, standard example libraries.
    - *Outputs*: Alpha expression code string.
*   **Memory & Tools**: Read-only template memory; local AST syntax parser.
*   **Failure Modes & Mitigations**:
    - *Failure Mode*: Generating code that violates platform syntax limits.
      - *Mitigation*: Strict grammar verification against local platform rules before output.

---

### 2. Execution Department
The Execution Department interfaces with sandboxed compilation runtimes and the external backtesting APIs.

#### Profile: Simulation Operator Agent
*   **Department**: Execution Department
*   **Responsibilities**:
    - Send expressions to the official WorldQuant BRAIN ACE API.
    - Monitor simulation status and extract raw performance statistics.
*   **Interfaces & Data Flow**:
    - *Inputs*: Alpha expression code, simulation run parameters.
    - *Outputs*: Raw performance logs and simulation metrics.
*   **Memory & Tools**: Stateless runtime; Simulation Client interface connection.
*   **Failure Modes & Mitigations**:
    - *Failure Mode*: API rate-limiting or network timeout.
      - *Mitigation*: Exponential backoff queue management.

---

### 3. Learning Department
The Learning Department refines system heuristics by analyzing operational and strategy failures.

#### Profile: Memory & Evaluation Agent
*   **Department**: Learning Department (coordinates with Knowledge Department)
*   **Responsibilities**:
    - Parse raw simulation results and code logs.
    - Classify failure modes for failed backtests.
    - Log results in the Experiment Database and vectorize error metrics.
*   **Interfaces & Data Flow**:
    - *Inputs*: Simulation performance results and raw log outputs.
    - *Outputs*: Database entry payload, vector semantic store entry.
*   **Memory & Tools**: Relational DB connector, vector DB connector, error regex parsing tool.
*   **Failure Modes & Mitigations**:
    - *Failure Mode*: Database write conflicts under parallel tasks.
      - *Mitigation*: Transaction queue logging to prevent data loss.

---

### 4. Knowledge Department
Manages the long-term compound data storage.
- **Responsibilities**: Maintains the Knowledge Graph, Experiment Graph, and Research Memory.

---

### 5. Portfolio Department
Governs correlation limits and strategy diversification.
- **Responsibilities**: Conducts cross-correlation checks and packages strategy candidates.

---

### 6. Infrastructure Department
Coordinates hardware resources, data directories, and network transport configurations.
