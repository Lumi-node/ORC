"""
Warrior - An agent that fights in The Arena.

A Warrior is a thin wrapper around the Agent protocol with ORC theming.
Each Warrior has a name, LLM client, system prompt, and capabilities.
"""

import random
from typing import Any, Dict, List, Optional, Union

from dynabots_core import TaskResult


class Warrior:
    """A Warrior is an agent that fights in The Arena.

    The wrapper is ORC-themed, but the arguments are standard AI concepts.

    Example:
        grog = Warrior(
            name="Grog",
            llm_client="gpt-4o",           # Standard AI model
            system_prompt="You are a senior python backend dev...",
            temperature=0.2,
            capabilities=["code_review", "debugging"],
            domains=["backend", "python"],
        )
    """

    def __init__(
        self,
        name: str,
        llm_client: Union[str, Any],
        system_prompt: str,
        temperature: float = 0.7,
        capabilities: Optional[List[str]] = None,
        domains: Optional[List[str]] = None,
    ):
        """
        Initialize a Warrior.

        Args:
            name: Warrior's name (unique identifier).
            llm_client: Either a string (model name) or LLMProvider instance.
            system_prompt: System prompt defining the warrior's expertise.
            temperature: LLM temperature (0-1). Default 0.7.
            capabilities: List of capabilities this warrior possesses.
            domains: List of domains this warrior claims expertise in.
        """
        self._name = name
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        self.temperature = temperature
        self._capabilities = capabilities or []
        self._domains = domains or []

    @property
    def name(self) -> str:
        """Unique warrior identifier."""
        return self._name

    @property
    def capabilities(self) -> List[str]:
        """List of capabilities this warrior supports."""
        return self._capabilities

    @property
    def domains(self) -> List[str]:
        """List of domains this warrior claims expertise in."""
        return self._domains

    async def process_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        """
        Execute a task.

        If llm_client is a string (model name), returns a mock success result.
        If llm_client is an LLMProvider instance, calls it to process the task.

        Args:
            task_description: Natural language description of the task.
            context: Execution context.

        Returns:
            TaskResult with the outcome.
        """
        context = context or {}
        task_id = context.get("task_id", "unknown")

        try:
            if isinstance(self.llm_client, str):
                # Mock mode: simulate variable performance
                duration = random.randint(50, 500)
                return TaskResult.success(
                    task_id=task_id,
                    data={
                        "response": f"Warrior {self.name} processed task: {task_description}",
                        "model": self.llm_client,
                    },
                    duration_ms=duration,
                )

            # Real LLM mode: call the provider
            if hasattr(self.llm_client, "complete"):
                from dynabots_core import LLMMessage
                import time

                start = time.perf_counter()
                response = await self.llm_client.complete(
                    messages=[
                        LLMMessage(role="system", content=self.system_prompt),
                        LLMMessage(role="user", content=task_description),
                    ],
                    temperature=self.temperature,
                )
                elapsed_ms = int((time.perf_counter() - start) * 1000)

                return TaskResult.success(
                    task_id=task_id,
                    data={
                        "response": response.content,
                        "model": getattr(self.llm_client, "model", "unknown"),
                    },
                    duration_ms=elapsed_ms,
                )
            else:
                return TaskResult.success(
                    task_id=task_id,
                    data={
                        "response": f"Warrior {self.name} processed task (no LLM): {task_description}"
                    },
                )

        except Exception as e:
            return TaskResult.failure(
                task_id=task_id,
                error=f"Warrior {self.name} failed to process task: {str(e)}",
            )

    async def health_check(self) -> bool:
        """Check if this warrior is healthy and ready to fight."""
        # Basic implementation: always healthy if instantiated
        return True
