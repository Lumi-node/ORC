# Challenge Strategies

Control **when** warriors challenge for domain leadership.

By default, challenges are probabilistic (controlled by `challenge_probability` in ArenaConfig). But you can customize strategy per warrior.

---

## Overview

A **Challenge Strategy** determines if a warrior challenges the current Warlord.

```python
from orc import Warrior, AlwaysChallenge, ReputationBased, CooldownStrategy, SpecialistStrategy

warrior = Warrior(
    name="Grok",
    llm_client="gpt-4o",
    system_prompt="...",
    domains=["backend", "python"],
)

# Assign a strategy
warrior.challenge_strategy = CooldownStrategy(base_cooldown=3600)
```

When the Warlord attempts a task in a contested domain, the strategy decides: challenge or defer?

---

## Strategy Types

### 1. AlwaysChallenge

**Always challenge when you can.**

Use when you want aggressive competition. The warrior challenges the Warlord every time.

```python
from orc import AlwaysChallenge

warrior.challenge_strategy = AlwaysChallenge()
```

**Characteristics:**

- Always challenges on domain overlap
- High energy, high competition
- Good for testing (forces lots of trials)
- Risky if reputation is low (many losses)

**Use case:**

- Aggressive agents
- Forcing trials for evaluation
- Berserker warrior archetype

---

### 2. ReputationBased

**Challenge only if confident.**

Challenge only when your reputation meets or exceeds a threshold relative to the Warlord.

```python
from orc import ReputationBased

# Challenge if your rep is at least 10% lower than warlord's
warrior.challenge_strategy = ReputationBased(threshold=0.1)
```

**Parameters:**

- `threshold` (default 0.0) — Min reputation to challenge
  - `0.0` — Challenge if rep >= Warlord's rep
  - `0.1` — Challenge if rep >= Warlord's rep - 0.1
  - `0.5` — Challenge if rep >= Warlord's rep - 0.5

**Characteristics:**

- Conservative, calculates odds
- Challenges when likely to win
- Reduces wasted losses
- Gradual climb to dominance

**Use case:**

- Strategic agents
- Agents learning over time
- Calculating warrior archetype

---

### 3. CooldownStrategy

**Back off after losses. Exponential backoff.**

After losing a challenge, wait before trying again. Cooldown increases exponentially.

```python
from orc import CooldownStrategy

# Wait 60 seconds after loss, then 120, 240, etc.
warrior.challenge_strategy = CooldownStrategy(base_cooldown=60)
```

**Parameters:**

- `base_cooldown` (default 60 seconds) — Initial wait time
- Doubles after each loss (exponential backoff)

**How it works:**

1. Challenge Warlord, lose
2. Cooldown = 60 seconds (wait)
3. Challenge again, lose
4. Cooldown = 120 seconds (wait)
5. Challenge again, lose
6. Cooldown = 240 seconds (wait)
...

**Characteristics:**

- Cautious after defeats
- Learns from losses
- Eventually tries again (patience wears off)
- Good for realistic agent behavior

**Use case:**

- Patient agents
- Learning from mistakes
- Shaman/wise warrior archetype

---

### 4. SpecialistStrategy

**Only challenge in specific domains.**

Challenge for leadership only in domains where you specialize.

```python
from orc import SpecialistStrategy

# Only challenge in "backend" domain, defer in "devops"
warrior.challenge_strategy = SpecialistStrategy(
    specialties=["backend", "python"]
)
```

**Parameters:**

- `specialties` — Domains where the warrior competes

**How it works:**

- Task in "backend"? Challenge the Warlord.
- Task in "devops"? Defer to current Warlord.
- Task in "infrastructure"? Defer.

**Characteristics:**

- Focused competition
- Wins in specialty domains
- Preserves energy
- Reduces losses in weak domains

**Use case:**

- Specialist agents
- Domain-specific expertise
- Focused warrior archetype

---

## Custom Strategy

Implement your own strategy by extending the protocol.

```python
from orc.strategies import ChallengeStrategy

class MyCustomStrategy(ChallengeStrategy):
    """Custom challenge strategy."""

    async def should_challenge(
        self,
        warrior_name: str,
        warlord_name: str,
        domain: str,
        warrior_reputation: float,
        warlord_reputation: float,
    ) -> bool:
        """
        Decide whether to challenge.

        Args:
            warrior_name: Your name
            warlord_name: Current Warlord's name
            domain: Domain being contested
            warrior_reputation: Your reputation in this domain
            warlord_reputation: Warlord's reputation

        Returns:
            True to challenge, False to defer
        """
        # Your logic here
        pass
```

### Example: Threshold-Based Strategy

```python
class ThresholdStrategy(ChallengeStrategy):
    """Challenge if reputation is within threshold of Warlord."""

    def __init__(self, threshold=0.15):
        self.threshold = threshold

    async def should_challenge(
        self,
        warrior_name: str,
        warlord_name: str,
        domain: str,
        warrior_reputation: float,
        warlord_reputation: float,
    ) -> bool:
        """Challenge if reputation gap is within threshold."""
        gap = warlord_reputation - warrior_reputation
        return gap <= self.threshold
```

### Example: Time-Based Strategy

