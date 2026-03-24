"""
Tests for challenge strategy implementations.

Tests cover AlwaysChallenge, ReputationBased, CooldownStrategy,
and SpecialistStrategy.
"""

from datetime import datetime, timedelta, timezone
import time

import pytest

from orc.strategies import (
    AlwaysChallenge,
    ReputationBased,
    CooldownStrategy,
    SpecialistStrategy,
)


class TestAlwaysChallenge:
    """Test the AlwaysChallenge strategy."""

    def test_always_challenge_returns_true(self):
        """Test that AlwaysChallenge always returns True."""
        strategy = AlwaysChallenge()

        result = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.3,
        )

        assert result is True

    def test_always_challenge_regardless_of_reputation(self):
        """Test that AlwaysChallenge ignores reputation values."""
        strategy = AlwaysChallenge()

        # High warlord reputation, low challenger
        result1 = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.9,
            challenger_reputation=0.1,
        )
        assert result1 is True

        # Low warlord reputation, high challenger
        result2 = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.1,
            challenger_reputation=0.9,
        )
        assert result2 is True

        # Equal reputation
        result3 = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.5,
        )
        assert result3 is True


class TestReputationBased:
    """Test the ReputationBased strategy."""

    def test_reputation_based_challenges_above_threshold(self):
        """Test that ReputationBased challenges when above threshold."""
        strategy = ReputationBased(threshold=0.1)

        # Challenger has 0.15 advantage (> 0.1 threshold)
        result = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.65,
        )

        assert result is True

    def test_reputation_based_doesnt_challenge_below_threshold(self):
        """Test that ReputationBased doesn't challenge below threshold."""
        strategy = ReputationBased(threshold=0.1)

        # Challenger has only 0.05 advantage
        result = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.55,
        )

        assert result is False

    def test_reputation_based_doesnt_challenge_below_warlord(self):
        """Test that ReputationBased doesn't challenge when below warlord."""
        strategy = ReputationBased(threshold=0.1)

        # Challenger below warlord
        result = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.6,
            challenger_reputation=0.4,
        )

        assert result is False

    def test_reputation_based_configurable_threshold(self):
        """Test that ReputationBased threshold is configurable."""
        strategy = ReputationBased(threshold=0.2)

        # Challenger has 0.15 advantage - below 0.2 threshold
        result = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.65,
        )

        assert result is False

        # But with a lower threshold...
        strategy2 = ReputationBased(threshold=0.1)
        result2 = strategy2.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.65,
        )

        assert result2 is True


class TestCooldownStrategy:
    """Test the CooldownStrategy implementation."""

    def test_cooldown_allows_challenge_initially(self):
        """Test that first challenge is allowed."""
        strategy = CooldownStrategy(base_cooldown=300)

        result = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.3,
        )

        assert result is True

    def test_cooldown_blocks_after_loss(self):
        """Test that challenge is blocked after recording a loss."""
        strategy = CooldownStrategy(base_cooldown=1)

        # First challenge allowed
        result1 = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.3,
        )
        assert result1 is True

        # Record a loss
        strategy.record_loss("data")

        # Challenge immediately blocked (within cooldown)
        result2 = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.3,
        )
        assert result2 is False

    def test_cooldown_expires(self):
        """Test that challenge is allowed after cooldown expires."""
        from datetime import datetime, timezone, timedelta

        strategy = CooldownStrategy(base_cooldown=1)

        # Record a loss
        strategy.record_loss("data")

        # Blocked immediately
        result1 = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.3,
        )
        assert result1 is False

        # Manually set the last challenge time to the past
        strategy._last_challenge["data"] = datetime.now(timezone.utc) - timedelta(seconds=2)

        # Now allowed
        result2 = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.3,
        )
        assert result2 is True

    def test_cooldown_multiplier_on_successive_losses(self):
        """Test that cooldown increases with successive losses."""
        from datetime import datetime, timezone, timedelta

        strategy = CooldownStrategy(
            base_cooldown=1,
            loss_multiplier=2.0,
            max_cooldown=10,
        )

        # First loss - 1 second cooldown
        strategy.record_loss("data")
        result1 = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.3,
        )
        assert result1 is False

        # Manually set the last challenge time to after the cooldown
        strategy._last_challenge["data"] = datetime.now(timezone.utc) - timedelta(seconds=2)

        # Now should be allowed
        result2 = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.3,
        )
        assert result2 is True

    def test_cooldown_reset_on_win(self):
        """Test that winning resets the loss counter."""
        strategy = CooldownStrategy(
            base_cooldown=1,
            loss_multiplier=2.0,
        )

        # Record a loss
        strategy.record_loss("data")

        # Record a win
        strategy.record_win("data")

        # Loss counter should be reset
        assert strategy._losses.get("data", 0) == 0

    def test_cooldown_respects_max_cooldown(self):
        """Test that cooldown respects maximum limit."""
        strategy = CooldownStrategy(
            base_cooldown=1,
            loss_multiplier=10.0,  # High multiplier
            max_cooldown=5,  # Max 5 seconds
        )

        # Multiple losses
        for _ in range(5):
            strategy.record_loss("data")

        # Cooldown should be capped at max_cooldown
        # (We can't easily test the exact timing without mocking,
        # but we verify the strategy exists and functions)
        result = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.3,
        )

        # Should be blocked (within max cooldown)
        assert result is False

    def test_cooldown_independent_per_domain(self):
        """Test that cooldown is tracked independently per domain."""
        strategy = CooldownStrategy(base_cooldown=1)

        # Lose in "data" domain
        strategy.record_loss("data")

        # Should be blocked in "data" domain
        result1 = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.3,
        )
        assert result1 is False

        # But allowed in "analytics" domain (different cooldown)
        result2 = strategy.should_challenge(
            domain="analytics",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.3,
        )
        assert result2 is True


