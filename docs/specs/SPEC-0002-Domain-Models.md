# SPEC-0002 — Domain Models Specification

---
spec:
  id: SPEC-0002
  title: "Domain Models Definition"
  version: 1.0
  status: Approved
  priority: Critical

owner: Project Architect
reviewer: Project Architect
implementer: Lead Engineer

created: 2026-07-02
last_updated: 2026-07-02

depends_on: SPEC-0001, DESIGN-0002
required_by: SPEC-0003, ALL_MODULES

estimated_complexity: Low
estimated_effort: 1 Day
---

## 🏛️ Boundary Validation Questions

1. **Why does this module exist?**
   - *Answer*: To define the immutable Pydantic schemas that represent the data objects in SYNTHRA's research lifecycle.

2. **Why is this the right boundary?**
   - *Answer*: This specification covers type schemas, constraint validations, and serialization signatures. It does not cover database drivers, execution adapters, or logic runtimes.

3. **Could another module own this responsibility?**
   - *Answer*: No. Downstream modules must consume standard, predefined type schemas to prevent circular import loops and interface instability.

4. **What happens if this module disappears?**
   - *Answer*: Type verification becomes fragmented, leading to integration issues between storage and agentic modules.

5. **Will we still like this design in two years?**
   - *Answer*: Yes, Pydantic's clean validation engine is a standard python pattern that is robust, performant, and self-documenting.

---

# 1. Executive Summary

This specification defines the directory structure, file names, and class definitions for SYNTHRA's domain model layer. It defines 9 immutable schemas representing the core research lifecycle.

---

# 2. Concrete Directory Structure

Claude Code **SHALL** generate the filesystem topology exactly as specified below.

```text
synthra/
└── core/
    ├── __init__.py
    └── domain/
        ├── __init__.py
        └── models.py          # Strongly typed Pydantic models
```

---

# 3. Dependency Matrix Controls

### 3.1 Explicitly Allowed Dependencies
* `pydantic` (v2.10+) — Runtime schema validation and immutability.
* `pathlib` — Native filesystem path mapping.
* `typing` / `re` / `datetime` — Standard python libraries for typing, regex checks, and timestamps.

### 3.2 Strictly Forbidden Dependencies
* `sqlite3` / `sqlalchemy` — No database access or driver definitions are allowed in the domain tier.
* `requests` / `httpx` — No network access.

---

# 4. Code Schema Signatures (`models.py`)

