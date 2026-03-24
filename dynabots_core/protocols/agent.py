"""
Agent protocol.

Defines the contract that all agents must satisfy to participate
in DynaBots orchestration frameworks (DynaBots, Orc!!, etc.).

Agents can implement either or both execution modes:
- process_task (Smart Mode): Agent uses its own LLM to pick tools
- execute_capability (Legacy Mode): Direct capability routing

Example:
    class DataAgent:
        @property
        def name(self) -> str:
            return "DataAgent"

        @property
        def capabilities(self) -> list[str]:
            return ["fetch_data", "query_database", "transform"]

        @property
        def domains(self) -> list[str]:
            return ["data", "etl", "database"]

        async def process_task(self, task_description, context):
            # Use own LLM to decide which tool to call
            ...
            return TaskResult.success(task_id=context["task_id"], data=result)

        async def health_check(self) -> bool:
            return True
"""

from typing import Any, Dict, List, Protocol, runtime_checkable

# Import from sibling module to avoid circular imports
# TaskResult will be imported at runtime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dynabots_core.value_objects.task_result import TaskResult


@runtime_checkable
class Agent(Protocol):
    """
    Protocol for agents that participate in DynaBots orchestration.

    Required properties:
    - name: Unique agent identifier
    - capabilities: List of capability names this agent supports

    Optional properties:
    - domains: Domain keywords for intelligent routing (e.g., ["data", "etl"])
    - description: Human-readable description

    Required methods:
    - process_task: Execute a task described in natural language
    - health_check: Liveness check

    Optional methods:
    - execute_capability: Direct capability execution (legacy mode)
    """

    @property
    def name(self) -> str:
        """Unique agent identifier."""
        ...

    @property
    def capabilities(self) -> List[str]:
        """List of capability names this agent supports."""
        ...

    async def process_task(
        self,
        task_description: str,
        context: Dict[str, Any],
    ) -> "TaskResult":
        """
        Smart Mode: Execute a task described in natural language.

        The agent uses its own LLM and tool schemas to decide how
        to accomplish the task. This is the preferred execution mode.

        Args:
            task_description: Natural language description of what to do.
            context: Execution context including:
                - task_id: Unique task identifier
                - workflow_id: Parent workflow ID
                - parent_results: Results from upstream tasks
                - user_context: User information (email, etc.)

        Returns:
            TaskResult with the execution outcome.

        Example:
            async def process_task(self, task_description, context):
                # Use your agent's LLM to understand the task
                plan = await self.llm.plan(task_description, self.tools)

                # Execute the plan
                result = await self.execute_plan(plan)

                return TaskResult.success(
                    task_id=context["task_id"],
                    data=result
                )
        """
        ...

    async def health_check(self) -> bool:
        """
        Check if this agent is healthy and ready to process tasks.

        Returns:
            True if healthy, False otherwise.

        Example:
            async def health_check(self) -> bool:
                try:
                    await self.db.ping()
                    return True
                except Exception:
                    return False
        """
        ...


@runtime_checkable
class LegacyAgent(Protocol):
    """
    Extended agent protocol with legacy capability execution support.

    Use this when migrating from direct capability routing to smart mode.
    """

    @property
    def name(self) -> str:
        ...

    @property
    def capabilities(self) -> List[str]:
        ...

    async def execute_capability(
        self,
        capability: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> "TaskResult":
        """
        Legacy Mode: Execute a specific capability with given parameters.

        This bypasses the agent's LLM and directly executes a capability.
        Use process_task instead for new implementations.

        Args:
            capability: Name of the capability to execute.
            parameters: Parameters for the capability.
            context: Execution context.

        Returns:
            TaskResult with the execution outcome.
        """
        ...

    async def health_check(self) -> bool:
        ...
