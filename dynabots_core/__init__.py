"""
DynaBots Core - Shared primitives for the DynaBots orchestration framework family.

This package provides:
- Protocols: Agent, LLMProvider, Judge, Tool
- Value Objects: TaskResult, LLMMessage, LLMResponse, Verdict
- Providers: OpenAI, Ollama, Anthropic adapters

Example:
    from dynabots_core import Agent, TaskResult, LLMProvider
    from dynabots_core.providers import OllamaProvider

    # Create a local LLM provider
    llm = OllamaProvider(model="qwen2.5:72b")

    # Define your agent
    class MyAgent:
        @property
        def name(self) -> str:
            return "MyAgent"

        async def process_task(self, task: str, context: dict) -> TaskResult:
            return TaskResult.success(task_id=context["task_id"], data="done")
"""

from dynabots_core.protocols.agent import Agent
from dynabots_core.protocols.llm import LLMProvider, LLMMessage, LLMResponse
from dynabots_core.protocols.judge import Judge, Verdict
from dynabots_core.protocols.tool import Tool
from dynabots_core.protocols.storage import ExecutionStore, AuditStore, CacheStore, ReputationStore
from dynabots_core.protocols.swarm import (
    SwarmParticipant,
    SwarmParticipantWithStatus,
    SwarmMessageBus,
)
from dynabots_core.value_objects.task_result import TaskResult, TaskOutcome

__version__ = "0.1.0"

__all__ = [
    # Protocols - Agent
    "Agent",
    # Protocols - LLM
    "LLMProvider",
    "LLMMessage",
    "LLMResponse",
    # Protocols - Judge
    "Judge",
    "Verdict",
    # Protocols - Tool
    "Tool",
    # Protocols - Storage
    "ExecutionStore",
    "AuditStore",
    "CacheStore",
    "ReputationStore",
    # Protocols - Swarm
    "SwarmParticipant",
    "SwarmParticipantWithStatus",
    "SwarmMessageBus",
    # Value Objects
    "TaskResult",
    "TaskOutcome",
]
