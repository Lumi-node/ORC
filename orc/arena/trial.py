"""
Trial - The competition mechanism in Orc!!

A Trial is executed when an agent challenges the current Warlord.
Both agents attempt the same task, and a Judge determines the winner.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

from dynabots_core import Agent, TaskResult, Judge, Verdict
from dynabots_core.protocols.judge import Submission


@dataclass
class TrialResult:
    """
    Result of a trial between two agents.

    Attributes:
        task: The task that was executed
        domain: The domain being contested
        winner: Name of the winning agent
        winner_result: TaskResult from the winner
        was_challenged: Whether this was a contested trial
        verdict: Judge's verdict (if challenged)
        warlord_result: TaskResult from the warlord
        challenger_result: TaskResult from the challenger
        trial_id: Unique trial identifier
        timestamp: When the trial completed
        duration_ms: Total trial duration in milliseconds
    """

    task: str
    domain: str
    winner: str
    winner_result: TaskResult
    was_challenged: bool
    verdict: Optional[Verdict]
    warlord_result: Optional[TaskResult] = None
    challenger_result: Optional[TaskResult] = None
    trial_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: Optional[int] = None

    @property
    def data(self) -> Any:
        """Get the winning result's data."""
        return self.winner_result.data if self.winner_result else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "trial_id": self.trial_id,
            "task": self.task,
            "domain": self.domain,
            "winner": self.winner,
            "was_challenged": self.was_challenged,
            "verdict": self.verdict.to_dict() if self.verdict else None,
            "warlord_result": self.warlord_result.to_dict() if self.warlord_result else None,
            "challenger_result": self.challenger_result.to_dict() if self.challenger_result else None,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
        }


class Trial:
    """
    Executes a trial between a Warlord and Challenger.

    Example:
        trial = Trial(
            task="Analyze Q4 sales data",
            domain="data",
            warlord=data_agent,
            challenger=analytics_agent,
            judge=llm_judge,
        )

        result = await trial.execute()
        print(f"Winner: {result.winner}")
    """

    def __init__(
        self,
        task: str,
        domain: str,
        warlord: Agent,
        challenger: Agent,
        judge: Judge,
        context: Optional[Dict[str, Any]] = None,
        timeout: int = 300,
        parallel: bool = True,
    ):
        """
        Initialize a trial.

        Args:
            task: The task to execute.
            domain: The domain being contested.
            warlord: The current Warlord agent.
            challenger: The challenging agent.
            judge: Judge to evaluate outcomes.
            context: Execution context.
            timeout: Timeout for each agent's execution (seconds).
            parallel: Whether to execute agents in parallel.
        """
        self.task = task
        self.domain = domain
        self.warlord = warlord
        self.challenger = challenger
        self.judge = judge
        self.context = context or {}
        self.timeout = timeout
        self.parallel = parallel
        self.trial_id = str(uuid.uuid4())

    async def execute(self) -> TrialResult:
        """
        Execute the trial.

        Both agents attempt the task. The Judge evaluates the results
        and determines a winner.

        Returns:
            TrialResult with the outcome.
        """
        start_time = datetime.now(timezone.utc)

        # Build contexts for each agent
        warlord_context = {
            **self.context,
            "task_id": f"{self.trial_id}_warlord",
            "trial_id": self.trial_id,
            "role": "warlord",
        }
        challenger_context = {
            **self.context,
            "task_id": f"{self.trial_id}_challenger",
            "trial_id": self.trial_id,
            "role": "challenger",
        }

        # Execute both agents
        if self.parallel:
            warlord_result, challenger_result = await self._execute_parallel(
                warlord_context, challenger_context
            )
        else:
            warlord_result = await self._execute_single(self.warlord, warlord_context)
            challenger_result = await self._execute_single(self.challenger, challenger_context)

        # Build submissions for judge
        submissions = [
            Submission(
                agent=self.warlord.name,
                result=warlord_result,
                latency_ms=warlord_result.duration_ms,
            ),
            Submission(
                agent=self.challenger.name,
                result=challenger_result,
                latency_ms=challenger_result.duration_ms,
            ),
        ]

        # Judge evaluates
        verdict = await self.judge.evaluate(self.task, submissions)

        # Determine winner (ties go to the defending warlord)
        winner = verdict.winner
        if verdict.is_tie or winner not in (self.warlord.name, self.challenger.name):
            winner = self.warlord.name
        winner_result = (
            warlord_result if winner == self.warlord.name else challenger_result
        )

        # Calculate duration
        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

        return TrialResult(
            task=self.task,
            domain=self.domain,
            winner=winner,
            winner_result=winner_result,
            was_challenged=True,
            verdict=verdict,
            warlord_result=warlord_result,
            challenger_result=challenger_result,
            trial_id=self.trial_id,
            duration_ms=duration_ms,
        )

    async def _execute_parallel(
        self,
        warlord_context: Dict[str, Any],
        challenger_context: Dict[str, Any],
    ) -> tuple[TaskResult, TaskResult]:
        """Execute both agents in parallel."""
        results = await asyncio.gather(
            self._execute_single(self.warlord, warlord_context),
            self._execute_single(self.challenger, challenger_context),
            return_exceptions=True,
        )

        warlord_result = results[0]
        challenger_result = results[1]

        # Handle exceptions
        if isinstance(warlord_result, Exception):
            warlord_result = TaskResult.failure(
                task_id=warlord_context["task_id"],
                error=str(warlord_result),
            )
        if isinstance(challenger_result, Exception):
            challenger_result = TaskResult.failure(
                task_id=challenger_context["task_id"],
                error=str(challenger_result),
            )

        return warlord_result, challenger_result

    async def _execute_single(
        self,
        agent: Agent,
        context: Dict[str, Any],
    ) -> TaskResult:
        """Execute a single agent with timeout."""
        start_time = datetime.now(timezone.utc)

        try:
            result = await asyncio.wait_for(
                agent.process_task(self.task, context),
                timeout=self.timeout,
            )

            # Add duration if not set
            if result.duration_ms is None:
                duration_ms = int(
                    (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                )
                # TaskResult is frozen, so we need to create a new one
                result = TaskResult(
                    task_id=result.task_id,
                    outcome=result.outcome,
                    data=result.data,
                    metadata=result.metadata,
                    should_continue=result.should_continue,
                    skip_reason=result.skip_reason,
                    timestamp=result.timestamp,
                    duration_ms=duration_ms,
                    error_message=result.error_message,
                )

            return result

        except asyncio.TimeoutError:
            return TaskResult.failure(
                task_id=context["task_id"],
                error=f"Timeout after {self.timeout}s",
            )
        except Exception as e:
            return TaskResult.failure(
                task_id=context["task_id"],
                error=str(e),
            )
