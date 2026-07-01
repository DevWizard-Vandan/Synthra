# SYNTHRA

SYNTHRA is an autonomous quantitative research operating system designed to automate the end-to-end lifecycle of quantitative strategy development (alphas) for the WorldQuant BRAIN platform. The system operates exclusively within the boundaries of official WorldQuant BRAIN APIs and platform capabilities.

---

## Why SYNTHRA Exists

Quantitative research on modern platforms is often constrained by human bottlenecks in hypothesis generation, translation of ideas into code, and structured evaluation. While previous tools like QuantForge focused on automated alpha generation, they lacked a unified, stateful architecture to manage the entire scientific loop. 

SYNTHRA is built to resolve these limitations by treating the research process as a closed-loop engineering system. Rather than generating high-volume, random mathematical expressions, SYNTHRA structures research around economic rationale, systematic backtesting, and persistent memory accumulation. It is designed to act as an autonomous research organization that compounds knowledge from both successful and failed simulations.

---

## Long-Term Vision

The five-year objective for SYNTHRA is to achieve fully autonomous, self-directed quantitative research. This means the system will independently generate viable economic hypotheses, map them to appropriate datasets, construct expressions, run simulations, evaluate portfolios, and submit diversified candidates to WorldQuant BRAIN without human intervention.

In the ten-year horizon, SYNTHRA aims to evolve into a decentralized network of specialized research nodes that collaborate, share learnings via privacy-preserving federated memory, and continuously adapt to platform regime shifts.

---

## Project Goals

1.  **Closed-Loop Automation**: Automate idea discovery, dataset mapping, expression synthesis, simulation execution, and result analysis.
2.  **Rigor Over Scale**: Prioritize high-quality, economically sound hypotheses over brute-force mathematical mutations.
3.  **Knowledge Compounding**: Build a structured, queryable research database that logs every experiment, ensuring the system does not repeat failures and continuously optimizes parameters.
4.  **Portfolio Diversification**: Focus on submitting low-correlation alphas to build robust, multi-strategy portfolios rather than single high-performing outliers.

---

## High-Level Architecture

SYNTHRA is structured as a decoupled, layered system to maintain separation of concerns and facilitate modular replacements:

*   **Orchestration Layer**: Manages execution state, schedules research campaigns, and coordinates specialized agents.
*   **Knowledge & Memory Layer**: Logs historical experiments, maintains correlation matrices, and indexes past alpha performances to prevent redundant research.
*   **Execution Layer**: Directly interfaces with the official WorldQuant BRAIN APIs (such as the Simulation and Data APIs) inside a sandboxed environment.
*   **Learning & Evaluation Layer**: Analyzes simulation failures, updates hypothesis generation parameters, and optimizes alpha selection algorithms based on empirical results.

---

## Repository Structure

```
SYNTHRA/
├── README.md                 # Project introduction and design summary
├── CLAUDE.md                 # Agent operating manual and coding instructions
└── docs/
    ├── VISION.md             # Multi-year strategic goals and success metrics
    ├── CONSTITUTION.md       # Safety boundaries, core tenets, and non-goals
    ├── ARCHITECTURE.md       # High-level component design and interaction layers
    ├── ROADMAP.md            # Realistic milestones and release timeline
    ├── AGENTS.md             # Detailed profiles, tools, and failure states of AI agents
    ├── CODING_STANDARDS.md   # Formatting, testing, and pull request requirements
    ├── RESEARCH_PHILOSOPHY.md # Scientific method and quantitative principles
    └── DECISIONS.md          # Architecture Decision Records (ADR) log
```

---

## Development Philosophy

The development of SYNTHRA is guided by strict software engineering principles:
*   **Architecture First**: System design and interface specifications must be fully documented before code is written.
*   **Modularity**: Every module must have a single responsibility. Any component (including the underlying LLM, database, or simulation wrapper) should be replaceable without affecting the rest of the system.
*   **Empirical Decisions**: We prioritize empirical performance data and logical proof over assumptions.

---

## Current Development Status

The project is currently in the **Architecture & Planning Phase (Milestone 0)**. The repository contains the core specifications, design frameworks, and standard operating procedures. Implementation of the core simulation interfaces and the orchestration bus is scheduled for the next phase.
