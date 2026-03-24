"""
Tests for the Trial execution mechanism.

Tests cover parallel/sequential execution, timeout handling,
exception handling, and result construction.
"""

import asyncio

import pytest

from dynabots_core import TaskResult
from orc.arena.trial import Trial, TrialResult

from conftest import MockAgent, MockJudge


class TestTrialExecution:
    """Test basic trial execution."""

    async def test_parallel_execution(
        self, mock_agent_fast, mock_agent_slow, mock_judge
    ):
        """Test that agents execute in parallel when configured."""
        trial = Trial(
            task="Do something",
            domain="test",
            warlord=mock_agent_fast,
            challenger=mock_agent_slow,
            judge=mock_judge,
            parallel=True,
        )

        result = await trial.execute()

        assert result.warlord_result is not None
        assert result.challenger_result is not None
        assert result.was_challenged is True
        # Both agents should have been called
        assert mock_agent_fast.call_count == 1
        assert mock_agent_slow.call_count == 1

    async def test_sequential_execution(
        self, mock_agent_fast, mock_agent_slow, mock_judge
    ):
        """Test that agents execute sequentially when configured."""
        trial = Trial(
            task="Do something",
            domain="test",
            warlord=mock_agent_fast,
            challenger=mock_agent_slow,
            judge=mock_judge,
            parallel=False,
        )

        result = await trial.execute()

        assert result.warlord_result is not None
        assert result.challenger_result is not None
        assert result.was_challenged is True

    async def test_trial_result_construction(
        self, mock_agent_fast, mock_agent_slow, mock_judge
    ):
        """Test that TrialResult is properly constructed."""
        trial = Trial(
            task="Analyze data",
            domain="data",
            warlord=mock_agent_fast,
            challenger=mock_agent_slow,
            judge=mock_judge,
        )

        result = await trial.execute()

        assert result.task == "Analyze data"
        assert result.domain == "data"
        assert result.was_challenged is True
        assert result.verdict is not None
        assert result.trial_id is not None
        assert result.timestamp is not None
        assert result.duration_ms is not None

    async def test_trial_result_winner_result(
        self, mock_agent_fast, mock_agent_slow, mock_judge
    ):
        """Test that trial result contains winner's result."""
        trial = Trial(
            task="Do something",
            domain="test",
            warlord=mock_agent_fast,
            challenger=mock_agent_slow,
            judge=mock_judge,
        )

        result = await trial.execute()

        assert result.winner_result is not None
        # Winner is determined by judge's verdict
        if result.verdict.winner == mock_agent_fast.name:
            assert result.winner_result == result.warlord_result
        else:
            assert result.winner_result == result.challenger_result


class TestTimeoutHandling:
    """Test timeout handling during trial execution."""

    async def test_timeout_creates_failure_result(self, mock_judge):
        """Test that timeout results in failure TaskResult."""
        async def slow_agent_process(task, context):
            await asyncio.sleep(10)  # Very slow
            return TaskResult.success(task_id=context["task_id"], data="ok")

        mock_agent_fast = MockAgent(name="FastAgent")
        mock_agent_slow = MockAgent(name="SlowAgent")

        # Inject slow process_task
        mock_agent_slow.process_task = slow_agent_process

        trial = Trial(
            task="Do something",
            domain="test",
            warlord=mock_agent_fast,
            challenger=mock_agent_slow,
            judge=mock_judge,
            timeout=1,  # 1 second timeout
            parallel=True,
        )

        result = await trial.execute()

        # One agent should timeout
        assert (
            result.warlord_result.is_failure or
            result.challenger_result.is_failure
        )

    async def test_timeout_error_message(self, mock_judge):
        """Test that timeout includes informative error message."""
        async def slow_agent_process(task, context):
            await asyncio.sleep(10)
            return TaskResult.success(task_id=context["task_id"], data="ok")

        mock_agent_fast = MockAgent(name="FastAgent")
        mock_agent_slow = MockAgent(name="SlowAgent")
        mock_agent_slow.process_task = slow_agent_process

        trial = Trial(
            task="Do something",
            domain="test",
            warlord=mock_agent_slow,
            challenger=mock_agent_fast,
            judge=mock_judge,
            timeout=1,
            parallel=True,
        )

        result = await trial.execute()

        # Find the timeout error
        timeout_occurred = (
            (result.warlord_result.error_message and "Timeout" in result.warlord_result.error_message) or
            (result.challenger_result.error_message and "Timeout" in result.challenger_result.error_message)
        )
        assert timeout_occurred


