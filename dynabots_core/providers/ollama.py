"""
Ollama LLM Provider.

Enables using local LLMs via Ollama with the DynaBots frameworks.
This is the recommended provider for local/self-hosted deployments.

Requirements:
    pip install ollama

Setup:
    1. Install Ollama: https://ollama.ai
    2. Pull a model: ollama pull qwen2.5:72b
    3. Start Ollama: ollama serve

Example:
    from dynabots_core.providers import OllamaProvider
    from dynabots_core import LLMMessage

    llm = OllamaProvider(model="qwen2.5:72b")

    response = await llm.complete([
        LLMMessage(role="system", content="You are a helpful assistant."),
        LLMMessage(role="user", content="What's 2+2?")
    ])
    print(response.content)  # "4"

Recommended models for autonomous agents:
    - qwen2.5:72b - Best overall for tool use and reasoning
    - llama3.1:70b - Strong reasoning, good tool use
    - mixtral:8x22b - Fast, good for simpler tasks
    - codellama:70b - Best for code-related tasks
"""

from typing import Any, Dict, List, Optional

from dynabots_core.protocols.llm import (
    LLMMessage,
    LLMProvider,
    LLMResponse,
    ToolDefinition,
)


class OllamaProvider:
    """
    LLMProvider implementation for Ollama (local LLMs).

    Supports:
    - All Ollama models (Llama, Qwen, Mixtral, CodeLlama, etc.)
    - JSON mode for structured output
    - Tool calling (model-dependent)
    - Custom Ollama server URLs

    Example:
        # Basic usage
        llm = OllamaProvider(model="qwen2.5:72b")

        # Custom server
        llm = OllamaProvider(
            model="llama3.1:70b",
            host="http://gpu-server:11434"
        )

        # With options
        llm = OllamaProvider(
            model="qwen2.5:72b",
            options={"num_gpu": 2, "num_ctx": 8192}
        )
    """

    def __init__(
        self,
        model: str = "qwen2.5:72b",
        host: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize the Ollama provider.

        Args:
            model: Ollama model name (e.g., "qwen2.5:72b", "llama3.1:70b").
            host: Ollama server URL. Defaults to http://localhost:11434.
            options: Additional Ollama options (num_gpu, num_ctx, etc.).
        """
        try:
            import ollama
        except ImportError:
            raise ImportError(
                "ollama package not installed. Install with: pip install ollama"
            )

        self._model = model
        self._host = host
        self._options = options or {}
        self._client = ollama.AsyncClient(host=host) if host else ollama.AsyncClient()

    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        json_mode: bool = False,
        tools: Optional[List[ToolDefinition]] = None,
    ) -> LLMResponse:
        """
        Send messages to Ollama and get a response.

        Args:
            messages: Conversation messages.
            temperature: Sampling temperature (0.0-1.0).
            max_tokens: Maximum response tokens.
            json_mode: If True, request JSON-formatted output.
            tools: Optional list of tools (requires compatible model).

        Returns:
            LLMResponse with the model's output.
        """
        # Convert messages to Ollama format
        ollama_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        # Build options
        options = {
            **self._options,
            "temperature": temperature,
            "num_predict": max_tokens,
        }

        # Build request kwargs
        kwargs: Dict[str, Any] = {
            "model": self._model,
            "messages": ollama_messages,
            "options": options,
        }

        # JSON mode
        if json_mode:
            kwargs["format"] = "json"

        # Tool calling (if supported by model)
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

        # Make the request
        response = await self._client.chat(**kwargs)

        # Extract tool calls if present
        tool_calls = None
        if "message" in response and "tool_calls" in response["message"]:
            tool_calls = response["message"]["tool_calls"]

        # Build response
        return LLMResponse(
            content=response["message"]["content"],
            model=self._model,
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0),
                "total_tokens": (
                    response.get("prompt_eval_count", 0)
                    + response.get("eval_count", 0)
                ),
            },
        )

    async def list_models(self) -> List[str]:
        """List available models on the Ollama server."""
        response = await self._client.list()
        return [model["name"] for model in response["models"]]

    async def pull_model(self, model: str) -> None:
        """Pull a model from the Ollama library."""
        await self._client.pull(model)

    @property
    def model(self) -> str:
        """Get the current model name."""
        return self._model