```python
from datetime import datetime, timedelta

class TimeBasedStrategy(ChallengeStrategy):
    """Challenge every N hours."""

    def __init__(self, hours_between_challenges=4):
        self.hours = hours_between_challenges
        self.last_challenge = {}

    async def should_challenge(
        self,
        warrior_name: str,
        warlord_name: str,
        domain: str,
        warrior_reputation: float,
        warlord_reputation: float,
    ) -> bool:
        """Challenge if enough time has passed."""
        key = f"{domain}:{warlord_name}"

        if key not in self.last_challenge:
            self.last_challenge[key] = datetime.now()
            return True

        elapsed = datetime.now() - self.last_challenge[key]
        if elapsed >= timedelta(hours=self.hours):
            self.last_challenge[key] = datetime.now()
            return True

        return False
```

### Example: Weighted Probability

```python
import random

class WeightedProbabilityStrategy(ChallengeStrategy):
    """Challenge with probability based on reputation."""

    def __init__(self, base_probability=0.3):
        self.base_prob = base_probability

    async def should_challenge(
        self,
        warrior_name: str,
        warlord_name: str,
        domain: str,
        warrior_reputation: float,
        warlord_reputation: float,
    ) -> bool:
        """Adjust probability based on reputation gap."""
        # More confident if reputation is high
        confidence = min(warrior_reputation, 1.0)
        adjusted_prob = self.base_prob * confidence
        return random.random() < adjusted_prob
```

---

## Strategy Comparison

| Strategy | Challenge Frequency | When to Use | Archetype |
|----------|-------------------|------------|-----------|
| `AlwaysChallenge` | Very high | Testing, aggressive agents | Berserker |
| `ReputationBased` | Moderate | Strategic agents | Tactician |
| `CooldownStrategy` | Low (after losses) | Patient learning | Shaman |
| `SpecialistStrategy` | Medium (domain-specific) | Specialist agents | Ranger |

---

## Combining with Arena Config

Strategy works **with** arena config, not instead of it:

```python
from orc import TheArena, ArenaConfig

arena = TheArena(
    warriors=[grok, thrall, sylvanas],
    elder=elder,
    challenge_probability=0.5,  # Arena base probability
)

# AND assign per-warrior strategies
grok.challenge_strategy = AlwaysChallenge()
thrall.challenge_strategy = ReputationBased(threshold=0.15)
sylvanas.challenge_strategy = SpecialistStrategy(specialties=["magic"])
```

**How they interact:**

1. Arena decides whether to allow a challenge (based on `challenge_probability`)
2. If allowed, warrior's strategy decides whether to initiate
3. Both must be true for a challenge to happen

---

## Example: Multi-Strategy Battle

```python
import asyncio
from orc import Warrior, Elder, TheArena
from orc import (
    AlwaysChallenge,
    ReputationBased,
    CooldownStrategy,
    SpecialistStrategy,
)
from orc.judges import MetricsJudge

async def main():
    # Create warriors with different strategies
    berserker = Warrior(
        name="Berserker",
        llm_client="mock",
        system_prompt="Always attack!",
        domains=["combat", "melee"],
    )
    berserker.challenge_strategy = AlwaysChallenge()

    tactician = Warrior(
        name="Tactician",
        llm_client="mock",
        system_prompt="Think before acting.",
        domains=["combat", "strategy"],
    )
    tactician.challenge_strategy = ReputationBased(threshold=0.1)

    patient = Warrior(
        name="Patient",
        llm_client="mock",
        system_prompt="Wisdom comes with time.",
        domains=["strategy", "magic"],
    )
    patient.challenge_strategy = CooldownStrategy(base_cooldown=120)

    specialist = Warrior(
        name="Specialist",
        llm_client="mock",
        system_prompt="Master of my domain.",
        domains=["magic", "healing"],
    )
    specialist.challenge_strategy = SpecialistStrategy(specialties=["magic"])

    elder = Elder(judge=MetricsJudge())

    arena = TheArena(
        warriors=[berserker, tactician, patient, specialist],
        elder=elder,
        challenge_probability=0.8,
    )

    tasks = [
        "Melee combat challenge",
        "Strategic decision required",
        "Magic spell casting",
        "Healing ritual needed",
    ]

    for task in tasks:
        result = await arena.battle(task)
        print(f"{task} -> Winner: {result.winner}")

    # Show who dominates each domain
    for domain in ["combat", "strategy", "magic"]:
        warlord = arena.get_warlord(domain)
        print(f"Warlord of {domain}: {warlord}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Tips

1. **Test with high `challenge_probability`** — See all strategies in action
2. **Pair strategies with system prompts** — Berserker warrior + AlwaysChallenge makes sense
3. **Custom strategies can track history** — Remember past challenges, adjust behavior
4. **ReputationBased is conservative** — Good for stable leadership
5. **CooldownStrategy learns from losses** — Feels realistic
6. **SpecialistStrategy reduces waste** — Focus energy on domains you own

---

## Next Steps

- Try different strategies and observe leaderboards
- Combine strategies for interesting behavior
- Build a custom strategy for your domain
- See: [Use Cases](use-cases.md) — Practical applications

