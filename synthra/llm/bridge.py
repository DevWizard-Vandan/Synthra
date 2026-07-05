"""Bridge helper to adapt unstructured LLM providers for structured outputs."""

import json
from typing import Type, TypeVar, List, Optional
from pydantic import BaseModel

from synthra.llm.base import LLMProvider
from synthra.llm.models import GenerationConfig, LLMRequest

T = TypeVar("T", bound=BaseModel)


class StructuredLLMBridge:
    """Helper class converting string completions to validated Pydantic models."""

    def __init__(
        self,
        provider: LLMProvider,
        fallback_providers: Optional[List[LLMProvider]] = None,
    ) -> None:
        """Initialize the bridge wrapper around any LLMProvider instance."""
        self.provider = provider
        self.fallback_providers = fallback_providers or []

    def generate_structured(
        self, system_prompt: str, user_prompt: str, response_model: Type[T]
    ) -> T:
        """Submit prompt and validate/coerce response to a Pydantic model.

        Ensures JSON format constraints are activated if supported, else
        injects schema guidelines into the prompt and handles raw parser fallback.
        """
        all_providers = [self.provider] + [
            p for p in self.fallback_providers if p is not self.provider
        ]
        errors = []
        for prov in all_providers:
            # Configure request
            config = GenerationConfig(
                temperature=0.0,
                response_format="json" if prov.supports_json() else None,
            )

            full_prompt = user_prompt
            if not prov.supports_json():
                schema_json = json.dumps(response_model.model_json_schema())
                full_prompt = (
                    f"{user_prompt}\n\n"
                    f"You must return a valid JSON object matching the schema:\n"
                    f"{schema_json}"
                )

            request = LLMRequest(
                prompt=full_prompt,
                system_prompt=system_prompt,
                config=config,
            )

            # Call underlying provider
            try:
                response = prov.generate(request)

                # Parse text output to Pydantic model
                cleaned_text = response.text.strip()

                # Remove potential markdown JSON blocks
                if cleaned_text.startswith("```"):
                    lines = cleaned_text.splitlines()
                    if lines[0].startswith("```json") or lines[0].startswith("```"):
                        cleaned_text = "\n".join(lines[1:-1])

                parsed_dict = json.loads(cleaned_text)
                return response_model.model_validate(parsed_dict)
            except Exception as e:
                model_name = getattr(prov, "model", "unknown")
                errors.append(f"{model_name}: {e}")

        raise ValueError(
            f"All LLM providers failed structured generation: {'; '.join(errors)}"
        )
