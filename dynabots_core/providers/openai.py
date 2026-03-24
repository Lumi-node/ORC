"""
OpenAI / Azure OpenAI LLM Provider.

Supports both OpenAI and Azure OpenAI endpoints.

Requirements:
    pip install openai

Example (OpenAI):
    from openai import AsyncOpenAI
    from dynabots_core.providers import OpenAIProvider

    client = AsyncOpenAI(api_key="sk-...")
    llm = OpenAIProvider(client, model="gpt-4o")

Example (Azure OpenAI):
    from openai import AsyncAzureOpenAI
    from dynabots_core.providers import OpenAIProvider

    client = AsyncAzureOpenAI(
        azure_endpoint="https://my-resource.openai.azure.com",
        api_key="...",
        api_version="2024-02-01",
    )
    llm = OpenAIProvider(client, model="my-deployment-name")
"""

from typing import Any, Dict, List, Optional

from dynabots_core.protocols.llm import (
    LLMMessage,
    LLMResponse,
    ToolDefinition,
)


class OpenAIProvider:
    """
    LLMProvider implementation for OpenAI and Azure OpenAI.

    Example:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key="sk-...")
        llm = OpenAIProvider(client, model="gpt-4o")

        response = await llm.complete([
            LLMMessage(role="user", content="Hello!")
        ])
    """

    def __init__(self, client: Any, model: str = "gpt-4o") -> None:
        """
        Initialize the OpenAI provider.

        Args:
            client: An AsyncOpenAI or AsyncAzureOpenAI client instance.
            model: Model name (OpenAI) or deployment name (Azure).
        """
        self._client = client
        self._model = model

    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        json_mode: bool = False,
        tools: Optional[List[ToolDefinition]] = None,
    ) -> LLMResponse:
        """
        Send messages to OpenAI and get a response.

        Args:
            messages: Conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum response tokens.
            json_mode: If True, request JSON-formatted output.
            tools: Optional list of tools for function calling.

        Returns:
            LLMResponse with the model's output.
        """
        kwargs: Dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": m.role, "content": m.content}
                for m in messages
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        if tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]

        response = await self._client.chat.completions.create(**kwargs)

        # Extract usage
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        # Extract tool calls
        tool_calls = None
        if response.choices[0].message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in response.choices[0].message.tool_calls
            ]

        return LLMResponse(
            content=response.choices[0].message.content or "",
            usage=usage,
            model=self._model,
            tool_calls=tool_calls,
            finish_reason=response.choices[0].finish_reason,
        )

    @property
    def model(self) -> str:
        """Get the current model name."""
        return self._model
