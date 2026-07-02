---
title: Synthra
emoji: 📈
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
app_port: 7860
---

# Synthra

**Autonomous Quantitative Research Platform**

Synthra is a production-grade autonomous research pipeline designed to assist quantitative researchers working on the [WorldQuant BRAIN](https://platform.worldquant.com/) platform.

## What Synthra Does

Synthra automates the full alpha research lifecycle:

1. **Research** — Generates hypotheses grounded in financial theory and data signals
2. **Generate** — Constructs alpha expressions from the Dataset Catalog
3. **Validate** — Validates expressions against field/operator constraints
4. **Simulate** — Submits simulations to WorldQuant BRAIN and stores results
5. **Evaluate** — Ranks results using Sharpe, turnover, fitness, and drawdown metrics

## Service Endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Service identity |
| `GET /health` | Liveness probe |
| `GET /status` | Runtime status and memory counters |
| `GET /campaigns` | Active research campaigns |
| `GET /docs` | Interactive API documentation |

## Architecture

```
synthra/
├── api/            — FastAPI service layer
├── core/
│   ├── catalog/    — Dataset & operator metadata catalog
│   ├── config/     — Configuration management
│   └── domain/     — Immutable domain models
├── execution/      — WorldQuant BRAIN simulation client
└── memory/         — SQLite persistence layer
```

## Tech Stack

- **Python 3.11**
- **FastAPI + Uvicorn** — HTTP service
- **Pydantic v2** — Type-safe domain models
- **SQLite** — Local persistence
- **Docker** — Container deployment

## Status

> V1.0.0 — Service skeleton. The autonomous research loop is under active development.
