"""
Challenge strategies for Orc!!

Strategies determine when an agent should challenge the current Warlord.
"""

from orc.strategies.always import AlwaysChallenge
from orc.strategies.base import ChallengeStrategy
from orc.strategies.cooldown import CooldownStrategy
from orc.strategies.reputation import ReputationBased
from orc.strategies.specialist import SpecialistStrategy

__all__ = [
    "ChallengeStrategy",
    "AlwaysChallenge",
    "ReputationBased",
    "CooldownStrategy",
    "SpecialistStrategy",
]
