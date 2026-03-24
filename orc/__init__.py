"""
Orc!! - Brutalist Hierarchy Orchestration

No appointed leaders. Leadership is earned and contested.

Example:
    from orc import Arena, LLMJudge
    from dynabots_core.providers import OllamaProvider

    llm = OllamaProvider(model="qwen2.5:72b")
    arena = Arena(
        agents=[DataAgent(), ReportAgent()],
        judge=LLMJudge(llm),
    )

    result = await arena.process("Analyze sales data")
"""

from orc.arena import Arena, ArenaConfig, TrialResult
from orc.judges import LLMJudge, MetricsJudge, ConsensusJudge
from orc.strategies import (
    ChallengeStrategy,
    AlwaysChallenge,
    ReputationBased,
    CooldownStrategy,
    SpecialistStrategy,
)
from orc.themed import Warrior, Elder, Warchief, TheArena

__version__ = "0.1.0"

__all__ = [
    # Core
    "Arena",
    "ArenaConfig",
    "TrialResult",
    # Judges
    "LLMJudge",
    "MetricsJudge",
    "ConsensusJudge",
    # Strategies
    "ChallengeStrategy",
    "AlwaysChallenge",
    "ReputationBased",
    "CooldownStrategy",
    "SpecialistStrategy",
    # Themed API
    "Warrior",
    "Elder",
    "Warchief",
    "TheArena",
]
