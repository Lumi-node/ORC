"""
Base challenge strategy protocol.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ChallengeStrategy(Protocol):
    """
    Protocol for challenge strategies.

    Strategies determine when an agent should challenge
    the current Warlord for leadership of a domain.
    """

    def should_challenge(
        self,
        domain: str,
        warlord_name: str,
        warlord_reputation: float,
        challenger_reputation: float,
    ) -> bool:
        """
        Determine whether to challenge.

        Args:
            domain: The domain in question.
            warlord_name: Name of the current Warlord.
            warlord_reputation: Warlord's reputation in this domain.
            challenger_reputation: Challenger's reputation in this domain.

        Returns:
            True if the agent should challenge, False otherwise.
        """
        ...
