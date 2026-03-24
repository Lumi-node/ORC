"""
Specialist challenge strategy.
"""

from typing import List, Optional


class SpecialistStrategy:
    """
    Strategy that only challenges in specialty domains.

    For agents that want to focus on specific domains
    rather than competing broadly.

    Example:
        strategy = SpecialistStrategy(specialties=["data", "analytics"])
        # Will only challenge in "data" and "analytics" domains
    """

    def __init__(
        self,
        specialties: Optional[List[str]] = None,
        min_reputation: float = 0.3,
    ):
        """
        Initialize the strategy.

        Args:
            specialties: List of specialty domains. If None, never challenges.
            min_reputation: Minimum reputation required to challenge.
        """
        self.specialties = set(specialties or [])
        self.min_reputation = min_reputation

    def should_challenge(
        self,
        domain: str,
        warlord_name: str,
        warlord_reputation: float,
        challenger_reputation: float,
    ) -> bool:
        """Challenge only in specialty domains with sufficient reputation."""
        if domain not in self.specialties:
            return False
        if challenger_reputation < self.min_reputation:
            return False
        return True

    def add_specialty(self, domain: str):
        """Add a specialty domain."""
        self.specialties.add(domain)

    def remove_specialty(self, domain: str):
        """Remove a specialty domain."""
        self.specialties.discard(domain)
