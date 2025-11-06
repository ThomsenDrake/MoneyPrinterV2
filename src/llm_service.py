"""
LLM Service wrapper for AI model interactions.

This module eliminates code duplication across YouTube, Twitter, and AFM classes
by centralizing LLM client initialization and interaction logic.
"""

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from mistralai import Mistral

from llm_cache import LLMCache, get_llm_cache


class LLMService:
    """
    Service class for interacting with Large Language Models.

    This class centralizes LLM initialization and provides a clean interface
    for chat completions, which was previously duplicated across multiple classes.

    The service uses a singleton pattern per API key to avoid creating
    multiple client instances.
    """

    _instances: Dict[str, "LLMService"] = {}

    def __init__(
        self,
        api_key: str,
        default_model: str = "mistral-medium-latest",
        enable_cache: bool = False,
        cache: Optional[LLMCache] = None,
    ):
        """
        Initialize the LLM service.

        Args:
            api_key: The API key for the LLM provider (e.g., Mistral AI)
            default_model: Default model to use for completions
            enable_cache: Whether to enable response caching (default: False)
            cache: Optional LLMCache instance. If enable_cache is True and this is None,
                   the default global cache will be used.

        Example:
            >>> service = LLMService(api_key="sk-...", default_model="mistral-large-latest")
            >>> # With caching enabled:
            >>> service = LLMService(api_key="sk-...", enable_cache=True)
        """
        self.api_key = api_key
        self.default_model = default_model
        self.enable_cache = enable_cache
        self._client: Optional[Mistral] = None

        # Set up caching if enabled
        if enable_cache:
            self.cache = cache if cache is not None else get_llm_cache()
            logging.info("LLM response caching enabled")
        else:
            self.cache = None

    @classmethod
    def get_instance(
        cls, api_key: str, default_model: str = "mistral-medium-latest"
    ) -> "LLMService":
        """
        Get or create an LLM service instance for the given API key.

        Uses singleton pattern to reuse client instances for the same API key.

        Args:
            api_key: The API key for the LLM provider
            default_model: Default model to use for completions

        Returns:
            LLMService instance

        Example:
            >>> service = LLMService.get_instance(api_key="sk-...")
        """
        if api_key not in cls._instances:
            cls._instances[api_key] = cls(api_key=api_key, default_model=default_model)
            logging.info(f"Created new LLMService instance with model: {default_model}")
        return cls._instances[api_key]

    @property
    def client(self) -> Mistral:
        """
        Get or create the Mistral client instance.

        Lazily initializes the client on first access.

        Returns:
            Mistral client instance
        """
        if self._client is None:
            self._client = Mistral(api_key=self.api_key)
            logging.info("Mistral client initialized")
        return self._client

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
    ) -> str:
        """
        Perform a chat completion using the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            model: Model to use (defaults to instance's default_model)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            use_cache: Whether to use cache for this request (default: True).
                       Only used if caching is enabled for the service.

        Returns:
            The completion text from the LLM

        Raises:
            Exception: If the API call fails

        Example:
            >>> messages = [
            ...     {"role": "system", "content": "You are a helpful assistant"},
            ...     {"role": "user", "content": "Write a tweet about AI"}
            ... ]
            >>> response = service.chat_completion(messages)
        """
        try:
            model_to_use = model or self.default_model

            # Create a unique cache key from messages and parameters
            if self.enable_cache and use_cache and self.cache is not None:
                # Create a stable prompt representation for caching
                prompt_key = json.dumps(messages, sort_keys=True)

                # Check cache first
                cached_response = self.cache.get(
                    prompt=prompt_key,
                    model=model_to_use,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                if cached_response is not None:
                    logging.info(f"Using cached response for model: {model_to_use}")
                    return cached_response

            # Prepare API call parameters
            params = {"model": model_to_use, "messages": messages, "temperature": temperature}

            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            # Make the API call
            response = self.client.chat.complete(**params)

            # Extract the completion text
            completion = response.choices[0].message.content

            # Cache the response if caching is enabled
            if self.enable_cache and use_cache and self.cache is not None:
                prompt_key = json.dumps(messages, sort_keys=True)
                self.cache.set(
                    prompt=prompt_key,
                    response=completion,
                    model=model_to_use,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

            logging.info(f"Chat completion successful with model: {model_to_use}")
            return completion

        except Exception as e:
            logging.error(f"Chat completion failed: {str(e)}", exc_info=True)
            raise

    def generate_script(
        self, system_prompt: str, user_prompt: str, model: Optional[str] = None
    ) -> str:
        """
        Generate a script using the LLM.

        Convenience method for the common pattern of system + user prompts.

        Args:
            system_prompt: The system prompt defining the AI's role
            user_prompt: The user's request
            model: Model to use (defaults to instance's default_model)

        Returns:
            Generated script text

        Example:
            >>> script = service.generate_script(
            ...     system_prompt="You are a YouTube script writer",
            ...     user_prompt="Write a script about Python programming"
            ... )
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.chat_completion(messages, model=model)

    @classmethod
    def reset_instances(cls) -> None:
        """
        Reset all cached service instances.

        Useful for testing and cleanup.
        """
        cls._instances.clear()
        logging.debug("LLMService instances reset")


# Convenience function for backward compatibility
def create_llm_service(api_key: str, model: str = "mistral-medium-latest") -> LLMService:
    """
    Create or get an LLM service instance.

    This is a convenience function that wraps LLMService.get_instance()
    for easier migration from the old code pattern.

    Args:
        api_key: The API key for the LLM provider
        model: Default model to use

    Returns:
        LLMService instance

    Example:
        >>> from config import get_mistral_api_key
        >>> service = create_llm_service(get_mistral_api_key())
    """
    return LLMService.get_instance(api_key=api_key, default_model=model)
