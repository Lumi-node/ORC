"""
Tests for the Arena orchestration component.

Tests cover warlord election, challenge mechanics, reputation tracking,
and succession/defense mechanics.
"""

import random
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

# Ensure we're using async test function signature
pytestmark = pytest.mark.asyncio

from dynabots_core import TaskResult, Verdict
from orc.arena.arena import Arena, ArenaConfig, AgentState
from orc.arena.trial import TrialResult
from orc.strategies import AlwaysChallenge, ReputationBased

from conftest import MockAgent, MockJudge


class TestArenaInitialization:
    """Test arena initialization and warlord election."""

    async def test_arena_init_with_agents_and_judge(
        self, mock_agent, mock_judge
    ):
        """Test basic arena initialization."""
        agents = [mock_agent]
        arena = Arena(agents=agents, judge=mock_judge)

        assert arena.judge == mock_judge
        assert arena.config is not None
        assert len(arena._agents) == 1
        assert mock_agent.name in arena._agents

    async def test_arena_init_with_custom_config(self, mock_agent, mock_judge):
        """Test arena initialization with custom configuration."""
        config = ArenaConfig(
            challenge_probability=0.5,
            max_consecutive_defenses=5,
        )
        arena = Arena(agents=[mock_agent], judge=mock_judge, config=config)

        assert arena.config.challenge_probability == 0.5
        assert arena.config.max_consecutive_defenses == 5

    async def test_warlord_election_first_come_first_serve(
        self, mock_data_agent, mock_analytics_agent, mock_judge
    ):
        """Test that first agent claiming a domain becomes warlord."""
        # Data agent claims "data" domain first
        agents = [mock_data_agent, mock_analytics_agent]
        arena = Arena(agents=agents, judge=mock_judge)

        warlord = arena.get_warlord("data")
        assert warlord == "DataAgent"

        # Analytics agent doesn't claim data, so it's not warlord for data
        data_warlord = arena.get_warlord("data")
        assert data_warlord != "AnalyticsAgent"

    async def test_agent_state_initialization(self, mock_data_agent, mock_judge):
        """Test that agent state is properly initialized."""
        arena = Arena(agents=[mock_data_agent], judge=mock_judge)

        state = arena._agents["DataAgent"]
        assert isinstance(state, AgentState)
        assert state.agent == mock_data_agent
        assert "data" in state.reputation
        assert "database" in state.reputation


class TestTaskProcessing:
    """Test task processing through the arena."""

    async def test_process_task_no_challenge(
        self, mock_data_agent, mock_judge
    ):
        """Test task processing without challenge (challenge_probability=0)."""
        config = ArenaConfig(challenge_probability=0.0)
        arena = Arena(
            agents=[mock_data_agent],
            judge=mock_judge,
            config=config,
        )

        result = await arena.process("Fetch data", domain="data")

        assert result.was_challenged is False
        assert result.winner == "DataAgent"
        assert result.verdict is None
        assert mock_data_agent.call_count == 1

    async def test_process_task_infers_domain(
        self, mock_data_agent, mock_judge
    ):
        """Test that domain is inferred from task keywords."""
        config = ArenaConfig(challenge_probability=0.0)
        arena = Arena(
            agents=[mock_data_agent],
            judge=mock_judge,
            config=config,
        )

        # Task contains "data" keyword
        result = await arena.process("Fetch the data from the database")

        assert result.domain == "data"

    async def test_process_task_with_explicit_domain(
        self, mock_data_agent, mock_judge
    ):
        """Test task processing with explicit domain."""
        config = ArenaConfig(challenge_probability=0.0)
        arena = Arena(
            agents=[mock_data_agent],
            judge=mock_judge,
            config=config,
        )

        result = await arena.process(
            "Do something",
            domain="data",
        )

        assert result.domain == "data"
        assert result.winner == "DataAgent"


