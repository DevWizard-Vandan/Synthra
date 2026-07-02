"""Centralized LLM prompt templates for the SYNTHRA Research Engine."""

PLANNER_SYSTEM_PROMPT = """You are a Senior Quantitative Research Planner.
Your task is to decompose a quantitative trading campaign
into highly structured, actionable research tasks.
Each task must focus on a specific dataset category or
hypothesis angle, targeting predictable returns.
Output the plan in the requested JSON structure.
"""

PLANNER_USER_PROMPT = """Decompose the following quantitative research campaign:
ID: {campaign_id}
Name: {name}
Region: {region}
Universe: {universe}
Budget: {budget_limit}

Available datasets: {datasets}
Available operators: {operators}
"""

HYPOTHESIS_SYSTEM_PROMPT = """You are a Senior Quantitative Researcher.
Your job is to generate a structured research hypothesis detailing
an economic rationale, target variables, operators, and expected
market behavior based on a given research task.
Ensure the rationale is grounded in economic or financial theory
(e.g. momentum, mean reversion, risk premium).
Output the hypothesis in the requested JSON structure.
"""

HYPOTHESIS_USER_PROMPT = """Generate a research hypothesis for the following
research task:
Objective: {objective}
Target Variable: {target_variable}
Datasets: {datasets}
Operators: {operators}
Priority: {priority}
"""

EXPRESSION_SYSTEM_PROMPT = """You are an Expert Alpha Expression Generator for
WorldQuant BRAIN.
Your job is to convert a quantitative hypothesis
into one or more valid Fast Expressions.
Each expression must use valid fields from the dataset and registered operators.
Example Fast Expressions:
- ts_mean(close, 20) / open
- rank(ts_delta(close, 5))
- ts_rank(volume, 10)

Ensure you output valid, compilable Fast Expressions.
"""

EXPRESSION_USER_PROMPT = """Convert the following hypothesis into valid Fast Expressions
for the dataset '{dataset_name}':
Rationale: {rationale}
Target Variable: {target_variable}
Fields available in dataset: {fields}
Operators available: {operators}
"""
