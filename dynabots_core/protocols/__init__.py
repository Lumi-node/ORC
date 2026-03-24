"""
Core protocols for the DynaBots framework family.

Protocols define contracts that implementations must satisfy.
They enable loose coupling and easy swapping of components.
"""

from dynabots_core.protocols.agent import Agent
from dynabots_core.protocols.llm import LLMProvider, LLMMessage, LLMResponse
from dynabots_core.protocols.judge import Judge, Verdict
from dynabots_core.protocols.tool import Tool
from dynabots_core.protocols.storage import ExecutionStore, AuditStore, CacheStore
from dynabots_core.protocols.swarm import (
    SwarmParticipant,
    SwarmParticipantWithStatus,
    SwarmMessageBus,
)
from dynabots_core.protocols.runtime import (
    DeploymentRuntime,
    RuntimeType,
    AgentState,
    DeploymentConfig,
    DeployedAgent,
    RuntimeWithMetrics,
    RuntimeWithExec,
)

__all__ = [
    # Agent
    "Agent",
    # LLM
    "LLMProvider",
    "LLMMessage",
    "LLMResponse",
    # Judge
    "Judge",
    "Verdict",
    # Tool
    "Tool",
    # Storage
    "ExecutionStore",
    "AuditStore",
    "CacheStore",
    # Swarm
    "SwarmParticipant",
    "SwarmParticipantWithStatus",
    "SwarmMessageBus",
    # Runtime
    "DeploymentRuntime",
    "RuntimeType",
    "AgentState",
    "DeploymentConfig",
    "DeployedAgent",
    "RuntimeWithMetrics",
    "RuntimeWithExec",
]