class TestChallenge:
    """Test challenge and trial mechanics."""

    async def test_challenge_triggered_with_high_probability(
        self, mock_data_agent, mock_analytics_agent, mock_judge
    ):
        """Test that challenge is triggered with high probability."""
        random.seed(42)  # Deterministic seed

        # Create agents where both claim "data" domain
        agent1 = MockAgent(
            name="Agent1",
            domains=["data"],
            process_task_result=TaskResult.success(
                task_id="test",
                data={"result": "agent1"},
            ),
        )
        agent2 = MockAgent(
            name="Agent2",
            domains=["data"],
            process_task_result=TaskResult.success(
                task_id="test",
                data={"result": "agent2"},
            ),
        )

        verdict = Verdict(
            winner="Agent2",
            reasoning="Agent2 is better",
            scores={"Agent1": 0.6, "Agent2": 0.8},
            confidence=0.9,
        )
        judge = MockJudge(verdict=verdict)

        config = ArenaConfig(challenge_probability=1.0)
        arena = Arena(agents=[agent1, agent2], judge=judge, config=config)

        result = await arena.process("Do data task", domain="data")

        assert result.was_challenged is True
        assert result.verdict is not None

    async def test_no_challenge_without_challengers(
        self, mock_data_agent, mock_judge
    ):
        """Test that no challenge occurs if no other agent claims domain."""
        random.seed(42)

        config = ArenaConfig(challenge_probability=1.0)
        arena = Arena(
            agents=[mock_data_agent],
            judge=mock_judge,
            config=config,
        )

        result = await arena.process("Do data task", domain="data")

        assert result.was_challenged is False

    async def test_challenge_respects_cooldown(
        self, mock_judge
    ):
        """Test that challenge respects cooldown after loss."""
        random.seed(42)

        agent1 = MockAgent(
            name="Agent1",
            domains=["data"],
            process_task_result=TaskResult.success(
                task_id="test",
                data={"result": "agent1"},
            ),
        )
        agent2 = MockAgent(
            name="Agent2",
            domains=["data"],
            process_task_result=TaskResult.success(
                task_id="test",
                data={"result": "agent2"},
            ),
        )

        verdict_1_wins = Verdict(
            winner="Agent1",
            reasoning="Agent1 wins",
            scores={"Agent1": 0.8, "Agent2": 0.6},
            confidence=0.9,
        )

        judge = MockJudge(verdict=verdict_1_wins)

        config = ArenaConfig(
            challenge_probability=1.0,
            challenge_cooldown_seconds=300,
        )
        arena = Arena(agents=[agent1, agent2], judge=judge, config=config)

        # First challenge
        result1 = await arena.process("Do task", domain="data")
        assert result1.was_challenged is True

        # Agent2 should be in cooldown now, so no second challenge
        result2 = await arena.process("Do task", domain="data")
        assert result2.was_challenged is False

    async def test_challenge_respects_minimum_reputation(
        self, mock_judge
    ):
        """Test that agents below min_reputation_to_challenge cannot challenge."""
        agent1 = MockAgent(
            name="HighRepAgent",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )
        agent2 = MockAgent(
            name="LowRepAgent",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )

        config = ArenaConfig(
            challenge_probability=1.0,
            min_reputation_to_challenge=0.7,
            default_reputation=0.2,
        )
        arena = Arena(agents=[agent1, agent2], judge=mock_judge, config=config)

        # Agent2 has low reputation (0.2), below threshold (0.7)
        result = await arena.process("Do task", domain="data")

        # No challenge because agent2 is below minimum
        assert result.was_challenged is False


