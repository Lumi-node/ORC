"""
Deployment Runtime Protocol

Abstraction for agent deployment across different container/process runtimes.
Enables clean transition from development (native) to production (K8s) without
changing orchestration logic.

Design principle: Security through simplicity.
"""

from typing import Protocol, Optional, Dict, Any, List, runtime_checkable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class RuntimeType(Enum):
    """Supported runtime types"""
    NATIVE = "native"      # Direct subprocess
    DOCKER = "docker"      # Docker containers
    K3S = "k3s"           # Lightweight Kubernetes
    KUBERNETES = "kubernetes"  # Full Kubernetes


class AgentState(Enum):
    """Agent lifecycle states"""
    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class DeploymentConfig:
    """Configuration for deploying an agent"""
    agent_id: str
    image: str  # Container image or executable path

    # Resource limits (optional, runtime-dependent)
    cpu_limit: Optional[str] = None      # e.g., "0.5" or "500m"
    memory_limit: Optional[str] = None   # e.g., "256Mi"

    # Networking
    port: Optional[int] = None
    expose_port: bool = False

    # Environment
    env: Dict[str, str] = field(default_factory=dict)

    # Runtime-specific options
    labels: Dict[str, str] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)

    # Restart policy
    restart_on_failure: bool = True
    max_restarts: int = 3


@dataclass
class DeployedAgent:
    """Information about a deployed agent"""
    agent_id: str
    runtime_type: RuntimeType
    state: AgentState
    endpoint: Optional[str] = None  # How to reach this agent

    # Runtime-specific identifiers
    container_id: Optional[str] = None
    process_id: Optional[int] = None
    pod_name: Optional[str] = None

    # Metadata
    started_at: Optional[datetime] = None
    labels: Dict[str, str] = field(default_factory=dict)

    def is_running(self) -> bool:
        return self.state == AgentState.RUNNING


@runtime_checkable
class DeploymentRuntime(Protocol):
    """
    Protocol for agent deployment runtimes.

    Implementations provide the actual mechanism for starting/stopping agents
    whether via subprocess, Docker, K3s, or full Kubernetes.

    Example:
        runtime = NativeRuntime()

        config = DeploymentConfig(
            agent_id="zeroclaw-1",
            image="/path/to/zeroclaw",
            env={"SWARM_ID": "swarm-123"}
        )

        agent = await runtime.deploy(config)
        print(f"Agent running at {agent.endpoint}")

        # Later...
        await runtime.stop(agent.agent_id)
    """

    @property
    def runtime_type(self) -> RuntimeType:
        """Return the runtime type"""
        ...

    async def deploy(self, config: DeploymentConfig) -> DeployedAgent:
        """
        Deploy an agent with the given configuration.

        Args:
            config: Deployment configuration

        Returns:
            DeployedAgent with endpoint and state info

        Raises:
            RuntimeError: If deployment fails
        """
        ...

    async def stop(self, agent_id: str, force: bool = False) -> bool:
        """
        Stop a deployed agent.

        Args:
            agent_id: Agent identifier
            force: Force stop (SIGKILL vs SIGTERM)

        Returns:
            True if stopped successfully
        """
        ...

    async def get_state(self, agent_id: str) -> Optional[DeployedAgent]:
        """
        Get current state of a deployed agent.

        Args:
            agent_id: Agent identifier

        Returns:
            DeployedAgent or None if not found
        """
        ...

    async def list_agents(self, labels: Optional[Dict[str, str]] = None) -> List[DeployedAgent]:
        """
        List deployed agents, optionally filtered by labels.

        Args:
            labels: Filter by labels (all must match)

        Returns:
            List of deployed agents
        """
        ...

    async def scale(self, agent_id: str, replicas: int) -> List[DeployedAgent]:
        """
        Scale an agent to the specified number of replicas.

        Note: Only meaningful for container runtimes. NativeRuntime
        may raise NotImplementedError or spawn multiple processes.

        Args:
            agent_id: Base agent identifier
            replicas: Desired replica count

        Returns:
            List of all replicas
        """
        ...

    async def get_logs(
        self,
        agent_id: str,
        tail: int = 100,
        since: Optional[datetime] = None
    ) -> str:
        """
        Get logs from an agent.

        Args:
            agent_id: Agent identifier
            tail: Number of lines from end
            since: Only logs after this time

        Returns:
            Log output as string
        """
        ...

    async def health_check(self, agent_id: str) -> bool:
        """
        Check if agent is healthy.

        Args:
            agent_id: Agent identifier

        Returns:
            True if healthy
        """
        ...


@runtime_checkable
class RuntimeWithMetrics(Protocol):
    """Extended runtime protocol with resource metrics"""

    async def get_metrics(self, agent_id: str) -> Dict[str, Any]:
        """
        Get resource usage metrics for an agent.

        Returns:
            Dict with cpu_percent, memory_mb, network_rx, network_tx, etc.
        """
        ...


@runtime_checkable
class RuntimeWithExec(Protocol):
    """Extended runtime protocol with exec capability"""

    async def exec(self, agent_id: str, command: List[str]) -> tuple[int, str, str]:
        """
        Execute a command inside the agent's environment.

        Args:
            agent_id: Agent identifier
            command: Command and arguments

        Returns:
            (exit_code, stdout, stderr)
        """
        ...
