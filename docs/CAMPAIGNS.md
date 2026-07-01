# SYNTHRA Campaigns Spec

This document defines the Campaign lifecycle within SYNTHRA. In SYNTHRA, all research tasks are organized under a centralized Campaign object, ensuring all code, simulations, and outcomes are contextualized.

---

## 🏛️ The Campaign Hierarchy

In SYNTHRA, single alphas or isolated backtests do not exist in a vacuum. Everything belongs to a Campaign. The campaign governs the operational scope, parameter boundaries, and evaluation criteria.

```
                         CAMPAIGN
                            │
                            v
                         Question
                            │
                            v
                        Hypothesis
                            │
                            v
                        Datasets
                            │
                            v
                        Operators
                            │
                            v
                        Variants
                            │
                            v
                       Simulations
                            │
                            v
                        Learning
                            │
                            v
                       Conclusion
```

---

## 🔄 Campaign Lifecycle Phases

### 1. Campaign Initialization
- **Action**: The user or planning core defines a Campaign scope.
- **Parameters**: Specifies the geographic region (e.g., US, EU), liquid asset universe, target holding period (delay parameters), and an economic theme.
- **Objective**: Establish the bounds within which the system is authorized to run tests.

### 2. Inquiry Formulation (Question & Hypothesis)
- **Question**: The Research Department formulates specific scientific inquiries matching the campaign theme.
- **Hypothesis**: The system generates testable economic statements explaining the target relationship.

### 3. Data & Operator Mapping (Datasets & Operators)
- **Datasets**: The system selects specific fields from the platform catalog that represent the variables in the Hypothesis.
- **Operators**: The system filters the platform operator set, selecting mathematical and statistical transformations matching the hypothesis structure.

### 4. Strategy Generation & Execution (Variants & Simulations)
- **Variants**: The synthesizer compiles multiple code variations (expressions) representing different combinations of variables, decay rates, and normalization parameters.
- **Simulations**: The execution layer schedules backtests for all variants via the ACE API and collects raw outcomes.

### 5. Learning & Retrospective (Learning & Conclusion)
- **Learning**: The learning department evaluates all simulation outputs, grouping errors, compiling correlations, and updating the Knowledge Graph.
- **Conclusion**: The campaign terminates when the predefined budget (token limit, simulation count, or time) is exhausted. The system outputs a campaign conclusion report summarizing the knowledge gained and preparing strategy candidates for human review.
