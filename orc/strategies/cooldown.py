"""
Cooldown-based challenge strategy.
"""

from datetime import datetime, timezone
from typing import Dict


class CooldownStrategy:
    """
    Strategy with cooldown after losses.

    Reduces challenge frequency after losses to avoid
    wasting resources on unlikely wins.

    Example:
        strategy = CooldownStrategy(
            base_cooldown=300,  # 5 minutes
            loss_multiplier=2.0,  # Double cooldown after each loss
        )
    """

    def __init__(
        self,
        base_cooldown: int = 300,
        loss_multiplier: float = 2.0,
        max_cooldown: int = 3600,
    ):
        """
        Initialize the strategy.

        Args:
            base_cooldown: Base cooldown in seconds.
            loss_multiplier: Cooldown multiplier after each loss.
            max_cooldown: Maximum cooldown in seconds.
        """
        self.base_cooldown = base_cooldown
        self.loss_multiplier = loss_multiplier
        self.max_cooldown = max_cooldown

        # Track losses per domain
        self._losses: Dict[str, int] = {}
        self._last_challenge: Dict[str, datetime] = {}

    def should_challenge(
        self,
        domain: str,
        warlord_name: str,
        warlord_reputation: float,
        challenger_reputation: float,
    ) -> bool:
        """Challenge if cooldown has expired."""
        now = datetime.now(timezone.utc)

        # Check cooldown
        last = self._last_challenge.get(domain)
        if last:
            losses = self._losses.get(domain, 0)
            cooldown = min(
                self.base_cooldown * (self.loss_multiplier ** losses),
                self.max_cooldown,
            )
            elapsed = (now - last).total_seconds()
            if elapsed < cooldown:
                return False

        return True

    def record_loss(self, domain: str):
        """Record a loss for cooldown calculation."""
        self._losses[domain] = self._losses.get(domain, 0) + 1
        self._last_challenge[domain] = datetime.now(timezone.utc)

    def record_win(self, domain: str):
        """Record a win - reset loss counter."""
        self._losses[domain] = 0
        self._last_challenge[domain] = datetime.now(timezone.utc)
