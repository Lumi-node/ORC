"""
Always challenge strategy.
"""


class AlwaysChallenge:
    """
    Strategy that always challenges when eligible.

    Use this for aggressive agents that want to maximize
    their chances of gaining leadership.
    """

    def should_challenge(
        self,
        domain: str,
        warlord_name: str,
        warlord_reputation: float,
        challenger_reputation: float,
    ) -> bool:
        """Always returns True."""
        return True