class TestSuccession:
    """Test succession and defense mechanics."""

    async def test_succession_when_challenger_wins(
        self, mock_judge, capture_hooks
    ):
        """Test that warlord changes when challenger wins."""
        random.seed(42)

        agent1 = MockAgent(
            name="Agent1",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )
        agent2 = MockAgent(
            name="Agent2",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )

        # Agent2 wins the verdict
        verdict = Verdict(
            winner="Agent2",
            reasoning="Agent2 wins",
            scores={"Agent1": 0.6, "Agent2": 0.8},
            confidence=0.9,
        )
        judge = MockJudge(verdict=verdict)

        config = ArenaConfig(challenge_probability=1.0)
        arena = Arena(
            agents=[agent1, agent2],
            judge=judge,
            config=config,
            on_succession=capture_hooks["on_succession"],
        )

        assert arena.get_warlord("data") == "Agent1"

        await arena.process("Do task", domain="data")

        assert arena.get_warlord("data") == "Agent2"
        assert len(capture_hooks["successions"]) == 1
        assert capture_hooks["successions"][0]["new_warlord"] == "Agent2"

    async def test_defense_when_warlord_wins(
        self, mock_judge, capture_hooks
    ):
        """Test that warlord stays when defending against challenge."""
        random.seed(42)

        agent1 = MockAgent(
            name="Agent1",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )
        agent2 = MockAgent(
            name="Agent2",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )

        # Agent1 wins the verdict (warlord)
        verdict = Verdict(
            winner="Agent1",
            reasoning="Agent1 wins",
            scores={"Agent1": 0.8, "Agent2": 0.6},
            confidence=0.9,
        )
        judge = MockJudge(verdict=verdict)

        config = ArenaConfig(challenge_probability=1.0)
        arena = Arena(
            agents=[agent1, agent2],
            judge=judge,
            config=config,
            on_succession=capture_hooks["on_succession"],
        )

        assert arena.get_warlord("data") == "Agent1"

        await arena.process("Do task", domain="data")

        # Warlord remains the same
        assert arena.get_warlord("data") == "Agent1"
        assert len(capture_hooks["successions"]) == 0

    async def test_forced_rotation_after_max_defenses(
        self, mock_judge
    ):
        """Test forced rotation after too many consecutive defenses."""
        random.seed(42)

        agent1 = MockAgent(
            name="Agent1",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )
        agent2 = MockAgent(
            name="Agent2",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )

        verdict = Verdict(
            winner="Agent1",
            reasoning="Agent1 wins",
            scores={"Agent1": 0.8, "Agent2": 0.6},
            confidence=0.9,
        )
        judge = MockJudge(verdict=verdict)

        config = ArenaConfig(
            challenge_probability=1.0,
            max_consecutive_defenses=2,  # Force rotation after 2 defenses
        )
        arena = Arena(agents=[agent1, agent2], judge=judge, config=config)

        # Set Agent2's initial reputation higher so it can challenge
        arena._agents["Agent2"].reputation["data"] = 0.8

        assert arena.get_warlord("data") == "Agent1"

        # First challenge - Agent1 defends (defense count = 1)
        arena._agents["Agent2"].reputation["data"] = 0.8
        await arena.process("Do task", domain="data")
        assert arena.get_warlord("data") == "Agent1"
        assert arena._agents["Agent1"].consecutive_defenses["data"] == 1

        # Second challenge - Agent1 defends (defense count = 2, hits max)
        # This second defense will trigger forced rotation
        arena._agents["Agent2"].reputation["data"] = 0.8
        # Reset cooldown so Agent2 can challenge again
        arena._agents["Agent2"].last_challenge_time["data"] = (
            datetime.now(timezone.utc) - timedelta(seconds=400)
        )
        await arena.process("Do task", domain="data")

        # Warlord should have been forced to rotate to Agent2
        assert arena.get_warlord("data") == "Agent2"


class TestReputation:
    """Test reputation tracking and updates."""

    async def test_reputation_increases_on_win(
        self, mock_judge
    ):
        """Test that winner's reputation increases after trial."""
        random.seed(42)

        agent1 = MockAgent(
            name="Agent1",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )
        agent2 = MockAgent(
            name="Agent2",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )

        verdict = Verdict(
            winner="Agent2",
            reasoning="Agent2 wins",
            scores={"Agent1": 0.6, "Agent2": 0.8},
            confidence=0.9,
        )
        judge = MockJudge(verdict=verdict)

        config = ArenaConfig(challenge_probability=1.0)
        arena = Arena(agents=[agent1, agent2], judge=judge, config=config)

        initial_rep = arena.get_reputation("Agent2", "data")

        await arena.process("Do task", domain="data")

        final_rep = arena.get_reputation("Agent2", "data")
        assert final_rep > initial_rep

    async def test_reputation_decreases_on_loss(
        self, mock_judge
    ):
        """Test that loser's reputation decreases after trial."""
        random.seed(42)

        agent1 = MockAgent(
            name="Agent1",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )
        agent2 = MockAgent(
            name="Agent2",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )

        verdict = Verdict(
            winner="Agent2",
            reasoning="Agent2 wins",
            scores={"Agent1": 0.6, "Agent2": 0.8},
            confidence=0.9,
        )
        judge = MockJudge(verdict=verdict)

        config = ArenaConfig(challenge_probability=1.0)
        arena = Arena(agents=[agent1, agent2], judge=judge, config=config)

        initial_rep = arena.get_reputation("Agent1", "data")

        await arena.process("Do task", domain="data")

        final_rep = arena.get_reputation("Agent1", "data")
        assert final_rep < initial_rep


