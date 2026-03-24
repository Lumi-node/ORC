"""
Judge protocol.

Defines the contract for evaluating agent submissions in competitive
orchestration frameworks like Orc!!.

Judges compare multiple agent outputs for the same task and determine
a winner. They can be:
- LLM-based: Use an LLM to evaluate quality
- Metrics-based: Use objective measurements (latency, accuracy, cost)
- Consensus-based: Multiple judges vote
- Human-in-the-loop: Escalate to human reviewers

Example:
    from dynabots_core import Judge, Verdict

    class LLMJudge:
        def __init__(self, llm: LLMProvider):
            self.llm = llm

        async def evaluate(self, task: str, submissions: list[dict]) -> Verdict:
            prompt = f'''
            Task: {task}

            Submission A ({submissions[0]["agent"]}):
            {submissions[0]["result"]}

            Submission B ({submissions[1]["agent"]}):
            {submissions[1]["result"]}

            Which submission better accomplishes the task?
            Consider: accuracy, completeness, clarity, efficiency.
            '''

            response = await self.llm.complete([
                LLMMessage(role="user", content=prompt)
            ])

            # Parse response to determine winner
            winner = self._parse_winner(response.content)
            return Verdict(
                winner=winner,
                reasoning=response.content,
                scores={"A": 0.8, "B": 0.6}
            )
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from datetime import datetime, timezone


@dataclass
class Verdict:
    """
    The result of a judge's evaluation.

    Attributes:
        winner: Name of the winning agent
        reasoning: Explanation of why this agent won
        scores: Optional per-agent scores (agent_name -> score)
        confidence: Judge's confidence in the verdict (0.0-1.0)
        metadata: Additional evaluation metadata
        timestamp: When the verdict was rendered

    Example:
        verdict = Verdict(
            winner="DataAgent",
            reasoning="DataAgent provided more complete results with proper error handling.",
            scores={"DataAgent": 0.85, "ReportAgent": 0.72},
            confidence=0.9
        )
    """

    winner: str
    reasoning: str
    scores: Dict[str, float] = field(default_factory=dict)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_tie(self) -> bool:
        """Check if the verdict is a tie (no clear winner)."""
        return self.winner == "" or self.winner.lower() == "tie"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "winner": self.winner,
            "reasoning": self.reasoning,
            "scores": self.scores,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "is_tie": self.is_tie,
        }


@dataclass
class Submission:
    """
    An agent's submission for evaluation.

    Attributes:
        agent: Name of the agent that produced this submission
        result: The agent's output (TaskResult or raw data)
        latency_ms: How long the agent took (milliseconds)
        cost: Cost of producing this result (e.g., API costs)
        metadata: Additional submission metadata
    """

    agent: str
    result: Any
    latency_ms: Optional[int] = None
    cost: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent": self.agent,
            "result": self.result if not hasattr(self.result, "to_dict") else self.result.to_dict(),
            "latency_ms": self.latency_ms,
            "cost": self.cost,
            "metadata": self.metadata,
        }


@runtime_checkable
class Judge(Protocol):
    """
    Protocol for evaluating agent submissions.

    Judges are used in competitive orchestration frameworks (like Orc!!)
    to determine which agent performed better on a given task.

    Implementations can use various strategies:
    - LLM evaluation (ask another model to judge)
    - Metric-based evaluation (latency, accuracy, cost)
    - Consensus voting (multiple judges)
    - Domain-specific rules

    Example implementation:
        class MetricsJudge:
            async def evaluate(self, task: str, submissions: list[Submission]) -> Verdict:
                scores = {}
                for sub in submissions:
                    score = 0.0
                    # Accuracy bonus
                    if self._check_correctness(sub.result):
                        score += 50
                    # Speed bonus
                    if sub.latency_ms and sub.latency_ms < 1000:
                        score += 25
                    # Cost efficiency bonus
                    if sub.cost and sub.cost < 0.01:
                        score += 25
                    scores[sub.agent] = score

                winner = max(scores, key=scores.get)
                return Verdict(
                    winner=winner,
                    reasoning=f"Highest combined score: {scores[winner]}",
                    scores=scores
                )
    """

    async def evaluate(
        self,
        task: str,
        submissions: List[Submission],
    ) -> Verdict:
        """
        Evaluate multiple submissions and determine a winner.

        Args:
            task: The original task description.
            submissions: List of agent submissions to evaluate.

        Returns:
            Verdict indicating the winner and reasoning.

        Note:
            - Submissions should have at least 2 entries for meaningful comparison
            - If submissions are equivalent, return a tie (winner="tie")
            - Include detailed reasoning for transparency
        """
        ...


@runtime_checkable
class ScoringJudge(Protocol):
    """
    Extended judge protocol that provides individual scores.

    Use this when you need to score submissions independently,
    not just compare them against each other.
    """

    async def score(self, task: str, submission: Submission) -> float:
        """
        Score a single submission (0.0 to 1.0).

        Args:
            task: The original task description.
            submission: Single agent submission to score.

        Returns:
            Score between 0.0 (worst) and 1.0 (best).
        """
        ...

    async def evaluate(
        self,
        task: str,
        submissions: List[Submission],
    ) -> Verdict:
        """Evaluate by scoring each submission and comparing."""
        ...
