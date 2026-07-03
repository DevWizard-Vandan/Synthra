"""Reasoning Engine formulating structured research paths from alpha concepts."""

from typing import List
from pydantic import BaseModel

from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import Campaign
from synthra.research.intelligence.knowledge import KnowledgeBase
from synthra.research.intelligence.templates import (
    AnalystRevisionTemplate,
    CrossSectionalRankingTemplate,
    ExpressionTemplate,
    FundamentalSurpriseTemplate,
    MeanReversionTemplate,
    QualityFactorTemplate,
    TimeSeriesMomentumTemplate,
    VolatilityBreakoutTemplate,
)


class ReasoningPath(BaseModel):
    """Structured step-by-step reasoning behind a proposed quantitative hypothesis."""

    concept: str
    thesis: str
    evidence: str
    required_dataset: str
    suitable_operators: List[str]
    expression_blueprint: str
    candidate_expressions: List[str]


class ReasoningEngine:
    """Translates high-level alpha concepts into structured expression pipelines."""

    def __init__(self, catalog: DatasetCatalog) -> None:
        """Initialize the reasoning engine with the shared DatasetCatalog."""
        self.catalog = catalog

    def formulate_reasoning_paths(
        self, campaign: Campaign, knowledge_base: KnowledgeBase
    ) -> List[ReasoningPath]:
        """Convert campaign details and knowledge base entries into reasoning paths."""
        paths: List[ReasoningPath] = []
        region_str = getattr(campaign.region, "value", str(campaign.region))
        universe_str = getattr(campaign.universe, "value", str(campaign.universe))

        # Filter dataset catalog items compatible with campaign constraints
        catalog_datasets = self.catalog.filter_datasets(
            region=campaign.region, universe=campaign.universe
        )
        catalog_ds_names = {ds.name for ds in catalog_datasets}

        for entry in knowledge_base.get_entries():
            # Check compatibility with campaign region and universe
            if region_str not in entry.preferred_regions:
                continue
            if universe_str not in entry.preferred_universes:
                continue

            # Determine intersection of preferred datasets
            common_datasets = [
                ds_name
                for ds_name in entry.preferred_datasets
                if ds_name in catalog_ds_names
            ]
            if not common_datasets:
                continue

            # Match concept with appropriate templates
            for dataset_name in common_datasets:
                ds = self.catalog.get_dataset(dataset_name)
                if not ds or not ds.fields:
                    continue

                templates: List[ExpressionTemplate] = []
                if entry.concept == "Momentum":
                    templates.append(TimeSeriesMomentumTemplate())
                    templates.append(CrossSectionalRankingTemplate())
                elif entry.concept == "Mean Reversion":
                    templates.append(MeanReversionTemplate())
                elif entry.concept == "Volatility":
                    templates.append(VolatilityBreakoutTemplate())
                elif entry.concept == "Quality":
                    templates.append(QualityFactorTemplate())
                elif entry.concept == "Value" or entry.concept == "Growth":
                    templates.append(FundamentalSurpriseTemplate())
                elif entry.concept == "Analyst Revisions":
                    templates.append(AnalystRevisionTemplate())
                else:
                    # Fallback to simple cross-sectional ranking
                    templates.append(CrossSectionalRankingTemplate())

                for template in templates:
                    # Formulate blueprint and candidates based on catalog fields
                    primary_field = ds.fields[0]
                    blueprint = template.pattern

                    candidates: List[str] = []
                    # Generate options based on lookback windows
                    for window in entry.preferred_lookback_windows:
                        try:
                            if template.name == "quality factor":
                                # requires multiple fields
                                ebit_f = (
                                    "operating_income"
                                    if "operating_income" in ds.fields
                                    else ds.fields[0]
                                )
                                assets_f = (
                                    "total_assets"
                                    if "total_assets" in ds.fields
                                    else (
                                        ds.fields[1]
                                        if len(ds.fields) > 1
                                        else ds.fields[0]
                                    )
                                )
                                expr = template.format_pattern(
                                    ebit=ebit_f, assets=assets_f
                                )
                            elif template.name == "cross-sectional ranking":
                                expr = template.format_pattern(field=primary_field)
                            else:
                                expr = template.format_pattern(
                                    field=primary_field, window=window
                                )
                            candidates.append(expr)
                        except Exception:
                            pass

                    if candidates:
                        thesis = (
                            f"Predicting return anomalies using the '{entry.concept}' "
                            f"factor logic based on economic rationale: "
                            f"{entry.economic_rationale}"
                        )
                        evidence = (
                            f"Applying {template.name} templates to "
                            f"'{dataset_name}' using preferred windows: "
                            f"{entry.preferred_lookback_windows}"
                        )

                        paths.append(
                            ReasoningPath(
                                concept=entry.concept,
                                thesis=thesis,
                                evidence=evidence,
                                required_dataset=dataset_name,
                                suitable_operators=entry.preferred_operators,
                                expression_blueprint=blueprint,
                                candidate_expressions=candidates,
                            )
                        )

        return paths
