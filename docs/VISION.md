# SYNTHRA Vision

This document details the long-term mission, strategic horizons, and quantitative success metrics for SYNTHRA.

---

## Mission Statement

The mission of SYNTHRA is to build a self-improving, fully autonomous quantitative research operating system that handles the entire lifecycle of alpha strategy development, simulation, evaluation, and selection for WorldQuant BRAIN, operating strictly within official platform parameters.

---

## Five-Year Vision

By year five, SYNTHRA aims to achieve complete hands-off operational automation for a single research node. This includes:
- **Autonomous Idea Mining**: Generating economic hypotheses based on systemic scanning of available datasets and past simulation logs, without human ideation.
- **Dynamic Expression Compilation**: Automatically mapping selected datasets and operators to syntactically correct alpha expressions (in both Fast Expression and Python formats).
- **Execution Orchestration**: Running thousands of daily backtests using the official ACE API, parsing responses, and recovering from simulation errors or timeouts.
- **Self-Correcting Feedback Loop**: Utilizing a specialized evaluation engine that analyzes failed backtests to update hypothesis-generation weights, ensuring the system continually improves its hit rate.

---

## Ten-Year Vision

By year ten, SYNTHRA aims to scale from a single node to a federated, multi-node quantitative research organization:
- **Distributed Strategy Generation**: Multiple independent instances of SYNTHRA operating across isolated nodes, specializing in different asset classes or time horizons.
- **Privacy-Preserving Knowledge Sharing**: Exchanging anonymized performance metrics, metadata, and failure classifications between nodes to compound research speed without exposing specific alpha formulas.
- **Continuous Adaptation**: Automatically detecting market regime shifts and platform validation modifications, dynamically adjusting risk parameters, and shifting strategy allocations.

---

## High-Level Goals

1.  **Eliminate the Human Bottleneck**: Move quantitative research from manual script editing to high-level system monitoring.
2.  **Ensure Strict Compliance**: Operate 100% within the rules and technical limits of the WorldQuant BRAIN APIs, avoiding any scraping or unauthorized access.
3.  **Establish High-Fidelity Memory**: Capture every dataset mapping, expression, and simulation result to build a compounding scientific database.
4.  **Maximize Portfolio Information Ratio**: Focus on the aggregate correlation profile of submitted alphas, maximizing portfolio diversification over individual strategy performance.

---

## Success Metrics

To objectively evaluate the performance of SYNTHRA, we track the following engineering and research metrics:

### 1. Research Metrics
- **Alpha Pass Rate**: The percentage of generated alpha expressions that successfully pass all official WorldQuant BRAIN checks (e.g., self-correlation, copy checks, decay, turnover).
- **Information Ratio (IR)**: The portfolio-level Information Ratio of all submitted and accepted alphas.
- **Correlation Limit**: The average pairwise correlation between new submissions and the existing alpha portfolio must remain below `0.30`.
- **Submission Velocity**: The volume of valid, non-redundant strategy submissions per research campaign.

### 2. Operational Metrics
- **Simulation Success Rate**: The percentage of API simulation requests that complete successfully without timeout, authentication, or syntax errors.
- **Feedback Cycle Latency**: The time taken (in minutes) for the system to process a simulation failure, analyze the root cause, and update the hypothesis generation parameters.
- **Data Utilization**: The percentage of available platform datasets actively incorporated into simulated strategies.

---

## What Success Looks Like

A successful deployment of SYNTHRA results in a zero-intervention research loop:
1.  The system initiates a research campaign targeting a specific market anomaly.
2.  The hypothesis engine outputs ten testable ideas, mapping them to specific datasets.
3.  The synthesizer writes, validates, and submits the expressions to the simulation client.
4.  The simulation client handles authentication, schedules requests, and collects results from the ACE API.
5.  Successful strategies are automatically cataloged and evaluated for submission; failed runs are classified and indexed in the vector store to update prompt/generation weights.
6.  The portfolio optimizer selects the best-diversified candidates for final submission.
7.  The human operator's role is strictly limited to monitoring system logs, reviewing system configurations, and approving major architectural modifications.