```python
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

class BaseDomainModel(BaseModel):
    """Base class for all domain models enforcing immutability."""
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        arbitrary_types_allowed=True
    )

class Campaign(BaseDomainModel):
    """Bounding context for a quantitative research program."""
    id: str = Field(..., description="Unique ID matching 'CMP-XXXX'")
    name: str = Field(..., min_length=1)
    region: str = Field(..., description="Target trading region (e.g. US, EU, AP)")
    universe: str = Field(..., description="Target trading universe (e.g. TOP3000)")
    budget_limit: float = Field(..., gt=0.0)
    budget_spent: float = Field(default=0.0, ge=0.0)
    status: Literal["draft", "active", "concluded"] = Field(default="draft")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    concluded_at: Optional[datetime] = Field(default=None)

    @field_validator("id")
    @classmethod
    def validate_campaign_id(cls, v: str) -> str:
        if not re.match(r"^CMP-\d{4}$", v):
            raise ValueError("Campaign ID must match the format 'CMP-XXXX'")
        return v

class Hypothesis(BaseDomainModel):
    """An economic rationale outlining predictive variables."""
    id: str = Field(..., description="Unique ID matching 'HYP-XXXX'")
    campaign_id: str = Field(..., description="Parent campaign ID")
    rationale: str = Field(..., min_length=10)
    target_variable: str = Field(..., min_length=1)
    datasets: List[str] = Field(..., min_length=1)
    operators: List[str] = Field(..., min_length=1)
    status: Literal["draft", "tested", "archived"] = Field(default="draft")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("id")
    @classmethod
    def validate_hypothesis_id(cls, v: str) -> str:
        if not re.match(r"^HYP-\d{4}$", v):
            raise ValueError("Hypothesis ID must match the format 'HYP-XXXX'")
        return v

    @field_validator("campaign_id")
    @classmethod
    def validate_campaign_id(cls, v: str) -> str:
        if not re.match(r"^CMP-\d{4}$", v):
            raise ValueError("Campaign ID must match the format 'CMP-XXXX'")
        return v

class SimulationRequest(BaseDomainModel):
    """System-agnostic simulation request parameters."""
    expression: str = Field(..., min_length=1)
    region: str
    universe: str
    delay: int = Field(default=1, ge=0)
    decay: int = Field(default=0, ge=0)
    neutralization: str = Field(default="SUBINDUSTRY")

class SimulationResult(BaseDomainModel):
    """Unified result metrics returned from backtesting."""
    sharpe: float
    fitness: float
    margin: float
    turnover: float
    coverage: float
    simulated_at: datetime = Field(default_factory=datetime.utcnow)

class Experiment(BaseDomainModel):
    """An orchestrated test execution linking a hypothesis variant to results."""
    id: str = Field(..., description="Unique ID matching 'EXP-XXXX'")
    campaign_id: str
    hypothesis_id: str
    expression: str = Field(..., min_length=1)
    status: Literal["pending", "running", "completed", "failed"] = Field(default="pending")
    request: SimulationRequest
    result: Optional[SimulationResult] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = Field(default=None)

    @field_validator("id")
    @classmethod
    def validate_experiment_id(cls, v: str) -> str:
        if not re.match(r"^EXP-\d{4}$", v):
            raise ValueError("Experiment ID must match the format 'EXP-XXXX'")
        return v

    @field_validator("campaign_id")
    @classmethod
    def validate_campaign_id(cls, v: str) -> str:
        if not re.match(r"^CMP-\d{4}$", v):
            raise ValueError("Campaign ID must match the format 'CMP-XXXX'")
        return v

    @field_validator("hypothesis_id")
    @classmethod
    def validate_hypothesis_id(cls, v: str) -> str:
        if not re.match(r"^HYP-\d{4}$", v):
            raise ValueError("Hypothesis ID must match the format 'HYP-XXXX'")
        return v

class AlphaCandidate(BaseDomainModel):
    """A high-performing strategy flagged for submission review."""
    id: str = Field(..., description="Unique ID matching 'AST-XXXX'")
    experiment_id: str
    hypothesis_id: str
    campaign_id: str
    expression: str
    sharpe: float
    fitness: float
    turnover: float
    margin: float
    is_submitted: bool = Field(default=False)
    submitted_at: Optional[datetime] = Field(default=None)

    @field_validator("id")
    @classmethod
    def validate_asset_id(cls, v: str) -> str:
        if not re.match(r"^AST-\d{4}$", v):
            raise ValueError("Asset ID must match the format 'AST-XXXX'")
        return v

    @field_validator("experiment_id")
    @classmethod
    def validate_experiment_id(cls, v: str) -> str:
        if not re.match(r"^EXP-\d{4}$", v):
            raise ValueError("Experiment ID must match the format 'EXP-XXXX'")
        return v

    @field_validator("hypothesis_id")
    @classmethod
    def validate_hypothesis_id(cls, v: str) -> str:
        if not re.match(r"^HYP-\d{4}$", v):
            raise ValueError("Hypothesis ID must match the format 'HYP-XXXX'")
        return v

    @field_validator("campaign_id")
    @classmethod
    def validate_campaign_id(cls, v: str) -> str:
        if not re.match(r"^CMP-\d{4}$", v):
            raise ValueError("Campaign ID must match the format 'CMP-XXXX'")
        return v

class Dataset(BaseDomainModel):
    """Platform dataset metadata profile."""
    name: str = Field(..., min_length=1)
    region: str
    category: str
    description: str
    fields: List[str] = Field(..., min_length=1)

class Operator(BaseDomainModel):
    """Platform operator metadata signature."""
    name: str = Field(..., min_length=1)
    category: str
    signature: str
    description: str

class ResearchAsset(BaseDomainModel):
    """Arbitrary file output produced during the research lifecycle."""
    id: str = Field(..., description="Unique ID matching 'AST-XXXX'")
    campaign_id: str
    type: str = Field(..., description="e.g. notebook, plot, code, report")
    file_path: Path
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("id")
    @classmethod
    def validate_asset_id(cls, v: str) -> str:
        if not re.match(r"^AST-\d{4}$", v):
            raise ValueError("Asset ID must match the format 'AST-XXXX'")
        return v

    @field_validator("campaign_id")
    @classmethod
    def validate_campaign_id(cls, v: str) -> str:
        if not re.match(r"^CMP-\d{4}$", v):
            raise ValueError("Campaign ID must match the format 'CMP-XXXX'")
        return v
```

---

# 5. Definition of Done Checklist

* [ ] Implement exactly two Python modules (`synthra/core/domain/__init__.py` and `synthra/core/domain/models.py`).
* [ ] Zero static type checking warnings using `mypy`.
* [ ] Pytest suite achieves 100% green coverage on model instantiation, validation, and immutability checks.