class TestDynamicAgentManagement:
    """Test registering and unregistering agents."""

    async def test_register_agent(self, mock_data_agent, mock_judge):
        """Test registering a new agent."""
        arena = Arena(agents=[mock_data_agent], judge=mock_judge)

        new_agent = MockAgent(name="NewAgent", domains=["data"])
        arena.register_agent(new_agent)

        assert "NewAgent" in arena._agents
        assert arena._agents["NewAgent"].agent == new_agent

    async def test_unregister_agent(self, mock_data_agent, mock_judge):
        """Test unregistering an agent."""
        arena = Arena(agents=[mock_data_agent], judge=mock_judge)

        arena.unregister_agent("DataAgent")

        assert "DataAgent" not in arena._agents
        # Warlord should be cleared if unregistered agent was warlord
        assert arena.get_warlord("data") is None

    async def test_unregister_non_warlord_agent(
        self, mock_data_agent, mock_judge
    ):
        """Test unregistering agent that is not warlord."""
        agent1 = MockAgent(name="Agent1", domains=["data"])
        agent2 = MockAgent(name="Agent2", domains=["data"])

        arena = Arena(agents=[agent1, agent2], judge=mock_judge)

        # Agent1 is warlord
        assert arena.get_warlord("data") == "Agent1"

        # Unregister Agent2 (not warlord)
        arena.unregister_agent("Agent2")

        assert "Agent2" not in arena._agents
        assert arena.get_warlord("data") == "Agent1"


class TestLeaderboard:
    """Test leaderboard generation."""

    async def test_leaderboard_ordering(
        self, mock_judge
    ):
        """Test that leaderboard is ordered by reputation."""
        random.seed(42)

        agent1 = MockAgent(name="Agent1", domains=["data"])
        agent2 = MockAgent(name="Agent2", domains=["data"])
        agent3 = MockAgent(name="Agent3", domains=["data"])

        arena = Arena(agents=[agent1, agent2, agent3], judge=mock_judge)

        # Set different reputation scores
        arena._agents["Agent1"].reputation["data"] = 0.9
        arena._agents["Agent2"].reputation["data"] = 0.5
        arena._agents["Agent3"].reputation["data"] = 0.7

        leaderboard = arena.get_leaderboard("data")

        assert leaderboard[0]["agent"] == "Agent1"
        assert leaderboard[1]["agent"] == "Agent3"
        assert leaderboard[2]["agent"] == "Agent2"

    async def test_leaderboard_includes_wins_losses(
        self, mock_judge
    ):
        """Test that leaderboard includes trial win/loss counts."""
        arena = Arena(
            agents=[
                MockAgent(name="Agent1", domains=["data"]),
                MockAgent(name="Agent2", domains=["data"]),
            ],
            judge=mock_judge,
        )

        # Set trial counts
        arena._agents["Agent1"].trial_wins["data"] = 5
        arena._agents["Agent1"].trial_losses["data"] = 2

        leaderboard = arena.get_leaderboard("data")

        assert leaderboard[0]["wins"] == 5
        assert leaderboard[0]["losses"] == 2

    async def test_leaderboard_limit(self, mock_judge):
        """Test that leaderboard respects limit parameter."""
        agents = [MockAgent(name=f"Agent{i}", domains=["data"]) for i in range(10)]

        arena = Arena(agents=agents, judge=mock_judge)

        leaderboard = arena.get_leaderboard("data", limit=5)

        assert len(leaderboard) == 5


