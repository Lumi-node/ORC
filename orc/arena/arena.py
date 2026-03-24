"""
Arena - Where agents compete for leadership.

The Arena is the core orchestration component of Orc!!. It:
- Tracks Warlords (current leaders) for each domain
- Determines when challenges should occur
- Executes trials between competing agents
- Updates leadership based on trial outcomes
- Maintains reputation scores
"""

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set
import uuid

from dynabots_core import Agent, TaskResult, Judge, Verdict
from dynabots_core.protocols.storage import ReputationStore

from orc.arena.trial import Trial, TrialResult
from orc.strategies import ChallengeStrategy, AlwaysChallenge


@dataclass
class ArenaConfig:
    """Configuration for the Arena."""

    # Challenge settings
    challenge_probability: float = 0.3  # Base probability of challenge on domain overlap
    min_reputation_to_challenge: float = 0.2  # Minimum reputation to challenge
    challenge_cooldown_seconds: int = 300  # Cooldown after losing a challenge

    # Leadership settings
    min_trials_for_leadership: int = 1  # Minimum trial wins to become Warlord
    leadership_decay_rate: float = 0.01  # Reputation decay per hour without defense
    max_consecutive_defenses: int = 10  # Force rotation after N defenses

    # Trial settings
    trial_timeout_seconds: int = 300  # Timeout for trial execution
    parallel_trial_execution: bool = True  # Execute trial attempts in parallel

    # Defaults
    default_reputation: float = 0.5  # Starting reputation for new agents


@dataclass
class AgentState:
    """Internal state for an agent in the arena."""

    agent: Agent
    reputation: Dict[str, float] = field(default_factory=dict)  # domain -> score
    trial_wins: Dict[str, int] = field(default_factory=dict)  # domain -> count
    trial_losses: Dict[str, int] = field(default_factory=dict)
    last_challenge_time: Dict[str, datetime] = field(default_factory=dict)
    last_defense_time: Dict[str, datetime] = field(default_factory=dict)
    consecutive_defenses: Dict[str, int] = field(default_factory=dict)
    is_warlord: Set[str] = field(default_factory=set)  # domains where this agent is warlord


