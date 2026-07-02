# SPEC-0001 — Configuration Manager Technical Specification

---
specification:
  id: SPEC-0001
  title: "Configuration Manager Infrastructure Implementation"
  version: 1.2
  status: RATIFIED & FROZEN 🧊
  priority: Block-0

owner: Project Architect
implementer: Claude Code

target_language: Python 3.11+
core_framework: Pydantic v2.10+
configuration_format: TOML
---

## 1. Concrete Directory Structure

Claude Code **SHALL** generate the filesystem topology exactly as specified below. No additional files, multi-file extensions, or utility directories shall be injected into this namespace.

```text
synthra/
└── core/
    ├── __init__.py
    └── config/
        ├── __init__.py
        ├── models.py          # Strongly typed Pydantic structures & ownership
        ├── loader.py          # Discrete source byte-stream reader
        ├── parser.py          # Decoupled text format translation engine
        ├── resolver.py        # Cascading dictionary matrix processor
        ├── validator.py       # Pydantic schema validation wrapper
        ├── exceptions.py      # Module specific exception tree
        └── manager.py         # Orchestration gateway module
```

---

## 2. Dependency Matrix Controls

### 2.1 Explicitly Allowed Dependencies

The Configuration Manager subsystem **SHALL** only import and use these libraries:

* `pydantic` (v2.10+) — Runtime schema validation, constraint checking, and immutability enforcement.
* `tomllib` — Python standard library TOML parser.
* `pathlib` — Native filesystem object mapping.
* `typing` / `os` / `hashlib` / `json` — Type hinting, structural generics, standard environment interaction, and hash calculation.

### 2.2 Strictly Forbidden Dependencies

To ensure an uncompromising boundary, Claude Code **SHALL NOT** import or invoke any of the following within this subsystem namespace:

* `requests` / `httpx` / `aiohttp` — No runtime network calls are permitted during configuration parsing.
* `sqlite3` / `sqlalchemy` — The manager must know nothing about database drivers or execution types.
* `logging` — The manager produces structured telemetry records/events; it does not set up or call active logger sinks.

---

## 3. Configuration Ownership & Schema Hierarchy (`models.py`)

### 3.1 Conceptual Topology & Injection Pathway Diagram

The subsystem establishes a unidirectional dependency flow, transforming raw multi-tier file representations into a single frozen container injected cleanly down-stack into higher domain modules.

```text
       Bootstrap Engine (Discovers Paths & Ephemeral Overrides)
                │
                ▼
      Configuration Manager
                │
                ▼
        ApplicationConfig (Frozen Root Container Layer)
         ├── app: ApplicationSubConfig
         ├── runtime: RuntimeConfig
         ├── logging: LoggingConfig
         ├── storage: StorageConfig
         ├── llm: LLMConfig ──> Dict[str, LLMProviderConfig]
         ├── security: SecurityConfig
         ├── paths: PathConfig
         └── monitoring: MonitoringConfig
                │
                ▼
      [ Dependency Injection ]
                │
         ┌──────┴──────┐
         ▼             ▼
   Logging Engine   Storage Subsystem  ... (Everything Else)
```

### 3.2 Code Schema Signatures

```python
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from typing import Dict, Literal, Optional
from pathlib import Path

class BaseConfigModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,          # Enforces absolute post-validation immutability
        extra="forbid",        # Fails validation instantly if unknown keys are passed
        strict=True,          # Disallows unsafe implicit type-coercion loops
        arbitrary_types_allowed=True  # Allows native pathlib.Path type mappings
    )

class ApplicationSubConfig(BaseConfigModel):
    name: str = Field(default="Synthra")
    env: Literal["development", "production", "local"]
    schema_version: int = Field(default=1)

class RuntimeConfig(BaseConfigModel):
    concurrency_pool_size: int = Field(gt=0, le=64)
    thread_timeout_seconds: float = Field(default=30.0, gt=0.0)

class LoggingConfig(BaseConfigModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

class StorageConfig(BaseConfigModel):
    backend: str              # e.g., "sqlite", "postgresql", "memory"
    connection_string: str
    timeout_ms: int = Field(default=5000, ge=0)
    retry_limit: int = Field(default=3, ge=0)

class LLMProviderSecrets(BaseConfigModel):
    api_key: SecretStr        # Explicitly wrapped to block log leaks

class LLMProviderConfig(BaseConfigModel):
    model: str
    enabled: bool = Field(default=True)
    timeout_seconds: int = Field(default=120, gt=0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    api_base: Optional[str] = Field(default=None)
    secrets: LLMProviderSecrets

class LLMConfig(BaseConfigModel):
    providers: Dict[str, LLMProviderConfig] # Fully dynamic dictionary map

class PathConfig(BaseConfigModel):
    data_dir: Path
    output_dir: Path

class MonitoringConfig(BaseConfigModel):
    pulse_interval_seconds: int = Field(default=10, gt=0)
    metrics_enabled: bool = Field(default=True)

class ApplicationConfig(BaseConfigModel):
    app: ApplicationSubConfig
    runtime: RuntimeConfig
    logging: LoggingConfig
    storage: StorageConfig
    llm: LLMConfig
    paths: PathConfig
    monitoring: MonitoringConfig
```

