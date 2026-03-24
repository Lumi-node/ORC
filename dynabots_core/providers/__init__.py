"""
LLM Provider implementations for the DynaBots framework family.

Providers wrap specific LLM services behind the LLMProvider protocol,
enabling LLM-agnostic orchestration.

Available providers:
- OllamaProvider: Local LLMs via Ollama
- OpenAIProvider: OpenAI and Azure OpenAI
- AnthropicProvider: Anthropic Claude models

Example:
    # Local LLM
    from dynabots_core.providers import OllamaProvider
    llm = OllamaProvider(model="qwen2.5:72b")

    # OpenAI
    from dynabots_core.providers import OpenAIProvider
    from openai import AsyncOpenAI
    llm = OpenAIProvider(AsyncOpenAI(), model="gpt-4o")

    # Anthropic
    from dynabots_core.providers import AnthropicProvider
    from anthropic import AsyncAnthropic
    llm = AnthropicProvider(AsyncAnthropic(), model="claude-3-5-sonnet-20241022")
"""

from dynabots_core.providers.ollama import OllamaProvider
from dynabots_core.providers.openai import OpenAIProvider
from dynabots_core.providers.anthropic import AnthropicProvider

__all__ = ["OllamaProvider", "OpenAIProvider", "AnthropicProvider"]
