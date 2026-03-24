"""
Consensus Judge.

Uses multiple judges to vote on the winner.
"""

import asyncio
from typing import Dict, List

from dynabots_core import Verdict
from dynabots_core.protocols.judge import Judge, Submission


class ConsensusJudge:
    """
    Judge that aggregates votes from multiple sub-judges.

    Useful for reducing bias and increasing reliability.

    Example:
        judge = ConsensusJudge([
            LLMJudge(llm1),
            LLMJudge(llm2),
            MetricsJudge(),
        ])

        verdict = await judge.evaluate(task, submissions)
    """

    def __init__(
        self,
        judges: List[Judge],
        require_majority: bool = True,
        tiebreaker: str = "first",  # "first", "random", or judge name
    ):
        """
        Initialize the Consensus Judge.

        Args:
            judges: List of judges to vote.
            require_majority: If True, winner needs >50% votes.
            tiebreaker: How to break ties ("first" judge, "random", or specific judge name).
        """
        self.judges = judges
        self.require_majority = require_majority
        self.tiebreaker = tiebreaker

    async def evaluate(
        self,
        task: str,
        submissions: List[Submission],
    ) -> Verdict:
        """
        Evaluate by collecting votes from all judges.

        Args:
            task: The original task description.
            submissions: List of agent submissions.

        Returns:
            Verdict with the consensus winner.
        """
        # Collect verdicts from all judges in parallel
        verdicts = await asyncio.gather(*[
            judge.evaluate(task, submissions)
            for judge in self.judges
        ])

        # Tally votes
        votes: Dict[str, int] = {}
        vote_details: List[Dict] = []

        for i, verdict in enumerate(verdicts):
            winner = verdict.winner
            votes[winner] = votes.get(winner, 0) + 1
            vote_details.append({
                "judge_index": i,
                "winner": winner,
                "confidence": verdict.confidence,
                "reasoning": verdict.reasoning[:200],  # Truncate
            })

        # Determine winner
        total_votes = len(verdicts)
        max_votes = max(votes.values()) if votes else 0
        winners = [agent for agent, count in votes.items() if count == max_votes]

        if len(winners) == 1:
            winner = winners[0]
            confidence = max_votes / total_votes
        elif self.require_majority and max_votes <= total_votes / 2:
            # No majority - tie
            winner = "tie"
            confidence = 0.5
        else:
            # Tiebreaker
            if self.tiebreaker == "first":
                # Use first judge's decision among tied winners
                for verdict in verdicts:
                    if verdict.winner in winners:
                        winner = verdict.winner
                        break
                else:
                    winner = winners[0]
            elif self.tiebreaker == "random":
                import random
                winner = random.choice(winners)
            else:
                # Use specific judge
                winner = winners[0]

            confidence = max_votes / total_votes

        # Aggregate scores
        aggregated_scores: Dict[str, float] = {}
        for verdict in verdicts:
            for agent, score in verdict.scores.items():
                if agent not in aggregated_scores:
                    aggregated_scores[agent] = 0
                aggregated_scores[agent] += score / len(verdicts)

        # Build reasoning
        reasoning_lines = [
            f"Consensus decision: {winner}",
            f"Vote distribution: {votes}",
            "",
            "Individual verdicts:",
        ]
        for detail in vote_details:
            reasoning_lines.append(
                f"  Judge {detail['judge_index']}: {detail['winner']} "
                f"(confidence: {detail['confidence']:.2f})"
            )

        return Verdict(
            winner=winner,
            reasoning="\n".join(reasoning_lines),
            scores=aggregated_scores,
            confidence=confidence,
            metadata={
                "votes": votes,
                "vote_details": vote_details,
                "num_judges": len(self.judges),
            },
        )