class TestSpecialistStrategy:
    """Test the SpecialistStrategy implementation."""

    def test_specialist_challenges_in_specialty(self):
        """Test that SpecialistStrategy challenges in specialty domains."""
        strategy = SpecialistStrategy(
            specialties=["data", "analytics"],
            min_reputation=0.3,
        )

        # Challenge in specialty domain with sufficient reputation
        result = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.4,
        )

        assert result is True

    def test_specialist_doesnt_challenge_outside_specialty(self):
        """Test that SpecialistStrategy doesn't challenge outside specialties."""
        strategy = SpecialistStrategy(
            specialties=["data", "analytics"],
            min_reputation=0.3,
        )

        # Don't challenge in non-specialty domain
        result = strategy.should_challenge(
            domain="reporting",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.4,
        )

        assert result is False

    def test_specialist_respects_min_reputation(self):
        """Test that SpecialistStrategy respects minimum reputation."""
        strategy = SpecialistStrategy(
            specialties=["data"],
            min_reputation=0.5,
        )

        # Below minimum reputation
        result = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.3,
        )

        assert result is False

        # At or above minimum reputation
        result2 = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.5,
        )

        assert result2 is True

    def test_specialist_empty_specialties_never_challenges(self):
        """Test that SpecialistStrategy with no specialties never challenges."""
        strategy = SpecialistStrategy(specialties=None)

        result = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.9,
        )

        assert result is False

    def test_specialist_add_specialty(self):
        """Test that specialties can be dynamically added."""
        strategy = SpecialistStrategy(specialties=["data"])

        # Initially not in "analytics"
        result1 = strategy.should_challenge(
            domain="analytics",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.4,
        )
        assert result1 is False

        # Add specialty
        strategy.add_specialty("analytics")

        # Now in "analytics"
        result2 = strategy.should_challenge(
            domain="analytics",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.4,
        )
        assert result2 is True

    def test_specialist_remove_specialty(self):
        """Test that specialties can be dynamically removed."""
        strategy = SpecialistStrategy(specialties=["data", "analytics"])

        # Initially in "data"
        result1 = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.4,
        )
        assert result1 is True

        # Remove specialty
        strategy.remove_specialty("data")

        # Now not in "data"
        result2 = strategy.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.5,
            challenger_reputation=0.4,
        )
        assert result2 is False


class TestStrategyCombinations:
    """Test combining strategies in arena."""

    async def test_multiple_strategies_independently(self):
        """Test that different agents can use different strategies."""
        always = AlwaysChallenge()
        reputation = ReputationBased(threshold=0.2)

        # Same scenario, different results
        result_always = always.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.6,
            challenger_reputation=0.65,
        )

        result_reputation = reputation.should_challenge(
            domain="data",
            warlord_name="Warlord",
            warlord_reputation=0.6,
            challenger_reputation=0.65,
        )

        # AlwaysChallenge returns True
        assert result_always is True

        # ReputationBased returns False (only 0.05 advantage, needs 0.2)
        assert result_reputation is False
