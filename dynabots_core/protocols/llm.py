"""
LLM provider protocol.

Defines the contract for language model providers. Any LLM service
(OpenAI, Anthropic, Ollama, vLLM, etc.) can be used with DynaBots
frameworks by implementing this protocol.

Example:
    from dynabots_core import LLMProvider, LLMMessage, LLMResponse

    class MyLLMProvider:
        async def complete(self, messages, **kwargs) -> LLMResponse:
            # Call your LLM
            response = await my_llm_client.chat(messages)
            return LLMResponse(content=response.text)

    # Use it
    llm = MyLLMProvider()
    response = await llm.complete([
        LLMMessage(role="user", content="Hello!")
    ])
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@dataclass
class LLMMessage:
    """
    A single message in an LLM conversation.

    Attributes:
        role: Message role - "system", "user", or "assistant"
        content: Message content (text)
        name: Optional name for the message sender
        tool_calls: Optional list of tool calls (for assistant messages)
        tool_call_id: Optional ID linking to a tool call (for tool messages)

    Example:
        messages = [
            LLMMessage(role="system", content="You are a helpful assistant."),
            LLMMessage(role="user", content="What's 2+2?"),
            LLMMessage(role="assistant", content="2+2 equals 4."),
        ]
    """

    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


@dataclass
class LLMResponse:
    """
    Response from an LLM provider.

    Attributes:
        content: The model's response text
        usage: Optional token usage statistics
        model: Optional model identifier
        tool_calls: Optional list of tool calls requested by the model
        finish_reason: Why the model stopped generating (stop, length, tool_calls)

    Example:
        response = await provider.complete(messages)
        print(response.content)
        print(f"Tokens used: {response.usage.get('total_tokens', 'unknown')}")
    """

    content: str
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: Optional[str] = None


@dataclass
class ToolDefinition:
    """
    Definition of a tool that can be called by the LLM.

    Attributes:
        name: Tool name (function name)
        description: What the tool does
        parameters: JSON Schema for the parameters

    Example:
        search_tool = ToolDefinition(
            name="search_database",
            description="Search the database for records",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            }
        )
    """

    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    """
    Protocol for LLM providers.

    Implementations wrap a specific LLM service behind a uniform interface.
    This enables LLM-agnostic orchestration - swap providers without changing
    your agent code.

    Required method:
    - complete: Send messages and get a response

    Optional features (check implementation):
    - Tool calling: Pass tools parameter to enable function calling
    - JSON mode: Set json_mode=True for structured output
    - Streaming: Some implementations may offer streaming variants

    Example implementation:
        class OllamaProvider:
            def __init__(self, model: str = "llama3.1:70b"):
                self.model = model
                self.client = ollama.AsyncClient()

            async def complete(
                self,
                messages: list[LLMMessage],
                temperature: float = 0.1,
                max_tokens: int = 2000,
                json_mode: bool = False,
                tools: list[ToolDefinition] | None = None,
            ) -> LLMResponse:
                response = await self.client.chat(
                    model=self.model,
                    messages=[{"role": m.role, "content": m.content} for m in messages],
                    options={"temperature": temperature, "num_predict": max_tokens},
                    format="json" if json_mode else None,
                )
                return LLMResponse(
                    content=response["message"]["content"],
                    model=self.model,
                )
    """

    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        json_mode: bool = False,
        tools: Optional[List[ToolDefinition]] = None,
    ) -> LLMResponse:
        """
        Send messages to the LLM and get a response.

        Args:
            messages: Conversation messages (system, user, assistant, tool).
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
            max_tokens: Maximum tokens in the response.
            json_mode: If True, request JSON-formatted output.
            tools: Optional list of tools the LLM can call.

        Returns:
            LLMResponse with the model's response text and optional metadata.

        Raises:
            Exception: If the LLM call fails (implementation-specific).
        """
        ...
