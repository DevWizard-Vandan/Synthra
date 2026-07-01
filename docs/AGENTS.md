# SYNTHRA Agent Specifications

This document defines the roles, input-output schemas, communication channels, memory structures, tools, failure states, and success criteria for all active agents in SYNTHRA.

---

## 🤖 Agent Specifications

### 1. Hypothesis Generator Agent

#### Responsibilities
- Systematically review available platform datasets and metadata.
- Retrieve past campaign results and performance profiles.
- Generate testable economic hypotheses.
- Output a detailed research brief detailing the target datasets, mathematical operations, and execution logic.

#### Interfaces & Data Flow
- **Inputs**: 
  - Campaign parameters (region, holding period, universe constraints).
  - Platform dataset catalog metadata (data fields, descriptions, frequencies).
  - Relevant vector search results from historical successful and failed strategies.
- **Outputs**:
  - Structured research brief containing:
    - Verifiable economic hypothesis.
    - List of targeted datasets.
    - Proposed mathematical operators.
    - Rationale for expected predictability.

#### Capabilities & Integrations
- **Memory**: Vector Semantic Store (read-only) to query past experiments.
- **Tools**: Dataset catalog parser.
- **Communication**: Receives task instructions from the Agent Coordinator; sends research briefs to the Code Synthesizer.

#### Failure Modes & Mitigations
- *Failure Mode*: Generating mathematically complex but economically meaningless hypotheses.
  - *Mitigation*: Hard-coded constraints forcing the agent to map the hypothesis to a specific list of core economic variables (e.g., value, momentum, growth, liquidity).
- *Failure Mode*: Proposing datasets or operators that do not exist or are unavailable for the target region.
  - *Mitigation*: Schema validation against the platform dataset registry before final output.

#### Success Criteria
- The research brief maps to available datasets and operators.
- The hypothesis is classified as unique (less than `0.30` semantic similarity to existing hypotheses).

---

### 2. Code Synthesizer Agent

#### Responsibilities
- Translate the economic logic from a research brief into valid alpha expressions.
- Synthesize code in both WorldQuant BRAIN Fast Expression format and Python script format.
- Perform basic syntax checking.

#### Interfaces & Data Flow
- **Inputs**:
  - Research brief from the Hypothesis Generator.
  - Coding standards specification.
  - Syntax templates and examples of successful expressions.
- **Outputs**:
  - Alpha expression code block (Fast Expression string or Python function code).
  - Verification checklist demonstrating syntactic alignment.

#### Capabilities & Integrations
- **Memory**: Local code template database (read-only).
- **Tools**: Local syntax checker, AST (Abstract Syntax Tree) validator.
- **Communication**: Receives briefs from the Hypothesis Generator; sends code blocks to the Simulation Operator.

#### Failure Modes & Mitigations
- *Failure Mode*: Generating syntax errors (e.g., mismatched parentheses, invalid operator naming).
  - *Mitigation*: Local AST parsing and evaluation against the platform's operator grammar rules prior to transmission.
- *Failure Mode*: Hallucinating non-existent datasets or functions.
  - *Mitigation*: Code-generation prompts restricted by strict schema definitions.

#### Success Criteria
- Synthesized code passes local syntax checks and AST validations with zero errors.

---

### 3. Simulation Operator Agent

#### Responsibilities
- Intermediary between the code synthesis and the WorldQuant BRAIN execution engine.
- Format inputs, send requests to the Simulation Client, monitor backtest status, and parse the raw performance payload.

#### Interfaces & Data Flow
- **Inputs**:
  - Alpha expression code block.
  - Backtest parameters (region, universe, delay).
- **Outputs**:
  - Structured simulation results (Sharpe ratio, turnover, fitness, margin, drawdowns).
  - Raw stdout/stderr log output.

#### Capabilities & Integrations
- **Memory**: None (stateless runtime).
- **Tools**: Simulation Client connection wrapper.
- **Communication**: Receives code blocks from the Code Synthesizer; sends simulation records to the Memory & Evaluation Agent.

#### Failure Modes & Mitigations
- *Failure Mode*: Network timeout or API throttling.
  - *Mitigation*: Implemented exponential backoff and retry queues in the Simulation Client.
- *Failure Mode*: Infinite loop or hanging backtest.
  - *Mitigation*: Enforce timeout thresholds (e.g., maximum 300 seconds per simulation).

#### Success Criteria
- Receives a terminal response (success or failure log) from the ACE API.
- Correctly parses the performance payload.

---

### 4. Memory & Evaluation Agent

#### Responsibilities
- Parse, classify, and persist research outcomes.
- Analyze failed simulations to identify root causes.
- Write records to the Experiment Database and vectorize logs for the Semantic Store.

#### Interfaces & Data Flow
- **Inputs**:
  - Structured simulation results and logs.
  - Original research brief and expression code.
- **Outputs**:
  - Relational database record entry.
  - Semantic vector payload.
  - Summary report for the Agent Coordinator.

#### Capabilities & Integrations
- **Memory**: Relational Experiment Database (write-only), Vector Semantic Store (write-only).
- **Tools**: Vector embedding generator, error classification heuristics.
- **Communication**: Receives simulation records from the Simulation Operator; updates system memory; notifies the Agent Coordinator of completion.

#### Failure Modes & Mitigations
- *Failure Mode*: Database write lock or transaction failure.
  - *Mitigation*: Transaction logs written to temporary local files to prevent data loss.
- *Failure Mode*: Incorrect classification of errors (e.g., classifying a platform issue as a syntax error).
  - *Mitigation*: Strict regex pattern matching on official API error codes.

#### Success Criteria
- The database record is successfully written.
- The vector embedding is generated and stored.
- The Hypothesis Generator's prompt weights are updated.
