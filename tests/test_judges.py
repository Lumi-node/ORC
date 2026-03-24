"""
Tests for judge implementations.

Tests cover MetricsJudge, ConsensusJudge, and LLMJudge.
"""

import json

import pytest

from dynabots_core import TaskResult, Verdict
from dynabots_core.protocols.judge import Submission
from orc.judges.metrics_judge import MetricsJudge
from orc.judges.consensus_judge import ConsensusJudge
from orc.judges.llm_judge import LLMJudge

from conftest import MockAgent, MockJudge, MockLLMProvider


class TestMetricsJudge:
    """Test the MetricsJudge implementation."""

    async def test_metrics_judge_selects_higher_score(self):
        """Test that MetricsJudge selects agent with higher combined score."""
        judge = MetricsJudge(
            weights={"accuracy": 0.5, "latency": 0.3, "cost": 0.2}
        )

        result1 = TaskResult.success(task_id="task1", data="output1")
        result2 = TaskResult.success(task_id="task2", data="output2")

        submissions = [
            Submission(agent="Agent1", result=result1, latency_ms=100, cost=0.05),
            Submission(agent="Agent2", result=result2, latency_ms=200, cost=0.10),
        ]

        verdict = await judge.evaluate("Do something", submissions)

        # Agent1 should win (lower latency and cost)
        assert verdict.winner == "Agent1"
        assert verdict.scores["Agent1"] > verdict.scores["Agent2"]

    async def test_metrics_judge_accuracy_scoring(self):
        """Test that MetricsJudge scores accuracy correctly."""
        async def check_accuracy(task, result):
            # Simple accuracy checker: return 1.0 if success, 0.0 if failure
            return 1.0 if result.is_success else 0.0

        judge = MetricsJudge(
            weights={"accuracy": 1.0, "latency": 0.0, "cost": 0.0},
            accuracy_checker=check_accuracy,
        )

        success_result = TaskResult.success(task_id="task1", data="ok")
        failure_result = TaskResult.failure(task_id="task2", error="failed")

        submissions = [
            Submission(agent="GoodAgent", result=success_result),
            Submission(agent="BadAgent", result=failure_result),
        ]

        verdict = await judge.evaluate("Do something", submissions)

        # GoodAgent should win
        assert verdict.winner == "GoodAgent"
        assert verdict.scores["GoodAgent"] > verdict.scores["BadAgent"]

    async def test_metrics_judge_latency_scoring(self):
        """Test that MetricsJudge scores latency correctly."""
        judge = MetricsJudge(
            weights={"accuracy": 0.0, "latency": 1.0, "cost": 0.0},
            latency_threshold_ms=1000,
        )

        result1 = TaskResult.success(task_id="task1", data="ok")
        result2 = TaskResult.success(task_id="task2", data="ok")

        submissions = [
            Submission(agent="FastAgent", result=result1, latency_ms=100),
            Submission(agent="SlowAgent", result=result2, latency_ms=800),
        ]

        verdict = await judge.evaluate("Do something", submissions)

        # FastAgent should win
        assert verdict.winner == "FastAgent"

    async def test_metrics_judge_cost_scoring(self):
        """Test that MetricsJudge scores cost correctly."""
        judge = MetricsJudge(
            weights={"accuracy": 0.0, "latency": 0.0, "cost": 1.0},
            cost_threshold=0.10,
        )

        result1 = TaskResult.success(task_id="task1", data="ok")
        result2 = TaskResult.success(task_id="task2", data="ok")

        submissions = [
            Submission(agent="CheapAgent", result=result1, cost=0.02),
            Submission(agent="ExpensiveAgent", result=result2, cost=0.08),
        ]

        verdict = await judge.evaluate("Do something", submissions)

        # CheapAgent should win
        assert verdict.winner == "CheapAgent"

    async def test_metrics_judge_configurable_weights(self):
        """Test that MetricsJudge respects configurable weights."""
        judge_accuracy_focused = MetricsJudge(
            weights={"accuracy": 0.9, "latency": 0.05, "cost": 0.05}
        )

        judge_latency_focused = MetricsJudge(
            weights={"accuracy": 0.1, "latency": 0.8, "cost": 0.1}
        )

        result1 = TaskResult.success(task_id="task1", data="ok")
        result2 = TaskResult.success(task_id="task2", data="ok")

        submissions = [
            Submission(agent="Agent1", result=result1, latency_ms=100, cost=0.05),
            Submission(agent="Agent2", result=result2, latency_ms=500, cost=0.05),
        ]

        # Both judges should exist and be configurable
        assert judge_accuracy_focused.weights["accuracy"] == 0.9
        assert judge_latency_focused.weights["latency"] == 0.8

    async def test_metrics_judge_tie_detection(self):
        """Test that MetricsJudge detects ties."""
        judge = MetricsJudge(
            weights={"accuracy": 0.5, "latency": 0.3, "cost": 0.2}
        )

        result1 = TaskResult.success(task_id="task1", data="ok")
        result2 = TaskResult.success(task_id="task2", data="ok")

        # Nearly identical submissions
        submissions = [
            Submission(agent="Agent1", result=result1, latency_ms=100, cost=0.05),
            Submission(agent="Agent2", result=result2, latency_ms=101, cost=0.05),
        ]

        verdict = await judge.evaluate("Do something", submissions)

        # Should detect as tie (within 5% margin)
        assert verdict.is_tie

    async def test_metrics_judge_unknown_metrics(self):
        """Test that MetricsJudge handles unknown metrics gracefully."""
        judge = MetricsJudge()

        result1 = TaskResult.success(task_id="task1", data="ok")
        result2 = TaskResult.success(task_id="task2", data="ok")

        # No latency or cost provided - agents are identical
        submissions = [
            Submission(agent="Agent1", result=result1),
            Submission(agent="Agent2", result=result2),
        ]

        verdict = await judge.evaluate("Do something", submissions)

        # Should still produce a verdict (may be tie or first agent)
        assert verdict.winner in ["Agent1", "Agent2", "tie"]


