"""Cascading dictionary matrix processor and environment injector."""

import copy
from typing import Any, Dict, List


class ConfigurationResolver:
    """Pure dictionary structure cascade manipulation and environment injection."""

    @staticmethod
    def deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merges source dictionary into target without mutating inputs.

        Args:
            target: Base dictionary to merge into.
            source: Overriding dictionary.

        Returns:
            A new deep-merged dictionary instance.
        """
        merged = copy.deepcopy(target)
        for key, value in source.items():
            if (
                isinstance(value, dict)
                and key in merged
                and isinstance(merged[key], dict)
            ):
                merged[key] = ConfigurationResolver.deep_merge(merged[key], value)
            else:
                merged[key] = copy.deepcopy(value)
        return merged

    @staticmethod
    def _coerce_env_value(val: str) -> Any:
        """Coerces environment variable string values into correct types."""
        if val.lower() == "true":
            return True
        if val.lower() == "false":
            return False
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            pass
        return val

    @staticmethod
    def _set_nested_value(d: Dict[str, Any], parts: List[str], value: Any) -> bool:
        """Walks down the dictionary using path parts and sets the value.

        Handles both static keys with underscores and dynamic keys.
        """
        for k in range(1, len(parts) + 1):
            key_candidate = "_".join(parts[:k])
            if key_candidate in d:
                if k == len(parts):
                    d[key_candidate] = value
                    return True
                elif isinstance(d[key_candidate], dict):
                    if ConfigurationResolver._set_nested_value(
                        d[key_candidate], parts[k:], value
                    ):
                        return True

        # Fallback for dynamic keys: if path is not yet initialized but makes sense,
        # create sub-dictionaries as needed (e.g. under 'providers').
        if len(parts) > 1:
            part_key = parts[0]
            if part_key not in d:
                d[part_key] = {}
            if ConfigurationResolver._set_nested_value(d[part_key], parts[1:], value):
                return True
            else:
                if not d[part_key]:
                    del d[part_key]
        return False

    @classmethod
    def resolve_cascade(
        cls,
        file_payloads: List[Dict[str, Any]],
        env_vars: Dict[str, Any],
        bootstrap_overrides: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Collapses multidimensional inputs down to one cohesive dictionary.

        Precedence (Highest to Lowest):
        1. bootstrap_overrides
        2. env_vars (os.environ)
        3. file_payloads (local.toml -> prod/dev.toml -> base.toml)

        Args:
            file_payloads: Hierarchical raw dictionary payloads.
            env_vars: Environment values retrieved from os.environ.
            bootstrap_overrides: Ephemeral runtime overrides.
        """
        merged: Dict[str, Any] = {}

        # 1. Merge files in order (base -> env -> local)
        for payload in file_payloads:
            merged = cls.deep_merge(merged, payload)

        # 2. Inject environment variables
        for env_key, raw_val in env_vars.items():
            if env_key.startswith("SYNTHRA_"):
                # Strip prefix, split, and convert to lowercase parts
                clean_key = env_key[len("SYNTHRA_") :]
                parts = clean_key.lower().split("_")
                val = cls._coerce_env_value(str(raw_val))
                cls._set_nested_value(merged, parts, val)

        # 3. Apply bootstrap overrides
        if bootstrap_overrides:
            merged = cls.deep_merge(merged, bootstrap_overrides)

        return merged