---

## 4. Public Class Architecture & Component Contracts

### 4.1 `exceptions.py`

```python
class ConfigurationError(Exception):
    """Base exception for all system configuration structural errors."""
    pass

class ConfigurationFileMissing(ConfigurationError):
    """Raised if raw configuration resource lookups fail on disk."""
    pass

class ConfigurationValidationError(ConfigurationError):
    """Raised when Pydantic parsing verification metrics break."""
    pass

class ConfigurationVersionMismatch(ConfigurationError):
    """Base category for configuration schema version errors. 
    Note: The Configuration Manager does NOT perform data translation; schema migrations 
    MUST be managed by a separate, dedicated external orchestrator or migration script.
    """
    pass

class UnsupportedConfigurationVersion(ConfigurationVersionMismatch):
    """Raised if the top-level schema version integer is completely unrecognized."""
    pass

class ConfigurationMigrationRequired(ConfigurationVersionMismatch):
    """Raised if schema values require upstream legacy conversion prior to loading."""
    pass

class SecretMissingError(ConfigurationError):
    """Raised when required env keys or secret tokens evaluate to empty strings."""
    pass
```

### 4.2 Class Operations

#### `loader.py`

```python
class ConfigurationLoader:
    """Responsibility: Pure disk reader tracking byte stream location streams."""
    
    @staticmethod
    def load_bytes(file_path: Path) -> bytes:
        """Reads a physical location path asset and returns raw file contents.
        Raises: ConfigurationFileMissing if target path is unreachable or a directory.
        """
        pass
```

#### `parser.py`

```python
from typing import Dict, Any

class ConfigurationParser:
    """Responsibility: Decoupled translation engine converting serialized strings to dict mappings."""
    
    @staticmethod
    def parse_toml(raw_bytes: bytes) -> Dict[str, Any]:
        """Converts raw byte structures into standard primitive Python dictionary objects using tomllib."""
        pass
```

#### `resolver.py`

```python
from typing import Dict, Any, List

class ConfigurationResolver:
    """Responsibility: Pure dictionary structure cascade manipulation and environment injection."""
    
    @staticmethod
    def deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merges dictionary maps."""
        pass

    @classmethod
    def resolve_cascade(cls, 
                        file_payloads: List[Dict[str, Any]], 
                        env_vars: Dict[str, Any], 
                        bootstrap_overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Collapses multidimensional inputs down to one cohesive dictionary.
        
        Args:
            file_payloads: Hierarchical raw dictionary payloads.
            env_vars: Environment values retrieved from os.environ.
            bootstrap_overrides: Ephemeral runtime overrides supplied by the bootstrap process.
                                 These are strictly read-only overrides and SHALL NOT be written
                                 back into configuration files.
        """
        pass
```

#### `validator.py`

```python
from typing import Dict, Any
from synthra.core.config.models import ApplicationConfig

class ConfigurationValidator:
    """Responsibility: Structural type checking and instantiation pass using Pydantic models."""
    
    @staticmethod
    def validate_schema(raw_data: Dict[str, Any]) -> ApplicationConfig:
        """Instantiates ApplicationConfig. Raises ConfigurationValidationError or Version subclasses."""
        pass
```

#### `manager.py`

```python
from typing import Dict, Any, List
from pathlib import Path
from synthra.core.config.models import ApplicationConfig

class ConfigurationManager:
    """Responsibility: Orchestration control loop and data wrapper gateway."""
    
    @staticmethod
    def bootstrap_configuration(ordered_source_files: List[Path], 
                                bootstrap_overrides: Dict[str, Any]) -> ApplicationConfig:
        """Orchestrates configuration instantiation via dependency ingestion rules."""
        pass
```

---

## 5. Startup Sequence & Lifecycle Events

### 5.1 Programmatic Execution Flow

