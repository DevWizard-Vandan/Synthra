"""Pydantic models used by the WorldQuant execution layer."""

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class BaseExecutionModel(BaseModel):
    """Base immutable model for execution-layer contracts."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        arbitrary_types_allowed=True,
    )


class WorldQuantCredentials(BaseExecutionModel):
    """Credential pair used for official WorldQuant BRAIN authentication."""

    username: str = Field(..., min_length=1)
    password: SecretStr


class WorldQuantExecutionConfig(BaseExecutionModel):
    """Runtime controls for WorldQuant BRAIN API requests."""

    api_base_url: str = Field(default="https://api.worldquantbrain.com", min_length=1)
    auth_path: str = Field(default="/authentication", min_length=1)
    simulations_path: str = Field(default="/simulations", min_length=1)
    timeout_seconds: float = Field(default=30.0, gt=0.0)
    max_retries: int = Field(default=2, ge=0, le=10)


class SimulationHandle(BaseExecutionModel):
    """Reference returned after a simulation request is accepted."""

    id: str = Field(..., min_length=1)
    status: str = Field(default="submitted", min_length=1)
    location: str = Field(..., min_length=1)
