# SYNTHRA Agent & Department Specifications

This document defines the organizational structure of SYNTHRA's agentic systems, grouping active agents into specialized Departments to maintain separation of concerns and clear functional boundaries.

---

## 🏛️ Departmental Structure

Agents do not operate in a flat list. To coordinate complex campaigns, agents belong to specialized Departments. Communication between departments is managed through formal interfaces, and access to tools is governed at the department level.

```
                  +--------------------------------+
                  |      PLANNING DEPARTMENT       |
                  |  Task scheduling and governing |
                  +--------------------------------+
                                  |
            +---------------------+---------------------+
            |                     |                     |
+----------------------+ +------------------+ +-------------------+
|  RESEARCH DEPT       | |  KNOWLEDGE DEPT  | |  EXECUTION DEPT   |
|  Hypotheses and code | |  Graphs & memory | |  Simulations      |
+----------------------+ +------------------+ +-------------------+
            |                     |                     |
            +---------------------+---------------------+
                                  |
                        +------------------+
                        |  LEARNING DEPT   |
                        |  Failure analysis|
                        +------------------+
```

---

## 🏢 Departments & Agent Profiles

### 1. Planning Department
The Planning Department coordinates system activity, schedules campaign tasks, and monitors system safety.
- **Responsibilities**: Generates execution schedules, monitors agent dependencies, and blocks operations that violate system constraints.
- **Governing Concepts**: Planner, Governor.

---

### 2. Research Department
The Research Department translates economic concepts into testable code.
- **Responsibilities**: Formulates economic hypotheses based on campaign parameters and compiles them into syntactically valid alpha expressions.

#### Profile: Hypothesis Generator Agent
*   **Department**: Research Department
*   **Responsibilities**:
    - Review available datasets and metadata boundaries.
    - Generate economically sound hypotheses based on campaign themes.
    - Output a structured research brief detailing the target variables and operators.
*   **Interfaces & Data Flow**:
    - *Inputs*: Campaign parameters, dataset metadata profiles.
    - *Outputs*: Structured research brief (economic rationale, target variables, math operators).
*   **Memory & Tools**: Read-only access to Research Memory; dataset catalog query tool.
*   **Failure Modes & Mitigations**:
    - *Failure Mode*: Generating hypotheses that cannot be translated to expressions.
      - *Mitigation*: Hard-coded schema templates enforcing variable mapping.

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

### 3. Execution Department
The Execution Department interfaces with sandboxed compilation runtimes and the external backtesting APIs.
- **Responsibilities**: Manages API calls, authentication sessions, connection queues, and timeout recovery.

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

### 4. Knowledge Department
The Knowledge Department manages data persistence, links experiments, and evaluates portfolio fit.
- **Responsibilities**: Updates the Knowledge Graph and Experiment Graph, manages historical logs, and computes cross-strategy correlation metrics.
- **Governing Concepts**: Knowledge Graph, Experiment Graph, Research Memory, Portfolio Intelligence.

---

### 5. Learning Department
The Learning Department refines system heuristics by analyzing operational and strategy failures.
- **Responsibilities**: Evaluates simulation errors, classifies failure causes, and updates hypothesis generation weights.

#### Profile: Memory & Evaluation Agent
*   **Department**: Learning & Knowledge Departments (Joint/Cross-departmental role)
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

### 6. Portfolio Department
The Portfolio Department ensures strategy diversification.
- **Responsibilities**: Reviews successful alpha candidates, runs cross-correlation analysis, and structures candidates into a unified portfolio representation.
- **Governing Concepts**: Portfolio Intelligence.