class TestExceptionHandling:
    """Test exception handling during trial execution."""

    async def test_agent_exception_creates_failure_result(
        self, mock_judge
    ):
        """Test that agent exceptions result in failure TaskResult."""
        async def failing_agent_process(task, context):
            raise ValueError("Agent failed to process")

        mock_agent_good = MockAgent(name="GoodAgent")
        mock_agent_bad = MockAgent(name="BadAgent")
        mock_agent_bad.process_task = failing_agent_process

        trial = Trial(
            task="Do something",
            domain="test",
            warlord=mock_agent_good,
            challenger=mock_agent_bad,
            judge=mock_judge,
        )

        result = await trial.execute()

        # Bad agent's result should be failure
        assert result.challenger_result.is_failure
        assert "Agent failed to process" in result.challenger_result.error_message

    async def test_both_agents_exception(self, mock_judge):
        """Test handling when both agents raise exceptions."""
        async def failing_process(task, context):
            raise ValueError("Agent failed")

        mock_agent1 = MockAgent(name="Agent1")
        mock_agent2 = MockAgent(name="Agent2")
        mock_agent1.process_task = failing_process
        mock_agent2.process_task = failing_process

        trial = Trial(
            task="Do something",
            domain="test",
            warlord=mock_agent1,
            challenger=mock_agent2,
            judge=mock_judge,
        )

        result = await trial.execute()

        # Both should fail
        assert result.warlord_result.is_failure
        assert result.challenger_result.is_failure


class TestTrialContextPassing:
    """Test that context is properly passed to agents."""

    async def test_warlord_receives_context(
        self, mock_agent_fast, mock_agent_slow, mock_judge
    ):
        """Test that warlord receives augmented context."""
        trial = Trial(
            task="Do something",
            domain="test",
            warlord=mock_agent_fast,
            challenger=mock_agent_slow,
            judge=mock_judge,
            context={"custom_key": "custom_value"},
        )

        result = await trial.execute()

        warlord_context = mock_agent_fast.last_context
        assert "trial_id" in warlord_context
        assert warlord_context["role"] == "warlord"
        assert "custom_key" in warlord_context
        assert warlord_context["custom_key"] == "custom_value"

    async def test_challenger_receives_context(
        self, mock_agent_fast, mock_agent_slow, mock_judge
    ):
        """Test that challenger receives augmented context."""
        trial = Trial(
            task="Do something",
            domain="test",
            warlord=mock_agent_fast,
            challenger=mock_agent_slow,
            judge=mock_judge,
            context={"custom_key": "custom_value"},
        )

        result = await trial.execute()

        challenger_context = mock_agent_slow.last_context
        assert "trial_id" in challenger_context
        assert challenger_context["role"] == "challenger"
        assert "custom_key" in challenger_context
        assert challenger_context["custom_key"] == "custom_value"


class TestTrialResultSerialization:
    """Test TrialResult serialization."""

    async def test_trial_result_to_dict(
        self, mock_agent_fast, mock_agent_slow, mock_judge
    ):
        """Test that TrialResult can be serialized to dict."""
        trial = Trial(
            task="Analyze data",
            domain="data",
            warlord=mock_agent_fast,
            challenger=mock_agent_slow,
            judge=mock_judge,
        )

        result = await trial.execute()
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "trial_id" in result_dict
        assert "task" in result_dict
        assert "domain" in result_dict
        assert "winner" in result_dict
        assert "was_challenged" in result_dict
        assert "timestamp" in result_dict

    async def test_trial_result_data_property(
        self, mock_agent_fast, mock_agent_slow, mock_judge
    ):
        """Test that TrialResult.data returns winner's data."""
        trial = Trial(
            task="Do something",
            domain="test",
            warlord=mock_agent_fast,
            challenger=mock_agent_slow,
            judge=mock_judge,
        )

        result = await trial.execute()
        data = result.data

        # Data should come from winner's result
        assert data is not None


class TestTrialDurationTracking:
    """Test that trial duration is properly tracked."""

    async def test_trial_duration_is_set(
        self, mock_agent_fast, mock_agent_slow, mock_judge
    ):
        """Test that trial duration_ms is populated."""
        trial = Trial(
            task="Do something",
            domain="test",
            warlord=mock_agent_fast,
            challenger=mock_agent_slow,
            judge=mock_judge,
        )

        result = await trial.execute()

        assert result.duration_ms is not None
        assert result.duration_ms >= 0

    async def test_agent_duration_is_set(
        self, mock_agent_fast, mock_agent_slow, mock_judge
    ):
        """Test that agent result durations are tracked."""
        trial = Trial(
            task="Do something",
            domain="test",
            warlord=mock_agent_fast,
            challenger=mock_agent_slow,
            judge=mock_judge,
        )

        result = await trial.execute()

        assert result.warlord_result.duration_ms is not None
        assert result.challenger_result.duration_ms is not None


class TestTrialWithDifferentJudges:
    """Test trial execution with different judge implementations."""

    async def test_trial_with_tied_verdict(self, mock_agent_fast, mock_agent_slow):
        """Test trial handling when judge returns tie."""
        from conftest import MockJudge
        from dynabots_core import Verdict

        tie_verdict = Verdict(
            winner="tie",
            reasoning="Both agents equal",
            scores={"FastAgent": 0.7, "SlowAgent": 0.7},
            confidence=0.5,
        )
        tied_judge = MockJudge(verdict=tie_verdict)

        trial = Trial(
            task="Do something",
            domain="test",
            warlord=mock_agent_fast,
            challenger=mock_agent_slow,
            judge=tied_judge,
        )

        result = await trial.execute()

        assert result.verdict.winner == "tie"
        assert result.verdict.is_tie
