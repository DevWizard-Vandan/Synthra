# SYNTHRA Mental Model

This document explains how SYNTHRA reasons. It defines the logical framework and step-by-step scientific method that the system follows during all research activities.

---

## 🧠 The Reasoning Flow

SYNTHRA does not execute random searches or brute-force code generation. It reasons using a structured, progressive feedback loop:

```
                      Inquiry Phase
                     ┌──────────────┐
                     │   Question   │
                     └──────┬───────┘
                            │
                            v
                     ┌──────────────┐
                     │  Hypothesis  │
                     └──────┬───────┘
                            │
                            v
                     ┌──────────────┐
                     │   Evidence   │
                     └──────┬───────┘
                            │
                            v
                      Testing Phase
                     ┌──────────────┐
                     │  Experiment  │
                     └──────┬───────┘
                            │
                            v
                     ┌──────────────┐
                     │ Observation  │
                     └──────┬───────┘
                            │
                            v
                      Learning Phase
                     ┌──────────────┐
                     │   Learning   │
                     └──────┬───────┘
                            │
                            v
                     ┌──────────────┐
                     │  Knowledge   │ (Primary System Product)
                     └──────────────┘
```

---

## 🔎 Phases of Reasoning

### 1. Inquiry Phase: Establishing Rationale
*   **Question**: The starting point of any research cycle. It defines the target anomaly or relationship we want to investigate (e.g., *"Does short-term fundamental sentiment predict asset price movement in liquid European equities?"*).
*   **Hypothesis**: The formal economic statement answering the Question. It posits a specific economic mechanism and predicts a relationship between datasets (e.g., *"An increase in research and development expenditure relative to historical industry means predicts positive asset returns because it represents slow information diffusion of future productivity gains"*).
*   **Evidence**: The retrieval of pre-existing data. This includes platform dataset schemas, operator metadata, and past experiment records retrieved from the Knowledge Graph to verify that the hypothesis is statistically testable and distinct.

### 2. Testing Phase: Empirical Validation
*   **Experiment**: The translation of the Hypothesis into machine-readable code (alpha expressions) followed by backtest execution through the ACE API.
*   **Observation**: The objective, empirical output of the Experiment. This includes quantitative performance metrics (Sharpe ratio, turnover, fitness, margin) and logging messages (stdout, stderr, syntax warnings).

### 3. Learning Phase: Compounding Knowledge
*   **Learning**: The critical step of retrospective evaluation.
    - If the experiment **failed** to compile or meet correlation thresholds, the system classifies the failure (e.g., high self-correlation, syntax error) and indexes it.
    - If the experiment **succeeded**, the system maps the successful variables and operator structures.
*   **Knowledge**: The integration of learnings back into the database. The system updates the Knowledge Graph and Experiment Graph, modifying the probability weights for future campaigns. Alphas are valuable byproducts of this knowledge-compounding loop.
