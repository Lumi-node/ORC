"""
Judge implementations for Orc!!

Judges evaluate trial outcomes and determine winners.
"""

from orc.judges.llm_judge import LLMJudge
from orc.judges.metrics_judge import MetricsJudge
from orc.judges.consensus_judge import ConsensusJudge

__all__ = ["LLMJudge", "MetricsJudge", "ConsensusJudge"]
