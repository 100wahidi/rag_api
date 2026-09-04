from __future__ import annotations

import asyncio
import json
import os
import random
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from typing import Any, TypeVar

from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncGroq,
    Groq,
    RateLimitError,
)
from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """Provider-neutral LLM interface."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: type[T],
        *,
        model: str | None = None,
    ) -> T:
        raise NotImplementedError


class GroqProvider(BaseLLMProvider):
    """Groq provider with model fallback and retry handling."""

    DEFAULT_MODELS = (
                        "llama-3.1-8b-instant",

                        "llama-3.3-70b-versatile",

                        "openai/gpt-oss-20b",

                        "openai/gpt-oss-120b",

                        "qwen/qwen3-32b",

                        "groq/compound",

                        "groq/compound-mini",
                        
                    )

    RETRYABLE_ERRORS = (
        RateLimitError,
        APITimeoutError,
        APIConnectionError,
    )

    def __init__(
        self,
        api_key: str | None = None,
        *,
        models: Sequence[str] | None = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key 
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required.")

        self.operational_llms = list(models or self.DEFAULT_MODELS)
        if not self.operational_llms:
            raise ValueError("At least one Groq model is required.")

        self.model = self.operational_llms[0]
        self.max_retries = max_retries
        self.base_delay = base_delay

        self.client = Groq(
            api_key=self.api_key,
            timeout=timeout,
            max_retries=0,
        )

    def get_llm_client(self) -> Groq:
        return self.client

    def get_available_models(self) -> list[str]:
        return self.operational_llms.copy()

    def handlel_llm(self) -> str:
        """Backward-compatible misspelled method."""
        return self.model

    @staticmethod
    def _messages(
        system_prompt: str,
        user_prompt: str,
    ) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        if isinstance(exc, GroqProvider.RETRYABLE_ERRORS):
            return True

        return isinstance(exc, APIStatusError) and exc.status_code >= 500

    def _sleep(self, attempt: int) -> None:
        delay = self.base_delay * (2**attempt)
        delay += random.uniform(0, 0.25)
        time.sleep(delay)

    async def _async_sleep(self, attempt: int) -> None:
        delay = self.base_delay * (2**attempt)
        delay += random.uniform(0, 0.25)
        await asyncio.sleep(delay)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
    ) -> str:
        selected_models = [model] if model else self.operational_llms
        last_error: Exception | None = None

        for selected_model in selected_models:
            for attempt in range(self.max_retries + 1):
                try:
                    response = self.client.chat.completions.create(
                        model=selected_model,
                        messages=self._messages(system_prompt, user_prompt),
                    )

                    self.model = selected_model
                    return response.choices[0].message.content or ""

                except Exception as exc:
                    last_error = exc

                    if not self._is_retryable(exc):
                        break

                    if attempt < self.max_retries:
                        self._sleep(attempt)

        raise RuntimeError(
            f"All Groq models failed. Last error: {last_error!r}"
        ) from last_error

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        Response_format,
        *,
        model: str | None = None,
    ):

        selected_models = [model] if model else self.operational_llms
        last_error: Exception | None = None

        for selected_model in selected_models:
            for attempt in range(self.max_retries + 1):
                try:
                    response = self.client.chat.completions.create(
                        model=selected_model,
                        messages=self._messages(
                            system_prompt,
                            user_prompt,
                        ),
                        response_format=Response_format,
                    )

                    content = response.choices[0].message.content
                    if not content:
                        raise ValueError("Groq returned empty structured output.")

                    self.model = selected_model
                    return content

                except Exception as exc:
                    last_error = exc

                    if not self._is_retryable(exc):
                        break

                    if attempt < self.max_retries:
                        self._sleep(attempt)

        raise RuntimeError(
            f"All Groq models failed. Last error: {last_error!r}"
        ) from last_error

    def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
    ) -> Any:
        """Return a synchronous Groq streaming response."""
        return self.client.chat.completions.create(
            model=model or self.model,
            messages=self._messages(system_prompt, user_prompt),
            stream=True,
        )

    def create_embedding(
        self,
        text: str | Sequence[str],
        *,
        model: str = "text-embedding-3-small",
    ) -> list[list[float]]:
        raise NotImplementedError(
            "Groq does not provide a compatible embeddings endpoint. "
            "Use SentenceTransformer or another embedding provider."
        )


class AsyncGroqProvider(GroqProvider):
    """Asynchronous Groq provider."""

    def __init__(
        self,
        *args: Any,
        timeout: float = 60.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, timeout=timeout, **kwargs)
        self.client = AsyncGroq(
            api_key=self.api_key,
            timeout=timeout,
            max_retries=0,
        )

    def get_llm_client(self) -> AsyncGroq:
        return self.client

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
    ) -> str:
        selected_models = [model] if model else self.operational_llms
        last_error: Exception | None = None

        for selected_model in selected_models:
            for attempt in range(self.max_retries + 1):
                try:
                    response = await self.client.chat.completions.create(
                        model=selected_model,
                        messages=self._messages(system_prompt, user_prompt),
                    )

                    self.model = selected_model
                    return response.choices[0].message.content or ""

                except Exception as exc:
                    last_error = exc

                    if not self._is_retryable(exc):
                        break

                    if attempt < self.max_retries:
                        await self._async_sleep(attempt)

        raise RuntimeError(
            f"All Groq models failed. Last error: {last_error!r}"
        ) from last_error

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: type[T],
        *,
        model: str | None = None,
    ) -> T:
        schema = response_format.model_json_schema()
        structured_prompt = (
            f"{system_prompt}\n\n"
            "Return only valid JSON matching this schema:\n"
            f"{json.dumps(schema)}"
        )

        selected_models = [model] if model else self.operational_llms
        last_error: Exception | None = None

        for selected_model in selected_models:
            for attempt in range(self.max_retries + 1):
                try:
                    response = await self.client.chat.completions.create(
                        model=selected_model,
                        messages=self._messages(
                            structured_prompt,
                            user_prompt,
                        ),
                        response_format={"type": "json_object"},
                    )

                    content = response.choices[0].message.content
                    if not content:
                        raise ValueError("Groq returned empty structured output.")

                    self.model = selected_model
                    return response_format.model_validate(json.loads(content))

                except Exception as exc:
                    last_error = exc

                    if not self._is_retryable(exc):
                        break

                    if attempt < self.max_retries:
                        await self._async_sleep(attempt)

        raise RuntimeError(
            f"All Groq models failed. Last error: {last_error!r}"
        ) from last_error

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
    ) -> AsyncIterator[Any]:
        response = await self.client.chat.completions.create(
            model=model or self.model,
            messages=self._messages(system_prompt, user_prompt),
            stream=True,
        )

        async for chunk in response:
            yield chunk


# Backward-compatible names.
Llm = GroqProvider
AsyncLlm = AsyncGroqProvider


class PayloadResponse(BaseModel):
    content: str

