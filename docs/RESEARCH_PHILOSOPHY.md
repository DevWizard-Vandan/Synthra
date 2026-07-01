# SYNTHRA Research Philosophy

This document defines the quantitative research principles, methodology, and scientific frameworks guiding SYNTHRA.

---

## 🔬 The Scientific Method in Quantitative Finance

SYNTHRA treats quantitative research as an empirical science. Strategy development must follow the formal stages of the scientific method:

```
+---------------------------------------------------------------+
|                       ECONOMIC RATIONALE                      |
|            Observation of Market Inefficiency or Regime       |
+---------------------------------------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                      HYPOTHESIS FORMULATION                   |
|          "Variable X predicts Variable Y because..."          |
+---------------------------------------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                      EXPRESSION SYNTHESIS                     |
|           Translate Hypothesis into Mathematical Code         |
+---------------------------------------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                      EMPIRICAL TESTING                        |
|            ACE Simulation Backtest & Result Collection        |
+---------------------------------------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                      EVALUATION & LEARNING                    |
|             Analyze Result  •  Refine Base Hypothesis         |
+---------------------------------------------------------------+
```

---

## 💡 Economic Hypotheses Over Brute Force

A core principle of SYNTHRA is that economic reasoning must precede the writing of mathematical expressions. The platform rejects brute-force random mutations of mathematical symbols. 
- Every alpha generated must map to a logical hypothesis explaining *why* the strategy should capture premium or structural market inefficiency.
- Categories of acceptable economic rationales:
  - **Value**: Discrepancies between market pricing and fundamental value metrics.
  - **Momentum / Trend Following**: Persistence of price direction driven by behavioral biases or slow information diffusion.
  - **Reversion**: Overreaction anomalies returning to long-term equilibrium.
  - **Information Flow / Sentiment**: Market reactions to fundamental reports, announcements, or regulatory filings.

---

## 📂 Research Campaigns

Quantitative research is organized into structured **Campaigns**. A campaign is defined by:
- **Target Universe**: The asset group under study (e.g., specific liquid equity regions).
- **Time Horizon**: The target holding period of the strategies (e.g., daily, weekly).
- **Theme Constraints**: The economic theme (e.g., "Liquidity anomalies in emerging markets").
- **Dataset Boundaries**: A strict list of available datasets that are mapped to the campaign to focus agent synthesis.

By structuring research into campaigns, SYNTHRA avoids scattershot simulations and gathers concentrated datasets regarding target anomaly domains.

---

## 🧠 Compounding Knowledge: Learning from Failure

In quantitative research, more than 90% of initial simulations fail to meet performance thresholds. SYNTHRA views these failures as high-value data points.
- Every failed simulation must be classified by its primary failure mode:
  - **Syntax / Validation Failures**: Code failed compile checks.
  - **High Decay / Turnover**: Strategy generates excessive transaction costs.
  - **High Self-Correlation**: Strategy duplicates returns of existing submissions.
  - **Low Information Ratio**: Strategy lacks statistical significance.
- The details of these failures (hypothesis, code, error codes, performance logs) are stored in the vector store and relational database. Before generating new alphas, the system performs a vector lookup of this data to prune unviable hypothesis branches.

---

## 💼 Portfolio Thinking

SYNTHRA evaluates strategy success at the portfolio level, not in isolation.
- **Uncorrelated Submissions**: An alpha candidate with a Sharpe ratio of `1.5` that has zero correlation to the active portfolio is significantly more valuable than an alpha with a Sharpe of `2.5` that is `0.80` correlated.
- **Diversification Constraints**: The selection layer tracks the pairwise correlation matrix of all simulated strategies. Only strategies that meet the correlation threshold (e.g., maximum `0.30` pairwise correlation) are approved for submission.
- **Decay Tracking**: Strategies are monitored over time. If a strategy's information ratio degrades or decay accelerates, the memory layer updates to reduce generation weights for that strategy's parameters.
