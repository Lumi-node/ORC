"""
Anthropic Claude LLM Provider.

Requirements:
    pip install anthropic

Example:
    from anthropic import AsyncAnthropic
    from dynabots_core.providers import AnthropicProvider

    client = AsyncAnthropic(api_key="sk-ant-...")
    llm = AnthropicProvider(client, model="claude-3-5-sonnet-20241022")

    response = await llm.complete([
        LLMMessage(role="user", content="Hello!")
    ])
"""

from typing import Any, Dict, List, Optional

from dynabots_core.protocols.llm import (
    LLMMessage,
    LLMResponse,
    ToolDefinition,
)


class AnthropicProvider:
    """
    LLMProvider implementation for Anthropic Claude models.

    Example:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic()
        llm = AnthropicProvider(client, model="claude-3-5-sonnet-20241022")
    """

    def __init__(
        self,
        client: Any,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
    ) -> None:
        """
        Initialize the Anthropic provider.

        Args:
            client: An AsyncAnthropic client instance.
            model: Claude model ID.
            max_tokens: Default max tokens (Anthropic requires this).
        """
        self._client = client
        self._model = model
        self._default_max_tokens = max_tokens

    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        json_mode: bool = False,
        tools: Optional[List[ToolDefinition]] = None,
    ) -> LLMResponse:
        """
        Send messages to Anthropic and get a response.

        Args:
            messages: Conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum response tokens.
            json_mode: If True, append JSON instruction to system prompt.
            tools: Optional list of tools for function calling.

        Returns:
            LLMResponse with the model's output.
        """
        # Separate system message from conversation
        system_content = ""
        conversation_messages = []

        for msg in messages:
            if msg.role == "system":
                system_content += msg.content + "\n"
            else:
                conversation_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        # JSON mode: append instruction to system prompt
        if json_mode:
            system_content += "\n\nRespond with valid JSON only."

        kwargs: Dict[str, Any] = {
            "model": self._model,
            "messages": conversation_messages,
            "max_tokens": max_tokens or self._default_max_tokens,
            "temperature": temperature,
        }

        if system_content.strip():
            kwargs["system"] = system_content.strip()

        if tools:
            kwargs["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.parameters,
                }
                for t in tools
            ]

        response = await self._client.messages.create(**kwargs)

        # Extract content
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": block.input,
                    },
                })

        return LLMResponse(
            content=content,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": (
                    response.usage.input_tokens + response.usage.output_tokens
                ),
            },
            model=self._model,
            tool_calls=tool_calls if tool_calls else None,
            finish_reason=response.stop_reason,
        )

    @property
    def model(self) -> str:
        """Get the current model name."""
        return self._model
