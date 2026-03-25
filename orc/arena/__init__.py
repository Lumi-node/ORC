"""
Arena - The heart of Orc!! orchestration.

The Arena manages agent competition, trials, and leadership succession.
"""

from orc.arena.arena import Arena, ArenaConfig
from orc.arena.trial import Trial, TrialResult

__all__ = ["Arena", "ArenaConfig", "TrialResult", "Trial"]
