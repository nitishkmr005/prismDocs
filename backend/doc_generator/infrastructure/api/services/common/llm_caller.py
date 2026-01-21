"""LLM caller with automatic model fallback.

This module provides a wrapper around LLMService that handles model fallback
on transient errors, eliminating the duplicated fallback logic in IdeaCanvasService.
"""

from typing import Literal

from loguru import logger

from .....infrastructure.llm import LLMService
from .api_key_manager import configure_api_key


# Default fallback models for Gemini (in order of preference)
DEFAULT_GEMINI_FALLBACK_MODELS: list[str] = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
]


class LLMCaller:
    """Wrapper for LLM calls with automatic model fallback.

    This class encapsulates the retry logic that was previously duplicated
    in IdeaCanvasService._call_llm_with_fallback and similar methods.

    Example:
        >>> caller = LLMCaller(provider="gemini", api_key="key")
        >>> response = caller.call(
        ...     system_prompt="You are helpful.",
        ...     user_prompt="Hello!",
        ...     step_name="greeting"
        ... )
    """

    def __init__(
        self,
        provider: str,
        api_key: str,
        preferred_model: str | None = None,
        fallback_models: list[str] | None = None,
    ):
        """Initialize the LLM caller.

        Args:
            provider: LLM provider name (gemini, openai, anthropic)
            api_key: API key for the provider
            preferred_model: Preferred model to try first
            fallback_models: List of fallback models for Gemini
        """
        self.provider = provider.lower()
        if self.provider == "google":
            self.provider = "gemini"

        self.api_key = api_key
        self.preferred_model = preferred_model
        self.fallback_models = fallback_models or DEFAULT_GEMINI_FALLBACK_MODELS

        # Configure API key
        configure_api_key(self.provider, api_key)

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        step_name: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str:
        """Call LLM with automatic model fallback on transient errors.

        For Gemini provider, tries multiple models in order if one fails
        with 503/overload/unavailable errors.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            step_name: Name of the step (for logging)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            json_mode: Whether to request JSON output

        Returns:
            LLM response text

        Raises:
            ValueError: If no models are available
            Exception: If all models fail with non-retryable errors
        """
        if self.provider != "gemini":
            # Non-Gemini providers: single attempt
            return self._call_single_model(
                model=self.preferred_model or "gpt-4.1-mini",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                json_mode=json_mode,
                step_name=step_name,
            )

        # Gemini: try models with fallback
        models_to_try = self._build_model_list()
        return self._call_with_fallback(
            models=models_to_try,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            json_mode=json_mode,
            step_name=step_name,
        )

    def _build_model_list(self) -> list[str]:
        """Build ordered list of models to try.

        Returns:
            List of model names, preferred model first
        """
        models = []
        seen: set[str] = set()

        # Add preferred model first
        if self.preferred_model and self.preferred_model not in seen:
            models.append(self.preferred_model)
            seen.add(self.preferred_model)

        # Add fallback models
        for model in self.fallback_models:
            if model and model not in seen:
                models.append(model)
                seen.add(model)

        return models

    def _call_with_fallback(
        self,
        models: list[str],
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        json_mode: bool,
        step_name: str,
    ) -> str:
        """Try calling LLM with multiple models.

        Args:
            models: List of models to try in order
            Other args: Same as call()

        Returns:
            LLM response from first successful model

        Raises:
            ValueError: If no models available
            Exception: If all retryable attempts fail
        """
        last_error: Exception | None = None

        for model in models:
            try:
                return self._call_single_model(
                    model=model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    json_mode=json_mode,
                    step_name=step_name,
                )
            except Exception as e:
                if self._is_retryable_error(e):
                    logger.warning(
                        f"Model {model} overloaded, trying next. Error: {str(e)[:100]}"
                    )
                    last_error = e
                    continue
                else:
                    # Non-retryable error, propagate immediately
                    raise

        # All models failed
        if last_error:
            raise last_error
        raise ValueError("No models available")

    def _call_single_model(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        json_mode: bool,
        step_name: str,
    ) -> str:
        """Call a single LLM model.

        Args:
            model: Model name
            Other args: Same as call()

        Returns:
            LLM response text
        """
        llm_service = LLMService(provider=self.provider, model=model)
        return llm_service._call_llm(
            system_prompt,
            user_prompt,
            max_tokens,
            temperature,
            json_mode,
            step_name,
        )

    @staticmethod
    def _is_retryable_error(error: Exception) -> bool:
        """Check if an error should trigger model fallback.

        Args:
            error: The exception that occurred

        Returns:
            True if this error warrants trying another model
        """
        error_str = str(error).lower()
        retryable_patterns = ["503", "overload", "unavailable", "capacity"]
        return any(pattern in error_str for pattern in retryable_patterns)
