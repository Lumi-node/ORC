"""
TheArena - The stage where Warriors compete.

TheArena wraps the standard Arena with ORC theming and themed output.
It accepts Warriors and Elders directly for a more thematic API.
"""

from typing import Any, Dict, List, Optional

from orc.arena import Arena, ArenaConfig, TrialResult
from orc.judges import MetricsJudge
from orc.themed.warrior import Warrior
from orc.themed.elder import Elder
from orc.themed.warchief import Warchief


class TheArena(Arena):
    """The Arena where Warriors compete for supremacy.

    Same functionality as Arena but accepts Warriors and Elders directly,
    and produces themed console output.

    Example:
        arena = TheArena(
            warriors=[grog, thrall, sylvanas],
            elder=elder,
            challenge_probability=0.3,
        )

        result = await arena.battle("Optimize the database queries")
    """

    def __init__(
        self,
        warriors: List[Warrior],
        elder: Elder,
        challenge_probability: float = 0.3,
        **config_kwargs: Any,
    ):
        """
        Initialize TheArena.

        Args:
            warriors: List of Warrior agents competing.
            elder: Elder judge to evaluate trials.
            challenge_probability: Base probability of challenge (0-1).
            **config_kwargs: Additional Arena config options.
        """
        # Build ArenaConfig
        config = ArenaConfig(
            challenge_probability=challenge_probability,
            **config_kwargs,
        )

        # Initialize parent Arena with warriors as agents and elder's judge
        on_challenge = self._themed_on_challenge
        on_succession = self._themed_on_succession
        on_trial_complete = self._themed_on_trial_complete

        super().__init__(
            agents=warriors,
            judge=elder.judge,
            config=config,
            on_challenge=on_challenge,
            on_succession=on_succession,
            on_trial_complete=on_trial_complete,
        )

        self.warriors = {w.name: w for w in warriors}
        self.elder = elder

    async def battle(
        self,
        task: str,
        domain: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> TrialResult:
        """Execute a battle (alias for process).

        Args:
            task: The challenge to execute.
            domain: Optional domain hint.
            context: Execution context.

        Returns:
            TrialResult with the outcome.
        """
        return await self.process(task, domain, context)

    def get_warchief(self, domain: str) -> Optional[Warchief]:
        """Get the Warchief (current leader) for a domain.

        Args:
            domain: The domain to query.

        Returns:
            Warchief instance or None if no leader.
        """
        warlord_name = self.get_warlord(domain)
        if not warlord_name:
            return None

        warrior = self.warriors.get(warlord_name)
        if not warrior:
            return None

        reputation = self.get_reputation(warlord_name, domain)
        return Warchief(warrior=warrior, domain=domain, reputation=reputation)

    def _themed_on_challenge(self, warlord: str, challenger: str, domain: str):
        """Themed output when a challenge is issued."""
        print(f"\n⚔️ CHALLENGE: {challenger} challenges {warlord} for the '{domain}' domain!")

    def _themed_on_succession(self, old_warlord: str, new_warlord: str, domain: str):
        """Themed output when leadership changes."""
        print(f"\n👑 SUCCESSION: {new_warlord} defeats {old_warlord}! A new Warchief rises!")

    def _themed_on_trial_complete(self, verdict: Any):
        """Themed output when a trial completes."""
        print(f"\n⚖️ The Elder has spoken. Verdict: {verdict.reasoning[:100]}...")
