"""
Metrics-based Judge.

Evaluates submissions based on objective metrics like latency, accuracy, and cost.
"""

from typing import Callable, Dict, List, Optional

from dynabots_core import Verdict
from dynabots_core.protocols.judge import Judge, Submission


class MetricsJudge:
    """
    Judge that evaluates based on objective metrics.

    Uses configurable weights for different metrics to calculate
    a final score for each submission.

    Example:
        judge = MetricsJudge(
            weights={"accuracy": 0.5, "latency": 0.3, "cost": 0.2},
            accuracy_checker=my_accuracy_function,
        )

        verdict = await judge.evaluate(task, submissions)
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        accuracy_checker: Optional[Callable] = None,
        latency_threshold_ms: int = 5000,
        cost_threshold: float = 0.10,
    ):
        """
        Initialize the Metrics Judge.

        Args:
            weights: Metric weights (must sum to 1.0).
            accuracy_checker: Function to check result accuracy (returns 0.0-1.0).
            latency_threshold_ms: Latency above this gets score 0.
            cost_threshold: Cost above this gets score 0.
        """
        self.weights = weights or {"accuracy": 0.5, "latency": 0.3, "cost": 0.2}
        self.accuracy_checker = accuracy_checker
        self.latency_threshold_ms = latency_threshold_ms
        self.cost_threshold = cost_threshold

    async def evaluate(
        self,
        task: str,
        submissions: List[Submission],
    ) -> Verdict:
        """
        Evaluate submissions based on metrics.

        Args:
            task: The original task description.
            submissions: List of agent submissions.

        Returns:
            Verdict with the winner and scores.
        """
        scores: Dict[str, float] = {}
        details: Dict[str, Dict[str, float]] = {}

        for sub in submissions:
            agent_scores = {}

            # Accuracy score
            if self.accuracy_checker:
                try:
                    accuracy = await self.accuracy_checker(task, sub.result)
                except Exception:
                    accuracy = 0.5  # Default if checker fails
            else:
                # Default: success = 1.0, failure = 0.0
                if hasattr(sub.result, "is_success"):
                    accuracy = 1.0 if sub.result.is_success else 0.0
                else:
                    accuracy = 0.5
            agent_scores["accuracy"] = accuracy

            # Latency score (lower is better)
            if sub.latency_ms is not None:
                if sub.latency_ms >= self.latency_threshold_ms:
                    latency_score = 0.0
                else:
                    latency_score = 1.0 - (sub.latency_ms / self.latency_threshold_ms)
            else:
                latency_score = 0.5  # Unknown latency
            agent_scores["latency"] = latency_score

            # Cost score (lower is better)
            if sub.cost is not None:
                if sub.cost >= self.cost_threshold:
                    cost_score = 0.0
                else:
                    cost_score = 1.0 - (sub.cost / self.cost_threshold)
            else:
                cost_score = 0.5  # Unknown cost
            agent_scores["cost"] = cost_score

            # Calculate weighted total
            total = sum(
                agent_scores.get(metric, 0) * weight
                for metric, weight in self.weights.items()
            )

            scores[sub.agent] = total
            details[sub.agent] = agent_scores

        # Determine winner
        winner = max(scores, key=scores.get)

        # Check for tie (within 5% margin)
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) >= 2:
            margin = sorted_scores[0] - sorted_scores[1]
            is_tie = margin < 0.05
        else:
            is_tie = False

        return Verdict(
            winner="tie" if is_tie else winner,
            reasoning=self._build_reasoning(details, winner),
            scores=scores,
            confidence=0.9 if not is_tie else 0.5,
            metadata={"metric_details": details},
        )

    def _build_reasoning(
        self,
        details: Dict[str, Dict[str, float]],
        winner: str,
    ) -> str:
        """Build human-readable reasoning from scores."""
        lines = [f"Winner: {winner}", "", "Score breakdown:"]

        for agent, metrics in details.items():
            lines.append(f"\n{agent}:")
            for metric, score in metrics.items():
                weight = self.weights.get(metric, 0)
                lines.append(f"  {metric}: {score:.2f} (weight: {weight})")

        return "\n".join(lines)
