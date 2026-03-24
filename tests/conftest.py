"""
Shared fixtures for dynabots_orc tests.

Provides mock implementations of agents, judges, and LLM providers
that satisfy the protocol contracts.
"""

import sys
from pathlib import Path

# Add packages/core to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import json
from typing import Any, Dict, List, Optional

import pytest

from dynabots_core import Agent, Judge, TaskResult, Verdict, LLMProvider, LLMMessage, LLMResponse
from dynabots_core.protocols.judge import Submission
from orc.strategies import AlwaysChallenge


class MockAgent:
    """Mock agent for testing. Satisfies Agent protocol."""

    def __init__(
        self,
        name: str = "TestAgent",
        capabilities: Optional[List[str]] = None,
        domains: Optional[List[str]] = None,
        process_task_result: Optional[TaskResult] = None,
        challenge_strategy: Optional[Any] = None,
    ):
        self._name = name
        self._capabilities = capabilities or ["test_capability"]
        self._domains = domains or ["test"]
        self._process_task_result = (
            process_task_result
            or TaskResult.success(task_id="test", data={"status": "ok"})
        )
        self.challenge_strategy = challenge_strategy or AlwaysChallenge()
        self.call_count = 0
        self.last_context = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> List[str]:
        return self._capabilities

    @property
    def domains(self) -> List[str]:
        return self._domains

    async def process_task(self, task: str, context: Dict[str, Any]) -> TaskResult:
        self.call_count += 1
        self.last_context = context
        return self._process_task_result

    async def health_check(self) -> bool:
        return True


class MockJudge:
    """Mock judge for testing. Satisfies Judge protocol."""

    def __init__(self, verdict: Optional[Verdict] = None):
        self._verdict = verdict or Verdict(
            winner="agent1",
            reasoning="Test verdict",
            scores={"agent1": 0.8, "agent2": 0.6},
            confidence=0.9,
        )
        self.evaluation_count = 0
        self.last_task = None
        self.last_submissions = None

    async def evaluate(self, task: str, submissions: List[Submission]) -> Verdict:
        self.evaluation_count += 1
        self.last_task = task
        self.last_submissions = submissions
        return self._verdict

    def set_verdict(self, verdict: Verdict):
        """Configure the verdict this judge will return."""
        self._verdict = verdict


class MockLLMProvider:
    """Mock LLM provider for testing. Satisfies LLMProvider protocol."""

    def __init__(self, response_content: Optional[str] = None):
        self._response_content = response_content or json.dumps({
            "winner": "A",
            "reasoning": "Test reasoning",
            "scores": {"A": 0.8, "B": 0.6},
            "confidence": 0.9,
        })
        self.call_count = 0
        self.last_messages = None

    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        self.call_count += 1
        self.last_messages = messages
        return LLMResponse(content=self._response_content)

    def set_response(self, content: str):
        """Configure the response content this provider will return."""
        self._response_content = content


# Fixtures

@pytest.fixture
def mock_agent():
    """Create a basic mock agent."""
    return MockAgent()


@pytest.fixture
def mock_agent_fast():
    """Create a mock agent that returns quickly."""
    result = TaskResult.success(
        task_id="test",
        data={"status": "fast"},
        duration_ms=10,
    )
    return MockAgent(name="FastAgent", process_task_result=result)


@pytest.fixture
def mock_agent_slow():
    """Create a mock agent that takes longer."""
    result = TaskResult.success(
        task_id="test",
        data={"status": "slow"},
        duration_ms=1000,
    )
    return MockAgent(name="SlowAgent", process_task_result=result)


@pytest.fixture
def mock_agent_failure():
    """Create a mock agent that fails."""
    result = TaskResult.failure(task_id="test", error="Test failure")
    return MockAgent(name="FailureAgent", process_task_result=result)


@pytest.fixture
def mock_data_agent():
    """Create a mock agent specialized in data domain."""
    return MockAgent(
        name="DataAgent",
        capabilities=["fetch_data", "query_database"],
        domains=["data", "database"],
    )


@pytest.fixture
def mock_analytics_agent():
    """Create a mock agent specialized in analytics domain."""
    return MockAgent(
        name="AnalyticsAgent",
        capabilities=["analyze", "visualize"],
        domains=["analytics", "reporting"],
    )


@pytest.fixture
def mock_report_agent():
    """Create a mock agent specialized in reporting domain."""
    return MockAgent(
        name="ReportAgent",
        capabilities=["generate_report", "format_output"],
        domains=["reporting", "formatting"],
    )


@pytest.fixture
def mock_judge():
    """Create a basic mock judge."""
    return MockJudge()


@pytest.fixture
def mock_judge_tied():
    """Create a mock judge that returns a tie verdict."""
    verdict = Verdict(
        winner="tie",
        reasoning="Both agents performed equally",
        scores={"agent1": 0.7, "agent2": 0.7},
        confidence=0.5,
    )
    return MockJudge(verdict=verdict)


@pytest.fixture
def mock_llm_provider():
    """Create a basic mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def capture_hooks():
    """Fixture to capture arena hook calls."""
    hooks = {
        "challenges": [],
        "successions": [],
        "trial_completes": [],
    }

    def on_challenge(warlord: str, challenger: str, domain: str):
        hooks["challenges"].append({
            "warlord": warlord,
            "challenger": challenger,
            "domain": domain,
        })

    def on_succession(old_warlord: str, new_warlord: str, domain: str):
        hooks["successions"].append({
            "old_warlord": old_warlord,
            "new_warlord": new_warlord,
            "domain": domain,
        })

    def on_trial_complete(verdict: Verdict):
        hooks["trial_completes"].append({
            "winner": verdict.winner,
            "confidence": verdict.confidence,
        })

    hooks["on_challenge"] = on_challenge
    hooks["on_succession"] = on_succession
    hooks["on_trial_complete"] = on_trial_complete

    return hooks
