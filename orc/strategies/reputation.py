"""
Reputation-based challenge strategy.
"""


class ReputationBased:
    """
    Strategy that challenges when reputation exceeds the Warlord's.

    Only challenges when the agent has a meaningful reputation
    advantage over the current Warlord.

    Example:
        strategy = ReputationBased(threshold=0.1)
        # Will challenge if challenger_rep > warlord_rep + 0.1
    """

    def __init__(self, threshold: float = 0.1):
        """
        Initialize the strategy.

        Args:
            threshold: Minimum reputation advantage required to challenge.
        """
        self.threshold = threshold

    def should_challenge(
        self,
        domain: str,
        warlord_name: str,
        warlord_reputation: float,
        challenger_reputation: float,
    ) -> bool:
        """Challenge if reputation exceeds threshold."""
        return challenger_reputation > warlord_reputation + self.threshold
