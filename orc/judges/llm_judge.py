"""
LLM-based Judge.

Uses an LLM to evaluate agent submissions and determine winners.
"""

import json
from typing import List, Optional

from dynabots_core import LLMProvider, LLMMessage, Verdict
from dynabots_core.protocols.judge import Judge, Submission


class LLMJudge:
    """
    Judge that uses an LLM to evaluate submissions.

    The LLM compares agent outputs based on specified criteria
    and determines which agent performed better.

    Example:
        llm = OllamaProvider(model="qwen2.5:72b")
        judge = LLMJudge(
            llm,
            criteria=["accuracy", "completeness", "efficiency"],
        )

        verdict = await judge.evaluate(task, submissions)
    """

    def __init__(
        self,
        llm: LLMProvider,
        criteria: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
    ):
        """
        Initialize the LLM Judge.

        Args:
            llm: LLM provider for evaluation.
            criteria: Evaluation criteria (default: accuracy, completeness, clarity).
            system_prompt: Custom system prompt for evaluation.
        """
        self.llm = llm
        self.criteria = criteria or ["accuracy", "completeness", "clarity", "efficiency"]
        self.system_prompt = system_prompt or self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        criteria_str = ", ".join(self.criteria)
        return f"""You are an impartial judge evaluating agent submissions.

Your task is to compare two agent submissions for the same task and determine which one is better.

Evaluation criteria: {criteria_str}

You must respond with valid JSON in this format:
{{
    "winner": "A" or "B",
    "reasoning": "Detailed explanation of why this submission is better",
    "scores": {{
        "A": 0.0-1.0,
        "B": 0.0-1.0
    }},
    "confidence": 0.0-1.0
}}

Be fair and objective. If submissions are truly equivalent, you may declare a tie by setting winner to "tie".
"""

    async def evaluate(
        self,
        task: str,
        submissions: List[Submission],
    ) -> Verdict:
        """
        Evaluate submissions and determine a winner.

        Args:
            task: The original task description.
            submissions: List of agent submissions (typically 2).

        Returns:
            Verdict with the winner and reasoning.
        """
        if len(submissions) < 2:
            # Only one submission - automatic winner
            return Verdict(
                winner=submissions[0].agent,
                reasoning="Only one submission provided",
                scores={submissions[0].agent: 1.0},
                confidence=1.0,
            )

        # Build evaluation prompt
        sub_a = submissions[0]
        sub_b = submissions[1]

        user_prompt = f"""Task: {task}

Submission A ({sub_a.agent}):
{self._format_result(sub_a)}

Submission B ({sub_b.agent}):
{self._format_result(sub_b)}

Which submission better accomplishes the task? Evaluate based on: {", ".join(self.criteria)}"""

        # Call LLM
        response = await self.llm.complete(
            messages=[
                LLMMessage(role="system", content=self.system_prompt),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=0.1,
            json_mode=True,
        )

        # Parse response
        try:
            data = json.loads(response.content)
            winner_key = data.get("winner", "A")

            if winner_key.upper() == "A":
                winner = sub_a.agent
            elif winner_key.upper() == "B":
                winner = sub_b.agent
            elif winner_key.lower() == "tie":
                winner = "tie"
            else:
                winner = sub_a.agent  # Default to A

            # Map scores to agent names
            scores = {}
            raw_scores = data.get("scores", {})
            if "A" in raw_scores:
                scores[sub_a.agent] = raw_scores["A"]
            if "B" in raw_scores:
                scores[sub_b.agent] = raw_scores["B"]

            return Verdict(
                winner=winner,
                reasoning=data.get("reasoning", ""),
                scores=scores,
                confidence=data.get("confidence", 0.8),
            )

        except (json.JSONDecodeError, KeyError) as e:
            # Fallback: try to extract winner from text
            content = response.content.lower()
            if "submission b" in content or "agent b" in content:
                winner = sub_b.agent
            else:
                winner = sub_a.agent

            return Verdict(
                winner=winner,
                reasoning=response.content,
                confidence=0.5,
                metadata={"parse_error": str(e)},
            )

    def _format_result(self, submission: Submission) -> str:
        """Format a submission for the evaluation prompt."""
        result = submission.result

        # Handle TaskResult
        if hasattr(result, "to_dict"):
            result_data = result.to_dict()
        elif hasattr(result, "data"):
            result_data = result.data
        else:
            result_data = result

        parts = [f"Result: {result_data}"]

        if submission.latency_ms:
            parts.append(f"Latency: {submission.latency_ms}ms")

        if submission.cost:
            parts.append(f"Cost: ${submission.cost:.4f}")

        return "\n".join(parts)
