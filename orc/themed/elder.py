"""
Elder - The judge in The Arena.

An Elder evaluates battles between Warriors and determines the winner.
It wraps the Judge protocol with ORC theming.
"""

from typing import Any, List, Optional

from dynabots_core import Verdict
from dynabots_core.protocols.judge import Judge, Submission
from orc.judges import LLMJudge, MetricsJudge


class Elder:
    """The Elder judges combat between Warriors.

    Example:
        elder = Elder(
            evaluator_model="claude-3-opus",
            evaluation_criteria="Judge based on code quality and efficiency.",
        )

        # Or with a pre-built judge:
        elder = Elder(judge=MetricsJudge(weights={"accuracy": 0.7, "latency": 0.3}))
    """

    def __init__(
        self,
        evaluator_model: Optional[str] = None,
        evaluation_criteria: Optional[str] = None,
        judge: Optional[Judge] = None,
        llm: Optional[Any] = None,
    ):
        """
        Initialize an Elder.

        Args:
            evaluator_model: LLM model to use for evaluation (e.g., "claude-3-opus").
            evaluation_criteria: Custom criteria for evaluation.
            judge: Pre-built Judge instance (overrides evaluator_model if provided).
            llm: LLMProvider instance for LLM-based judging.
        """
        self.evaluator_model = evaluator_model
        self.evaluation_criteria = evaluation_criteria
        self._llm = llm
        self._judge = judge

    @property
    def judge(self) -> Judge:
        """Get or create the underlying Judge instance."""
        if self._judge is not None:
            return self._judge

        # If an LLM provider was given, use LLMJudge
        if self._llm is not None:
            criteria = (
                [c.strip() for c in self.evaluation_criteria.split(",")]
                if self.evaluation_criteria
                else None
            )
            self._judge = LLMJudge(self._llm, criteria=criteria)
        else:
            # Default to MetricsJudge
            self._judge = MetricsJudge()

        return self._judge

    async def evaluate(
        self,
        task: str,
        submissions: List[Submission],
    ) -> Verdict:
        """
        Evaluate warrior submissions and determine the victor.

        Args:
            task: The task/challenge description.
            submissions: List of warrior submissions (typically 2).

        Returns:
            Verdict with the winner and reasoning.
        """
        return await self.judge.evaluate(task, submissions)