class TestConsensusJudge:
    """Test the ConsensusJudge implementation."""

    async def test_consensus_judge_majority_voting(self):
        """Test that ConsensusJudge uses majority voting."""
        judge1 = MockJudge(verdict=Verdict(
            winner="Agent1",
            reasoning="Judge1 prefers Agent1",
            scores={"Agent1": 0.8, "Agent2": 0.6},
            confidence=0.9,
        ))
        judge2 = MockJudge(verdict=Verdict(
            winner="Agent1",
            reasoning="Judge2 prefers Agent1",
            scores={"Agent1": 0.7, "Agent2": 0.5},
            confidence=0.8,
        ))
        judge3 = MockJudge(verdict=Verdict(
            winner="Agent2",
            reasoning="Judge3 prefers Agent2",
            scores={"Agent1": 0.6, "Agent2": 0.7},
            confidence=0.8,
        ))

        consensus_judge = ConsensusJudge([judge1, judge2, judge3])

        result1 = TaskResult.success(task_id="task1", data="ok")
        result2 = TaskResult.success(task_id="task2", data="ok")

        submissions = [
            Submission(agent="Agent1", result=result1),
            Submission(agent="Agent2", result=result2),
        ]

        verdict = await consensus_judge.evaluate("Do something", submissions)

        # Agent1 wins with 2 out of 3 votes
        assert verdict.winner == "Agent1"

    async def test_consensus_judge_tie_handling(self):
        """Test that ConsensusJudge handles tie votes."""
        judge1 = MockJudge(verdict=Verdict(
            winner="Agent1",
            reasoning="Judge1 prefers Agent1",
            scores={"Agent1": 0.8, "Agent2": 0.6},
            confidence=0.9,
        ))
        judge2 = MockJudge(verdict=Verdict(
            winner="Agent2",
            reasoning="Judge2 prefers Agent2",
            scores={"Agent1": 0.6, "Agent2": 0.8},
            confidence=0.9,
        ))

        consensus_judge = ConsensusJudge([judge1, judge2], require_majority=True)

        result1 = TaskResult.success(task_id="task1", data="ok")
        result2 = TaskResult.success(task_id="task2", data="ok")

        submissions = [
            Submission(agent="Agent1", result=result1),
            Submission(agent="Agent2", result=result2),
        ]

        verdict = await consensus_judge.evaluate("Do something", submissions)

        # Should be a tie (no majority)
        assert verdict.is_tie

    async def test_consensus_judge_score_aggregation(self):
        """Test that ConsensusJudge aggregates scores correctly."""
        judge1 = MockJudge(verdict=Verdict(
            winner="Agent1",
            reasoning="Judge1",
            scores={"Agent1": 0.8, "Agent2": 0.6},
            confidence=0.9,
        ))
        judge2 = MockJudge(verdict=Verdict(
            winner="Agent1",
            reasoning="Judge2",
            scores={"Agent1": 0.7, "Agent2": 0.5},
            confidence=0.8,
        ))

        consensus_judge = ConsensusJudge([judge1, judge2])

        result1 = TaskResult.success(task_id="task1", data="ok")
        result2 = TaskResult.success(task_id="task2", data="ok")

        submissions = [
            Submission(agent="Agent1", result=result1),
            Submission(agent="Agent2", result=result2),
        ]

        verdict = await consensus_judge.evaluate("Do something", submissions)

        # Scores should be averaged
        expected_agent1_score = (0.8 + 0.7) / 2
        expected_agent2_score = (0.6 + 0.5) / 2
        assert abs(verdict.scores["Agent1"] - expected_agent1_score) < 0.01
        assert abs(verdict.scores["Agent2"] - expected_agent2_score) < 0.01

    async def test_consensus_judge_tiebreaker_first(self):
        """Test tiebreaker='first' uses first judge's decision."""
        judge1 = MockJudge(verdict=Verdict(
            winner="Agent1",
            reasoning="Judge1 prefers Agent1",
            scores={"Agent1": 0.8, "Agent2": 0.6},
            confidence=0.9,
        ))
        judge2 = MockJudge(verdict=Verdict(
            winner="Agent2",
            reasoning="Judge2 prefers Agent2",
            scores={"Agent1": 0.6, "Agent2": 0.8},
            confidence=0.9,
        ))

        consensus_judge = ConsensusJudge(
            [judge1, judge2],
            require_majority=False,
            tiebreaker="first",
        )

        result1 = TaskResult.success(task_id="task1", data="ok")
        result2 = TaskResult.success(task_id="task2", data="ok")

        submissions = [
            Submission(agent="Agent1", result=result1),
            Submission(agent="Agent2", result=result2),
        ]

        verdict = await consensus_judge.evaluate("Do something", submissions)

        # Tiebreaker should choose first judge's winner
        assert verdict.winner == "Agent1"


