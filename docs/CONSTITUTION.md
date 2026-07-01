# SYNTHRA Constitution

This Constitution defines the foundational constraints, principles, and boundaries governing SYNTHRA. It is the primary reference for all architectural, coding, and research decisions.

---

## 🏛️ Core Principles

### Principle Zero: Research Before Implementation
Software exists to enable research. All engineering and system decisions must ultimately serve to improve quantitative research quality, reproducibility, and rigor. Whenever engineering convenience, library constraints, or development speed conflict with research rigor, research rigor wins.

---

### 1. Project Principles
- **Compliance First**: SYNTHRA must operate strictly within the boundaries of official WorldQuant BRAIN platform APIs. Any action that bypasses authorization, scrapers, or violates the platform's terms of service is prohibited.
- **Knowledge Compounding**: The primary product of SYNTHRA is **Knowledge**, which is organized, search-indexed, and stored in a compounding database. Alphas are valuable byproducts of this knowledge generation process.
- **Retrospective Value**: No simulation run is wasted. The system must capture, classify, and index every failure and success to improve future operations.

### 2. Engineering Principles
- **Architecture First**: Do not write code without a documented design. Architectural diagrams and interfaces must precede implementation.
- **Simplicity Over Cleverness**: Code must be explicit and readable. Avoid dynamic logic, complex meta-programming, or abstract patterns that hinder static code analysis.
- **Modularity**: Every module must have a single, isolated responsibility. All external interfaces (such as databases, LLM APIs, and simulation runtimes) must be modular and replaceable.

### 3. Research Principles
- **Hypothesis-Driven Experimentation**: Every experiment must answer a research question. Experiments should exist solely to validate or invalidate a specific economic hypothesis. Generating or mutating expressions without a clear research objective is prohibited.
- **Economic Reason First**: The system must establish a clear economic hypothesis before writing mathematical expressions. Brute-force mutations of expressions without underlying financial logic are prohibited.
- **Portfolio Focus**: We optimize for portfolio diversification and low correlation, not individual alpha outperformance. A mediocre strategy that is uncorrelated to the existing portfolio is more valuable than a high-performing strategy that duplicates existing risk exposures.

### 4. Documentation Principles
- **Documentation Integrity**: Maintain precise and up-to-date documentation. Code changes and documentation updates must occur in the same pull request.
- **Technical Rigor**: Avoid marketing language, buzzwords, and vague descriptions. Write with engineering clarity.

### 5. AI & Agent Principles
- **Human-in-the-Loop Safeguards**: High-risk operations (such as making final submission calls or changing core security parameters) require explicit human approval.
- **Least Privilege**: Active agents must operate within strict sandboxes with bounded directory access, rate limits, and network firewalls.

### 6. Coding Principles
- **Strict Typing**: All code must use strict type hints.
- **Comprehensive Testing**: Write unit tests for all public classes and functions. Maintain high coverage. Do not commit untested code.

### 7. Decision Principles
- **Documented Rationale**: Every architectural pivot, dependency addition, or structural change must be logged as an Architecture Decision Record (ADR) in the [adr directory](file:///c:/Users/VANDAN/Projects/SYNTHRA/docs/adr/).

---

## 🚫 Non-Goals: What SYNTHRA Will Never Become

To maintain focus and system integrity, we explicitly list the boundaries of what SYNTHRA will **not** do:

1.  **Real-Money Execution Platform**: SYNTHRA is designed solely for quantitative research, backtesting, and candidate submission within the WorldQuant BRAIN simulation environment. It will never connect to live brokerages, execute real-money trades, or manage live portfolios.
2.  **Generic AI Chatbot/Copilot**: SYNTHRA is a structured, stateful operating system, not a chat wrapper or coding assistant. It interacts via APIs, queues, and automation pipelines, not conversational interfaces.
3.  **Unauthorized Scraper**: The system will not use web scraping, session hijacking, or automated browser emulation to bypass official API gates. If an official API for a feature does not exist, the system will not support that feature.
4.  **Brute-Force Equation Generator**: The platform will not generate random mathematical mutations in search of statistical anomalies. Every alpha generated must map to a verifiable economic hypothesis.
5.  **Monolithic System**: We will never build a single-process, highly coupled application. The orchestration layer, database, simulation client, and reasoning agents must remain separate processes communicating over clear interfaces.
