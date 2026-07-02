"""Feedback subsystem mapping simulation results to persistent learning records."""

from typing import List
from pydantic import BaseModel, ConfigDict, Field

from synthra.core.domain import SimulationRequest, SimulationResult
from synthra.learning.analyzer import ResultAnalyzer


class LearningRecord(BaseModel):
    """Container mapping expression parameters and metrics for model guidance."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
    )

    expression: str
    datasets: List[str]
    operators: List[str]
    delay: int
    neutralization: str
    universe: str
    region: str
    sharpe: float
    fitness: float
    margin: float
    turnover: float
    coverage: float
    success: bool
    failure_reasons: List[str] = Field(default_factory=list)
    success_reasons: List[str] = Field(default_factory=list)


class FeedbackGenerator:
    """Converts requests and results to structured LearningRecords."""

    def __init__(self, analyzer: ResultAnalyzer | None = None) -> None:
        """Initialize with an optional custom ResultAnalyzer."""
        self.analyzer = analyzer or ResultAnalyzer()

    def generate_record(
        self,
        request: SimulationRequest,
        result: SimulationResult,
        datasets: List[str],
        operators: List[str],
    ) -> LearningRecord:
        """Construct a LearningRecord detailing execution configuration and outcomes."""
        failure_reasons, success_reasons = self.analyzer.analyze(result)
        success = len(failure_reasons) == 0

        # Region/Universe values check (using string value directly if enum)
        region_str = getattr(request.region, "value", str(request.region))
        universe_str = getattr(request.universe, "value", str(request.universe))

        return LearningRecord(
            expression=request.expression,
            datasets=datasets,
            operators=operators,
            delay=request.delay,
            neutralization=request.neutralization,
            universe=universe_str,
            region=region_str,
            sharpe=result.sharpe,
            fitness=result.fitness,
            margin=result.margin,
            turnover=result.turnover,
            coverage=result.coverage,
            success=success,
            failure_reasons=failure_reasons,
            success_reasons=success_reasons,
        )
