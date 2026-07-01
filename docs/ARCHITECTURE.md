# SYNTHRA Architecture Specification

This document defines the high-level layered architecture of SYNTHRA. The design enforces separation of concerns through decoupled layers, ensuring the system remains implementation-agnostic.

---

## 🏛️ Layered Architecture

SYNTHRA is structured into eight architectural layers. Each layer is defined by its operational responsibilities and communicates with adjacent layers through strict boundaries.

```
+---------------------------------------------------------------+
|                       PRESENTATION LAYER                      |
|                  User Interfaces  •  CLI  •  APIs             |
+---------------------------------------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                        PLANNING LAYER                         |
|                    Campaigns  •  Task Router                  |
+---------------------------------------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                        RESEARCH LAYER                         |
|            Hypotheses  •  Quantitative Ideation               |
+---------------------------------------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                        REASONING LAYER                        |
|            Models Routing  •  Grammar & Validation            |
+---------------------------------------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                        KNOWLEDGE LAYER                        |
|           Memory  •  Graphs  •  Portfolio Intelligence        |
+---------------------------------------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                         LEARNING LAYER                        |
|              Evaluation  •  Failure Classifiers               |
+---------------------------------------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                       EXECUTION LAYER                         |
|             Simulation Client  •  Sandbox Runtimes            |
+---------------------------------------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                     INFRASTRUCTURE LAYER                      |
|             Hardware  •  Storage  •  Network Drivers          |
+---------------------------------------------------------------+
```

---

## 🧩 Layer Responsibilities

### 1. Presentation Layer
- **Responsibilities**: Governs external interactions with human operators. Captures user inputs, presents research campaign statuses, outputs strategy candidates for review, and handles authorization views.
- **Constraints**: Contains no business logic, research algorithms, or direct execution capabilities.

### 2. Planning Layer
- **Responsibilities**: Structures research actions into campaigns. It manages the campaign execution order, schedules sub-tasks, and routes messages between reasoning agents.
- **Core Component - Planner**: Generates execution schedules based on active campaign objectives. Tracks task dependencies, resolves execution bottlenecks, and handles error-recovery loops.
- **Core Component - Governor**: Enforces system constraints, safety guardrails, and compliance regulations. Validates actions proposed by planning and execution units, preventing out-of-bounds operations.

### 3. Research Layer
- **Responsibilities**: Focuses on quantitative ideation and hypothesis building. It structures research around systematic campaigns rather than isolated alpha generation.
- **Concept - Research Campaigns**: All research operations are grouped into campaigns. A campaign defines the parameters of study, including target assets, geographical regions, economic anomalies, and dataset boundaries.
- **Core Component - Hypothesis Engine**: Synthesizes data metadata and past research findings into specific, testable economic hypotheses.

### 4. Reasoning Layer
- **Responsibilities**: Manages cognitive task routing and syntactic validation.
- **Core Component - LLM Router**: Evaluates task complexity, token limits, and cost profiles to select the most appropriate language model or reasoning engine for a given task.
- **Core Component - Synthesizer**: Translates verbal economic rationale into structured expressions using strict grammatical templates.

### 5. Knowledge Layer
- **Responsibilities**: Accumulates, index-links, and retrieves the mathematical and economic findings generated by the system.
- **Concept - Research Memory**: A stateful repository storing historical performance data, context embeddings, and campaign results.
- **Concept - Knowledge Graph**: Maps relationships between datasets, mathematical operators, economic themes, and their joint performance.
- **Concept - Experiment Graph**: Tracks the lineage of every strategy generated. Connects the parent hypothesis, synthesized expression variants, simulation attempts, and classification codes in a traceable tree structure.
- **Concept - Portfolio Intelligence**: Evaluates the relationship between individual strategies and the active strategy portfolio. Calculates cross-correlation profiles and assesses information ratio contributions.

### 6. Learning Layer
- **Responsibilities**: Updates system intelligence from empirical successes and failures.
- **Core Component - Failure Classifier**: Analyzes simulation failures (e.g., compile issues, high self-correlation, syntax warnings). Categorizes them into structured failure profiles and updates the Knowledge Layer to prevent duplicate invalid attempts.

### 7. Execution Layer
- **Responsibilities**: Interfaces directly with platforms and external sandboxes.
- **Core Component - Simulation Client**: Manages queues, handles authorization tokens, rate limits, and interfaces with the target backtesting APIs.
- **Core Component - Runtime Sandbox**: Confines all code compilation and execution to isolated, permission-bounded runtimes.

### 8. Infrastructure Layer
- **Responsibilities**: Manages physical or virtual system resources. Coordinates data persistence, network interfaces, filesystem access, and hardware compute tasks.