class TestTrialHistory:
    """Test trial history tracking."""

    async def test_trial_history_tracking(
        self, mock_judge
    ):
        """Test that trials are tracked in history."""
        random.seed(42)

        agent1 = MockAgent(
            name="Agent1",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )
        agent2 = MockAgent(
            name="Agent2",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )

        verdict = Verdict(
            winner="Agent1",
            reasoning="Agent1 wins",
            scores={"Agent1": 0.8, "Agent2": 0.6},
            confidence=0.9,
        )
        judge = MockJudge(verdict=verdict)

        config = ArenaConfig(challenge_probability=1.0)
        arena = Arena(agents=[agent1, agent2], judge=judge, config=config)

        # Set up for challenge
        arena._agents["Agent2"].reputation["data"] = 0.8

        await arena.process("Do task", domain="data")

        history = arena.get_trial_history()

        assert len(history) == 1
        assert history[0].domain == "data"
        assert history[0].was_challenged is True

    async def test_trial_history_limit(
        self, mock_judge
    ):
        """Test that trial history respects limit parameter."""
        random.seed(42)

        agent1 = MockAgent(
            name="Agent1",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )
        agent2 = MockAgent(
            name="Agent2",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )

        verdict = Verdict(
            winner="Agent1",
            reasoning="Agent1 wins",
            scores={"Agent1": 0.8, "Agent2": 0.6},
            confidence=0.9,
        )
        judge = MockJudge(verdict=verdict)

        config = ArenaConfig(challenge_probability=1.0)
        arena = Arena(agents=[agent1, agent2], judge=judge, config=config)

        arena._agents["Agent2"].reputation["data"] = 0.8

        # Create multiple trials
        for i in range(5):
            # Reset reputation between trials to ensure challenge happens
            arena._agents["Agent2"].reputation["data"] = 0.8
            await arena.process("Do task", domain="data")

        history = arena.get_trial_history(limit=2)

        assert len(history) <= 2


class TestHookCallbacks:
    """Test hook callbacks."""

    async def test_on_challenge_hook(
        self, mock_judge, capture_hooks
    ):
        """Test that on_challenge hook is called."""
        random.seed(42)

        agent1 = MockAgent(
            name="Agent1",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )
        agent2 = MockAgent(
            name="Agent2",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )

        config = ArenaConfig(challenge_probability=1.0)
        arena = Arena(
            agents=[agent1, agent2],
            judge=mock_judge,
            config=config,
            on_challenge=capture_hooks["on_challenge"],
        )

        arena._agents["Agent2"].reputation["data"] = 0.8

        await arena.process("Do task", domain="data")

        assert len(capture_hooks["challenges"]) == 1
        assert capture_hooks["challenges"][0]["warlord"] == "Agent1"
        assert capture_hooks["challenges"][0]["challenger"] == "Agent2"

    async def test_on_succession_hook(
        self, mock_judge, capture_hooks
    ):
        """Test that on_succession hook is called."""
        random.seed(42)

        agent1 = MockAgent(
            name="Agent1",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )
        agent2 = MockAgent(
            name="Agent2",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )

        verdict = Verdict(
            winner="Agent2",
            reasoning="Agent2 wins",
            scores={"Agent1": 0.6, "Agent2": 0.8},
            confidence=0.9,
        )
        judge = MockJudge(verdict=verdict)

        config = ArenaConfig(challenge_probability=1.0)
        arena = Arena(
            agents=[agent1, agent2],
            judge=judge,
            config=config,
            on_succession=capture_hooks["on_succession"],
        )

        arena._agents["Agent2"].reputation["data"] = 0.8

        await arena.process("Do task", domain="data")

        assert len(capture_hooks["successions"]) == 1
        assert capture_hooks["successions"][0]["new_warlord"] == "Agent2"

    async def test_on_trial_complete_hook(
        self, mock_judge, capture_hooks
    ):
        """Test that on_trial_complete hook is called."""
        random.seed(42)

        agent1 = MockAgent(
            name="Agent1",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )
        agent2 = MockAgent(
            name="Agent2",
            domains=["data"],
            process_task_result=TaskResult.success(task_id="test", data="ok"),
        )

        config = ArenaConfig(challenge_probability=1.0)
        arena = Arena(
            agents=[agent1, agent2],
            judge=mock_judge,
            config=config,
            on_trial_complete=capture_hooks["on_trial_complete"],
        )

        arena._agents["Agent2"].reputation["data"] = 0.8

        await arena.process("Do task", domain="data")

        assert len(capture_hooks["trial_completes"]) == 1
        assert capture_hooks["trial_completes"][0]["winner"] is not None
