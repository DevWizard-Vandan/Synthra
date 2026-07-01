# SYNTHRA Architecture Specification

This document defines the high-level architecture of SYNTHRA. The architecture enforces separation of concerns across decoupled functional layers.

---

## 🗺️ System Overview

SYNTHRA is divided into four distinct operational layers. Communication between these layers is managed asynchronously through strict message contracts.

```
+---------------------------------------------------------------+
|                       ORCHESTRATION LAYER                     |
|           Campaign Scheduler  •  Agent Coordinator            |
+---------------------------------------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                       KNOWLEDGE & STORAGE                     |
|          Experiment Database  •  Vector Semantic Store         |
+---------------------------------------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                        LEARNING LAYER                         |
|         Hypothesis Engine  •  Failure Classifier               |
+---------------------------------------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                       EXECUTION ENVIRONMENT                   |
|        Sandboxed File System  •  Simulation Client            |
+---------------------------------------------------------------+
```

---

## 🏛️ Functional Layers

### 1. Orchestration Layer
The entry point of the system. It governs the execution state and controls the scheduling of research campaigns.
- **Campaign Scheduler**: Defines the parameters of a research campaign (e.g., target region, asset universe, holding periods, and target datasets).
- **Agent Coordinator**: Spawns specialized agents, manages task assignments, monitors agent status, and resolves pipeline blocks.

### 2. Knowledge & Storage Layer
Maintains the cumulative state of all research conducted by SYNTHRA.
- **Experiment Database**: A relational database logging every alpha expression generated, parameters used, simulation performance metrics (Sharpe, turnover, fitness), and submission outcomes.
- **Vector Semantic Store**: Stores semantic embeddings of successful coding patterns and detailed logs of simulation failures. This layer allows agents to perform contextual lookups to retrieve relevant history before starting a new task.

### 3. Learning Layer
Analyzes empirical data from the Execution Environment to refine research strategies.
- **Hypothesis Engine**: Integrates economic reasoning with platform parameters. It maps available datasets to economic themes, outputting testable strategy briefs.
- **Failure Classifier**: Analyzes stderr logs, compiler issues, and simulation performance errors. It classifies failures (e.g., syntax, correlation, decay) and updates weights to ensure the Hypothesis Engine avoids duplicate failure pathways.

### 4. Execution Environment
Interfaces with external environments and APIs under strict sandboxing protocols.
- **Simulation Client**: Manages authentication, rate limits, request queues, and connection timeouts with the official WorldQuant BRAIN ACE API.
- **File System Sandbox**: Confines all file creation, reading, and editing to a designated workspace directory. It blocks agents from accessing system configuration directories or environment variables.

---

## 🤖 Agent Overview

AI agents in SYNTHRA are specialized modules designed to execute a single task class. They do not maintain system state; they receive input parameters, perform their role, and return structured outputs.

- **Hypothesis Generator**: Receives dataset descriptions and historical performance logs. Outputs a structured PDF/text document containing an economic rationale and a list of target operators.
- **Code Synthesizer**: Receives the hypothesis brief. Translates the economic logic into syntactically correct code (Fast Expression or Python formats).
- **Simulation Operator**: Receives the code. Sends requests to the Simulation Client, monitors execution status, and extracts the performance payload.
- **Memory & Evaluation Agent**: Receives raw simulation results and code. Classifies any errors, writes structured metadata, and updates the databases.

---

## 🔮 Future Expansion

The architecture is designed to accommodate the following future extensions:
1.  **Multi-Node Federation**: The Storage and Knowledge layers can be modified to sync with remote instances using secure APIs, allowing collaborative research.
2.  **Adaptive LLM Routing**: The Orchestration layer can dynamically route tasks to different language models based on complexity and cost profile.
3.  **Alternative Simulation Backends**: The Simulation Client interface is abstracted, allowing local backtesting engines to be integrated alongside the official ACE API if needed.
