"""Reusable alpha expression templates representing core financial anomalies."""

from typing import Any, Dict


class ExpressionTemplate:
    """Base class for all formatting expression templates."""

    def __init__(self, name: str, pattern: str, parameters: Dict[str, Any]) -> None:
        """Initialize with a template name, pattern, and default params."""
        self.name = name
        self.pattern = pattern
        self.parameters = parameters

    def format_pattern(self, **kwargs: Any) -> str:
        """Build a formatted Fast Expression string from template parameters."""
        params = self.parameters.copy()
        params.update(kwargs)
        return self.pattern.format(**params)


class CrossSectionalRankingTemplate(ExpressionTemplate):
    """Template for sorting assets across a cross-section."""

    def __init__(self) -> None:
        """Initialize template with rank pattern."""
        super().__init__(
            name="cross-sectional ranking",
            pattern="rank({field})",
            parameters={"field": "close"},
        )


class TimeSeriesMomentumTemplate(ExpressionTemplate):
    """Template for time-series trend following."""

    def __init__(self) -> None:
        """Initialize template with delta pattern."""
        super().__init__(
            name="time-series momentum",
            pattern="ts_delta({field}, {window})",
            parameters={"field": "close", "window": 20},
        )


class VolatilityBreakoutTemplate(ExpressionTemplate):
    """Template for detecting breakouts relative to asset volatility."""

    def __init__(self) -> None:
        """Initialize template with standard deviation ratio pattern."""
        super().__init__(
            name="volatility breakout",
            pattern="ts_delta({field}, 1) / ts_std_dev({field}, {window})",
            parameters={"field": "close", "window": 20},
        )


class MeanReversionTemplate(ExpressionTemplate):
    """Template for asset mean reversion relative to a moving average."""

    def __init__(self) -> None:
        """Initialize template with mean deviation pattern."""
        super().__init__(
            name="mean reversion",
            pattern="ts_mean({field}, {window}) - {field}",
            parameters={"field": "close", "window": 20},
        )


class FundamentalSurpriseTemplate(ExpressionTemplate):
    """Template for measuring standardized surprises in accounting variables."""

    def __init__(self) -> None:
        """Initialize template with z-score surprise pattern."""
        super().__init__(
            name="fundamental surprise",
            pattern=(
                "({field} - ts_mean({field}, {window})) / "
                "ts_std_dev({field}, {window})"
            ),
            parameters={"field": "ebit", "window": 4},
        )


class AnalystRevisionTemplate(ExpressionTemplate):
    """Template for tracking forecast revision trends."""

    def __init__(self) -> None:
        """Initialize template with forecast revisions trend pattern."""
        super().__init__(
            name="analyst revision",
            pattern="ts_delta({field}, {window})",
            parameters={"field": "target_price", "window": 30},
        )


class QualityFactorTemplate(ExpressionTemplate):
    """Template for profit margin or asset return quality ratios."""

    def __init__(self) -> None:
        """Initialize template with division ratio pattern."""
        super().__init__(
            name="quality factor",
            pattern="({ebit} / {assets})",
            parameters={"ebit": "operating_income", "assets": "total_assets"},
        )


class MultiFactorBlendTemplate(ExpressionTemplate):
    """Template for combining two sub-alpha expressions."""

    def __init__(self) -> None:
        """Initialize template with double-scaled sum blend pattern."""
        super().__init__(
            name="multi-factor blend",
            pattern="scale(rank({expr1})) + scale(rank({expr2}))",
            parameters={"expr1": "close", "expr2": "volume"},
        )
