"""Strongly typed, immutable data models for the LLM Provider Layer."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BaseLLMModel(BaseModel):
    """Base class enforcing immutability and strict schemas for LLM models."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
    )


class GenerationConfig(BaseLLMModel):
    """Configuration parameters for language model generation requests."""

    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    response_format: Optional[str] = Field(default=None)  # e.g., "json"


class LLMRequest(BaseLLMModel):
    """Unified container for text generation request arguments."""

    prompt: str = Field(..., min_length=1)
    system_prompt: Optional[str] = Field(default=None)
    config: GenerationConfig = Field(default_factory=GenerationConfig)


class TokenUsage(BaseLLMModel):
    """Token consumption metrics for a given model inference execution."""

    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class LLMResponse(BaseLLMModel):
    """Unified container holding text output and execution metadata."""

    text: str
    model: str
    provider: str
    usage: TokenUsage = Field(default_factory=TokenUsage)
    cached: bool = Field(default=False)


class ModelInfo(BaseLLMModel):
    """Metadata detailing capabilities and limits of a specific LLM."""

    name: str
    context_window: int = Field(..., gt=0)
    supports_json: bool
    supports_streaming: bool


class ProviderHealth(BaseLLMModel):
    """Liveness probe details for an LLM provider connection."""

    status: str  # "healthy" or "unhealthy"
    latency_ms: float = Field(default=0.0, ge=0.0)
    error_message: Optional[str] = Field(default=None)