class Arena:
    """
    The Arena where agents compete for leadership.

    Example:
        arena = Arena(
            agents=[DataAgent(), ReportAgent(), AnalyticsAgent()],
            judge=LLMJudge(llm),
            config=ArenaConfig(challenge_probability=0.3),
        )

        # Process a task - may trigger a trial
        result = await arena.process("Analyze Q4 sales data")

        # Check who leads which domain
        warlord = arena.get_warlord("data")
        print(f"Data domain Warlord: {warlord}")
    """

    def __init__(
        self,
        agents: List[Agent],
        judge: Judge,
        config: Optional[ArenaConfig] = None,
        reputation_store: Optional[ReputationStore] = None,
        # Hooks
        on_challenge: Optional[Callable[[str, str, str], None]] = None,
        on_succession: Optional[Callable[[str, str, str], None]] = None,
        on_trial_complete: Optional[Callable[[Verdict], None]] = None,
    ):
        """
        Initialize the Arena.

        Args:
            agents: List of agents that can compete.
            judge: Judge to evaluate trial outcomes.
            config: Arena configuration.
            reputation_store: Optional persistent storage for reputation.
            on_challenge: Hook called when a challenge is issued.
            on_succession: Hook called when leadership changes.
            on_trial_complete: Hook called when a trial completes.
        """
        self.judge = judge
        self.config = config or ArenaConfig()
        self.reputation_store = reputation_store

        # Hooks
        self._on_challenge = on_challenge
        self._on_succession = on_succession
        self._on_trial_complete = on_trial_complete

        # Initialize agent states
        self._agents: Dict[str, AgentState] = {}
        for agent in agents:
            self._agents[agent.name] = AgentState(
                agent=agent,
                reputation={d: self.config.default_reputation for d in self._get_domains(agent)},
            )

        # Domain -> current warlord name
        self._warlords: Dict[str, str] = {}

        # Initialize warlords (first agent claiming each domain)
        self._initialize_warlords()

        # Trial history
        self._trial_history: List[TrialResult] = []

    def _get_domains(self, agent: Agent) -> List[str]:
        """Get domains for an agent."""
        if hasattr(agent, "domains"):
            return agent.domains
        # Fallback: use capabilities as domains
        return agent.capabilities

    def _initialize_warlords(self):
        """Set initial warlords based on first-come-first-serve."""
        for name, state in self._agents.items():
            for domain in self._get_domains(state.agent):
                if domain not in self._warlords:
                    self._warlords[domain] = name
                    state.is_warlord.add(domain)

    async def process(
        self,
        task: str,
        domain: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> TrialResult:
        """
        Process a task through the arena.

        This may trigger a trial if:
        1. Multiple agents claim the domain
        2. A challenger decides to challenge
        3. Challenge conditions are met

        Args:
            task: The task to execute.
            domain: Optional domain hint. If not provided, will be inferred.
            context: Optional execution context.

        Returns:
            TrialResult with the outcome.
        """
        context = context or {}
        context["task_id"] = context.get("task_id", str(uuid.uuid4()))

        # Determine domain
        if not domain:
            domain = await self._infer_domain(task)

        # Get current warlord
        warlord_name = self._warlords.get(domain)
        if not warlord_name:
            # No warlord - elect one
            warlord_name = await self._elect_warlord(domain)

        warlord_state = self._agents[warlord_name]

        # Check for challengers
        challenger = await self._find_challenger(task, domain, warlord_name)

        if challenger:
            # TRIAL BY COMBAT!
            if self._on_challenge:
                self._on_challenge(warlord_name, challenger, domain)

            trial = Trial(
                task=task,
                domain=domain,
                warlord=warlord_state.agent,
                challenger=self._agents[challenger].agent,
                judge=self.judge,
                context=context,
                timeout=self.config.trial_timeout_seconds,
                parallel=self.config.parallel_trial_execution,
            )

            result = await trial.execute()
            self._trial_history.append(result)

            # Update leadership
            await self._process_trial_result(result, domain, warlord_name, challenger)

            if self._on_trial_complete:
                self._on_trial_complete(result.verdict)

            return result

        else:
            # No challenge - warlord executes
            task_result = await warlord_state.agent.process_task(task, context)

            return TrialResult(
                task=task,
                domain=domain,
                winner=warlord_name,
                winner_result=task_result,
                was_challenged=False,
                verdict=None,
            )

    async def _infer_domain(self, task: str) -> str:
        """Infer the domain from the task description."""
        # Simple heuristic: find domain with most keyword matches
        task_lower = task.lower()
        scores: Dict[str, int] = {}

        for domain in self._warlords.keys():
            score = task_lower.count(domain.lower())
            # Also check agent capabilities
            for name, state in self._agents.items():
                for cap in state.agent.capabilities:
                    if cap.lower() in task_lower:
                        for d in self._get_domains(state.agent):
                            scores[d] = scores.get(d, 0) + 1

            scores[domain] = scores.get(domain, 0) + score

        if scores:
            return max(scores, key=scores.get)

        # Fallback: return first domain
        return list(self._warlords.keys())[0] if self._warlords else "general"

    async def _elect_warlord(self, domain: str) -> str:
        """Elect a warlord for a domain with no current leader."""
        candidates = [
            name for name, state in self._agents.items()
            if domain in self._get_domains(state.agent)
        ]

        if not candidates:
            # No one claims this domain - assign to highest reputation agent
            candidates = list(self._agents.keys())

        # Pick highest reputation
        best = max(candidates, key=lambda n: self._agents[n].reputation.get(domain, 0))
        self._warlords[domain] = best
        self._agents[best].is_warlord.add(domain)
        return best

    async def _find_challenger(
        self,
        task: str,
        domain: str,
        warlord_name: str,
    ) -> Optional[str]:
        """Find an agent willing to challenge the warlord."""
        candidates = []

        for name, state in self._agents.items():
            if name == warlord_name:
                continue

            # Check if agent claims this domain
            if domain not in self._get_domains(state.agent):
                continue

            # Check cooldown
            last_challenge = state.last_challenge_time.get(domain)
            if last_challenge:
                elapsed = (datetime.now(timezone.utc) - last_challenge).total_seconds()
                if elapsed < self.config.challenge_cooldown_seconds:
                    continue

            # Check minimum reputation
            rep = state.reputation.get(domain, self.config.default_reputation)
            if rep < self.config.min_reputation_to_challenge:
                continue

            # Check challenge strategy
            strategy = getattr(state.agent, "challenge_strategy", AlwaysChallenge())
            if await self._should_challenge(strategy, state, domain, warlord_name):
                candidates.append(name)

        if not candidates:
            return None

        # Random selection weighted by reputation
        weights = [
            self._agents[n].reputation.get(domain, self.config.default_reputation)
            for n in candidates
        ]
        total = sum(weights)
        if total == 0:
            return random.choice(candidates)

        r = random.random() * total
        cumulative = 0
        for name, weight in zip(candidates, weights):
            cumulative += weight
            if r <= cumulative:
                return name

        return candidates[-1]

    async def _should_challenge(
        self,
        strategy: ChallengeStrategy,
        state: AgentState,
        domain: str,
        warlord_name: str,
    ) -> bool:
        """Check if an agent should challenge based on strategy."""
        # Base probability check
        if random.random() > self.config.challenge_probability:
            return False

        # Strategy check
        warlord_rep = self._agents[warlord_name].reputation.get(
            domain, self.config.default_reputation
        )
        challenger_rep = state.reputation.get(domain, self.config.default_reputation)

        return strategy.should_challenge(
            domain=domain,
            warlord_name=warlord_name,
            warlord_reputation=warlord_rep,
            challenger_reputation=challenger_rep,
        )

    async def _process_trial_result(
        self,
        result: TrialResult,
        domain: str,
        warlord_name: str,
        challenger_name: str,
    ):
        """Process trial result and update leadership."""
        warlord_state = self._agents[warlord_name]
        challenger_state = self._agents[challenger_name]

        # Update challenge time
        challenger_state.last_challenge_time[domain] = datetime.now(timezone.utc)

        if result.winner == challenger_name:
            # SUCCESSION!
            # Update trial counts
            challenger_state.trial_wins[domain] = challenger_state.trial_wins.get(domain, 0) + 1
            warlord_state.trial_losses[domain] = warlord_state.trial_losses.get(domain, 0) + 1

            # Update reputation
            challenger_state.reputation[domain] = min(
                1.0, challenger_state.reputation.get(domain, 0.5) + 0.1
            )
            warlord_state.reputation[domain] = max(
                0.0, warlord_state.reputation.get(domain, 0.5) - 0.1
            )

            # Transfer leadership
            warlord_state.is_warlord.discard(domain)
            warlord_state.consecutive_defenses[domain] = 0
            challenger_state.is_warlord.add(domain)
            challenger_state.consecutive_defenses[domain] = 0
            self._warlords[domain] = challenger_name

            if self._on_succession:
                self._on_succession(warlord_name, challenger_name, domain)

        else:
            # Warlord defends!
            warlord_state.trial_wins[domain] = warlord_state.trial_wins.get(domain, 0) + 1
            challenger_state.trial_losses[domain] = challenger_state.trial_losses.get(domain, 0) + 1

            # Update reputation
            warlord_state.reputation[domain] = min(
                1.0, warlord_state.reputation.get(domain, 0.5) + 0.05
            )
            challenger_state.reputation[domain] = max(
                0.0, challenger_state.reputation.get(domain, 0.5) - 0.05
            )

            # Track consecutive defenses
            warlord_state.consecutive_defenses[domain] = (
                warlord_state.consecutive_defenses.get(domain, 0) + 1
            )
            warlord_state.last_defense_time[domain] = datetime.now(timezone.utc)

            # Check for forced rotation
            if warlord_state.consecutive_defenses[domain] >= self.config.max_consecutive_defenses:
                # Force rotation to second-highest reputation
                await self._force_rotation(domain, warlord_name)

        # Persist reputation if store available
        if self.reputation_store:
            await self.reputation_store.update_reputation(
                challenger_name,
                domain,
                challenger_state.reputation[domain] - self.config.default_reputation,
            )
            await self.reputation_store.update_reputation(
                warlord_name,
                domain,
                warlord_state.reputation[domain] - self.config.default_reputation,
            )

    async def _force_rotation(self, domain: str, current_warlord: str):
        """Force leadership rotation after too many consecutive defenses."""
        # Find second-highest reputation
        candidates = [
            (name, state.reputation.get(domain, 0))
            for name, state in self._agents.items()
            if name != current_warlord and domain in self._get_domains(state.agent)
        ]

        if candidates:
            new_warlord = max(candidates, key=lambda x: x[1])[0]
            self._agents[current_warlord].is_warlord.discard(domain)
            self._agents[current_warlord].consecutive_defenses[domain] = 0
            self._agents[new_warlord].is_warlord.add(domain)
            self._warlords[domain] = new_warlord

            if self._on_succession:
                self._on_succession(current_warlord, new_warlord, domain)

    # Public API

    def get_warlord(self, domain: str) -> Optional[str]:
        """Get the current Warlord for a domain."""
        return self._warlords.get(domain)

    def get_reputation(self, agent_name: str, domain: str) -> float:
        """Get an agent's reputation for a domain."""
        if agent_name not in self._agents:
            return 0.0
        return self._agents[agent_name].reputation.get(domain, self.config.default_reputation)

    def get_leaderboard(self, domain: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the reputation leaderboard for a domain."""
        scores = [
            {
                "agent": name,
                "reputation": state.reputation.get(domain, self.config.default_reputation),
                "wins": state.trial_wins.get(domain, 0),
                "losses": state.trial_losses.get(domain, 0),
                "is_warlord": domain in state.is_warlord,
            }
            for name, state in self._agents.items()
            if domain in self._get_domains(state.agent)
        ]

        return sorted(scores, key=lambda x: x["reputation"], reverse=True)[:limit]

    def get_trial_history(self, limit: int = 50) -> List[TrialResult]:
        """Get recent trial history."""
        return self._trial_history[-limit:]

    def register_agent(self, agent: Agent):
        """Register a new agent in the arena."""
        self._agents[agent.name] = AgentState(
            agent=agent,
            reputation={d: self.config.default_reputation for d in self._get_domains(agent)},
        )

    def unregister_agent(self, agent_name: str):
        """Remove an agent from the arena."""
        if agent_name in self._agents:
            state = self._agents[agent_name]
            # Remove from warlord positions
            for domain in list(state.is_warlord):
                if self._warlords.get(domain) == agent_name:
                    del self._warlords[domain]
            del self._agents[agent_name]