class TestLLMJudge:
    """Test the LLMJudge implementation."""

    async def test_llm_judge_parses_winner(self):
        """Test that LLMJudge correctly parses winner from LLM response."""
        llm = MockLLMProvider(response_content=json.dumps({
            "winner": "A",
            "reasoning": "Agent1 is better",
            "scores": {"A": 0.8, "B": 0.6},
            "confidence": 0.9,
        }))
        judge = LLMJudge(llm)

        result1 = TaskResult.success(task_id="task1", data="ok")
        result2 = TaskResult.success(task_id="task2", data="ok")

        submissions = [
            Submission(agent="Agent1", result=result1),
            Submission(agent="Agent2", result=result2),
        ]

        verdict = await judge.evaluate("Do something", submissions)

        assert verdict.winner == "Agent1"

    async def test_llm_judge_maps_scores(self):
        """Test that LLMJudge correctly maps scores to agent names."""
        llm = MockLLMProvider(response_content=json.dumps({
            "winner": "B",
            "reasoning": "Agent2 is better",
            "scores": {"A": 0.6, "B": 0.8},
            "confidence": 0.9,
        }))
        judge = LLMJudge(llm)

        result1 = TaskResult.success(task_id="task1", data="ok")
        result2 = TaskResult.success(task_id="task2", data="ok")

        submissions = [
            Submission(agent="Agent1", result=result1),
            Submission(agent="Agent2", result=result2),
        ]

        verdict = await judge.evaluate("Do something", submissions)

        assert verdict.scores["Agent1"] == 0.6
        assert verdict.scores["Agent2"] == 0.8

    async def test_llm_judge_handles_malformed_json(self):
        """Test that LLMJudge handles malformed JSON gracefully."""
        llm = MockLLMProvider(response_content="This is not valid JSON")
        judge = LLMJudge(llm)

        result1 = TaskResult.success(task_id="task1", data="ok")
        result2 = TaskResult.success(task_id="task2", data="ok")

        submissions = [
            Submission(agent="Agent1", result=result1),
            Submission(agent="Agent2", result=result2),
        ]

        verdict = await judge.evaluate("Do something", submissions)

        # Should still return a verdict (fallback)
        assert verdict.winner is not None
        assert verdict.reasoning is not None

    async def test_llm_judge_single_submission(self):
        """Test that LLMJudge handles single submission."""
        llm = MockLLMProvider()
        judge = LLMJudge(llm)

        result1 = TaskResult.success(task_id="task1", data="ok")

        submissions = [
            Submission(agent="Agent1", result=result1),
        ]

        verdict = await judge.evaluate("Do something", submissions)

        # Single submission should be automatic winner
        assert verdict.winner == "Agent1"
        assert verdict.confidence == 1.0

    async def test_llm_judge_custom_criteria(self):
        """Test that LLMJudge accepts custom evaluation criteria."""
        criteria = ["accuracy", "speed", "cost", "user_satisfaction"]
        llm = MockLLMProvider()
        judge = LLMJudge(llm, criteria=criteria)

        assert judge.criteria == criteria

    async def test_llm_judge_custom_system_prompt(self):
        """Test that LLMJudge accepts custom system prompt."""
        custom_prompt = "You are a very strict judge."
        llm = MockLLMProvider()
        judge = LLMJudge(llm, system_prompt=custom_prompt)

        assert judge.system_prompt == custom_prompt

    async def test_llm_judge_tie_detection(self):
        """Test that LLMJudge can return tie verdict from LLM."""
        llm = MockLLMProvider(response_content=json.dumps({
            "winner": "tie",
            "reasoning": "Both agents are equal",
            "scores": {"A": 0.7, "B": 0.7},
            "confidence": 0.5,
        }))
        judge = LLMJudge(llm)

        result1 = TaskResult.success(task_id="task1", data="ok")
        result2 = TaskResult.success(task_id="task2", data="ok")

        submissions = [
            Submission(agent="Agent1", result=result1),
            Submission(agent="Agent2", result=result2),
        ]

        verdict = await judge.evaluate("Do something", submissions)

        assert verdict.is_tie
        assert verdict.winner == "tie"

    async def test_llm_judge_llm_called_with_context(self):
        """Test that LLMJudge calls LLM with proper context."""
        llm = MockLLMProvider(response_content=json.dumps({
            "winner": "A",
            "reasoning": "Agent1 is better",
            "scores": {"A": 0.8, "B": 0.6},
            "confidence": 0.9,
        }))
        judge = LLMJudge(llm, criteria=["accuracy", "speed"])

        result1 = TaskResult.success(task_id="task1", data="output1")
        result2 = TaskResult.success(task_id="task2", data="output2")

        submissions = [
            Submission(agent="Agent1", result=result1),
            Submission(agent="Agent2", result=result2),
        ]

        await judge.evaluate("Do something specific", submissions)

        # Check that LLM was called
        assert llm.call_count == 1
        # Check that messages were passed
        assert llm.last_messages is not None
        assert len(llm.last_messages) == 2  # system + user
