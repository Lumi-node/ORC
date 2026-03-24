"""
Warchief - The victorious Warrior granted command.

A Warchief represents the winning agent after a trial. It can delegate
sub-tasks to defeated warriors (subordinates).
"""

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from orc.themed.warrior import Warrior


class Warchief:
    """The victorious Warrior, granted command.

    After winning a trial, the Warchief can delegate sub-tasks
    to the defeated Warriors.

    Example:
        warchief = Warchief(
            warrior=victor,
            domain="data_analysis",
            reputation=0.95
        )
        warchief.command(defeated_warrior)
        print(f"Warband size: {len(warchief.warband)}")
    """

    def __init__(
        self,
        warrior: "Warrior",
        domain: str,
        reputation: float,
    ):
        """
        Initialize a Warchief.

        Args:
            warrior: The Warrior who won the trial.
            domain: The domain they now control.
            reputation: Their reputation score for this domain.
        """
        self.warrior = warrior
        self.domain = domain
        self.reputation = reputation
        self._subordinates: List["Warrior"] = []

    @property
    def name(self) -> str:
        """The Warchief's name (from the underlying warrior)."""
        return self.warrior.name

    def command(self, subordinate: "Warrior"):
        """Add a defeated warrior as a subordinate.

        Args:
            subordinate: The Warrior to add to the warband.
        """
        self._subordinates.append(subordinate)

    @property
    def warband(self) -> List["Warrior"]:
        """All warriors under the Warchief's command."""
        return self._subordinates.copy()

    def __repr__(self) -> str:
        return (
            f"Warchief({self.name}, domain={self.domain}, "
            f"reputation={self.reputation:.2f}, warband_size={len(self._subordinates)})"
        )