```text
1. Bootstrap entry discovers configuration paths -> [config/base.toml, config/development.toml, config/local.toml]
2. Manager triggers loop and signals event -> ConfigurationLoadingStarted
3. ConfigurationLoader reads target files into memory byte streams
4. ConfigurationParser converts streams into standard primitive dictionaries
5. ConfigurationResolver executes deep_merge loop across file payloads sequentially
6. ConfigurationResolver pulls target tokens from os.environ and maps them into nested structures
7. ConfigurationResolver overlays programmatic, ephemeral bootstrap_overrides dict
8. Signals structural mapping finish event -> ConfigurationResolved
9. ConfigurationValidator executes type validation pass across the completed dictionary
10. Signals validation check success event -> ConfigurationValidated
11. Pydantic locks down structural modifications permanently via frozen configuration settings
12. Manager compiles data object summary -> Emits ConfigurationReady event containing ApplicationConfig instance
```

### 5.2 Explicit Conceptual Event Contracts

* `ConfigurationLoadingStarted(source_paths: List[Path])`
* `ConfigurationResolved(raw_merged_primitives: Dict[str, Any])`
* `ConfigurationValidated(validated_config: ApplicationConfig)`
* `ConfigurationReady(config: ApplicationConfig, summary: ConfigurationSummary)`
* `ConfigurationFailed(error: ConfigurationError, contextual_phrase: str)`

---

## 6. Output Telemetry Data Schema Contract

The output dictionary summary compiled during the `ConfigurationReady` execution state **MUST** exactly track this structural mapping:

```python
class ConfigurationSummary(BaseConfigModel):
    environment: Literal["development", "production", "local"]
    schema_version: int
    loaded_files: List[str]
    storage_backend: str
    providers_loaded: List[str]      # Derived list extracted out from dynamic provider keys
    configuration_hash: str          # Deterministic SHA-256 hex digest computed across the sorted, 
                                     # serialized JSON representation of the final raw_data dictionary, 
                                     # but EXCLUDING all sensitive Pydantic SecretStr field values,
                                     # ensuring full structural tracking without secret leakage.
    loaded_at: str                   # ISO 8601 UTC timestamp of bootstrap trigger
```

---

## 7. Implementation Verification Test Matrix

| Target ID | Injected Vector | Evaluated Subsystem State Reaction Lifecycle Output |
| --- | --- | --- |
| **TC-001** | Empty paths array or invalid targets passed to manager loop. | Ingestion Halt; Raise `ConfigurationFileMissing`. |
| **TC-002** | Invalid primitive schema type parameter entry. | Ingestion Halt; Raise `ConfigurationValidationError`. |
| **TC-003** | Injection of unmapped tracking parameters outside schema constraints. | Ingestion Halt; Raise `ConfigurationValidationError`. |
| **TC-004** | Target mapping missing mandatory environment variables (`api_key`). | Ingestion Halt; Raise `SecretMissingError`. |
| **TC-005** | Top-level schema version parameter is incremented out of bounds (`version = 99`). | Ingestion Halt; Raise `UnsupportedConfigurationVersion`. |
| **TC-006** | Flawless structural inputs and configuration files sheet. | Return fully frozen typed instance of `ApplicationConfig`. |
| **TC-007** | Post-instantiation code write mutation request execution. | Property write-operation blocked; Throw `ValidationError`/`PydanticError`. |
| **TC-008** | Serialization lookup verification pass. | Validate that calling `.model_dump_json()` replaces `SecretStr` entries with `""` or `**********`. |
| **TC-009** | Malformed TOML syntax verification. | Ingestion Halt; Raise `ConfigurationValidationError`. |
| **TC-010** | Environment override precedence over TOML values. | Return ApplicationConfig with environment values overriding TOML keys. |
| **TC-011** | Loaded At timestamp presence and properties. | Verify loaded_at ends with 'Z' and dynamic time changes do not alter configuration_hash. |

---

## 8. Definition of Done Checklist

Claude Code **SHALL NOT** sign off on this technical contract block until every target milestone below passes:

* [x] **Public API Stability**: Complete a formal structural review of all public function names and signatures; ensure signatures are bulletproof against immediate future alterations.
* [x] **Structural Isolation**: Create exactly 8 functional, single-purpose Python modules matching the designated file system topology layout.
* [x] **Type Correctness**: Enforce strict `mypy` typing checks; zero errors across the entire module layer.
* [x] **Zero Execution Noise**: `pytest` execution passes green across all test boundaries (**TC-001** through **TC-011**), with **0 active code warnings**.
* [x] **Clean Code Metrics**: No `TODO`, `FIXME`, or structural hacking markers inside production comments.
* [x] **Configuration Samples Provided**:
  * `config/base.toml` defining base specifications for all Child domain config definitions.
  - `config/development.toml`, `config/production.toml`, and git-ignored templates for `config/local.toml` and `.env`.
