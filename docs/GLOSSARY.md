# SYNTHRA Glossary

This document provides concise definitions for essential WorldQuant BRAIN and SYNTHRA terms used throughout the codebase and documentation.

---

## 🌍 WorldQuant BRAIN Concepts

- **Alpha**: A mathematical expression or algorithm designed to predict price movements of assets and generate risk-adjusted returns.
- **ACE (Alpha Calculation Engine)**: The official WorldQuant backtesting and simulation platform accessed via the API.
- **Fast Expression**: A single-line mathematical formula using platform-defined operators (e.g., `ts_mean`, `rank`) to represent alpha logic.
- **Python Alpha**: An alpha strategy implemented as a multi-line Python function conforming to the official template, allowing custom logic and pandas operations.
- **Sharpe Ratio**: A metric representing the risk-adjusted return of an alpha, calculated as average return divided by volatility.
- **Fitness**: A composite platform metric evaluating alpha quality, combining Sharpe ratio, turnover, and margin.
- **Turnover**: The rate at which the alpha portfolio changes its asset holdings, representing the transaction volume.
- **Margin**: The ratio of expected book returns to total transaction volume.
- **Delay**: The time lag between the collection of data and the execution of trades based on that data (e.g., Delay 1, Delay 2).
- **Neutralization**: A statistical adjustment subtracting market, industry, or sub-industry averages from alpha values to isolate idiosyncratic returns.
- **Decay**: The rate at which an alpha's predictive power and returns degrade over time.
- **Coverage**: The percentage of assets in the target universe for which the alpha generates non-zero predictions.

---

## 🤖 SYNTHRA Architecture Concepts

- **Campaign**: A structured research initiative bounded by asset universe, region, holding period, and economic theme (rather than isolated alpha generation).
- **Hypothesis**: A structured document defining an economic rationale explaining why a specific relationship should yield alpha.
- **Experiment**: A single backtest execution mapping to a hypothesis, generating specific logs and performance metrics.
- **Research Memory**: A persistence system caching historical campaign parameters, simulation logs, and performance metrics.
- **Knowledge Graph**: A conceptual representation linking datasets, mathematical operators, economic themes, and their empirical performance.
- **Experiment Graph**: A parent-child relational tree tracking the lineage of hypotheses, expression variations, and backtest results.
- **Portfolio Intelligence**: The layer that evaluates cross-strategy correlation, information ratio contribution, and overall portfolio diversification.
- **Planner**: The planning layer scheduler that coordinates campaign execution schedules and monitors agent workloads.
- **Governor**: The compliance module that validates proposed agent actions against security boundaries and rate limits.
- **LLM Router**: A reasoning utility that selects the optimal LLM size, context limit, and cost profile for a given agent task.
- **Department**: A high-level organizational structure grouping related agents (e.g., Research Department, Execution Department).
- **Agent**: A modular, single-responsibility AI actor executing tasks inside a department.
- **ADR (Architecture Decision Record)**: A document capturing a design choice, its context, and its trade-offs.
- **RFC (Request for Comments)**: A proposal detailing a new feature or design specification, circulated for review before writing code.
- **Specification**: A document detailing the precise technical requirements and interface designs for a system component.
