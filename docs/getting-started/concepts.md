# Core Concepts

Understand the fundamentals of ORC's competitive orchestration model.

---

## The Mapping Table

ORC uses fantasy theming over technical concepts:

| ORC Theme | AI Concept | What It Does |
|-----------|-----------|--------------|
| **Warrior** | Agent | An AI assistant with an LLM, system prompt, and claimed domains |
| **Elder** | Judge | Evaluates warrior submissions and determines winners |
| **Warchief** | Leader | The current champion of a domain; holds power until defeated |
| **The Arena** | Orchestrator | Manages competition, tracks reputation, executes trials |
| **Trial** | Head-to-head evaluation | Two warriors compete on the same task; Elder judges |
| **Reputation** | Performance score | Tracked per domain; affects challenge probability |
| **Domain** | Capability area | A category of tasks (e.g., "backend", "data analysis") |
| **Succession** | Leadership change | When a challenger beats the warlord and takes the throne |

---

## The Flow

Here's what happens when a task enters The Arena:

```
┌─────────────────────────────────────────────┐
│ 1. TASK ARRIVES                             │
│    "Optimize database connection pooling"   │
└────────────┬────────────────────────────────┘
             │
             v
┌─────────────────────────────────────────────┐
│ 2. DOMAIN INFERRED                          │
│    Task likely belongs to "backend" domain  │
└────────────┬────────────────────────────────┘
             │
             v
┌─────────────────────────────────────────────┐
│ 3. WARLORD IDENTIFIED                       │
│    Who currently rules "backend"?           │
│    Let's say: Grok (reputation: 0.85)       │
└────────────┬────────────────────────────────┘
             │
             v
┌─────────────────────────────────────────────┐
│ 4. WARLORD ATTEMPTS TASK                    │
│    Grok processes: "Optimize..."            │
│    Returns: TaskResult with response        │
└────────────┬────────────────────────────────┘
             │
             v
┌─────────────────────────────────────────────┐
│ 5. CHALLENGE DECISION                       │
│    Does any other warrior challenge?        │
│    Probability = challenge_probability      │
│    (adjusted by reputation gap)             │
└────────────┬────────────────────────────────┘
        YES  │  NO
            v      v
    ┌──────────┐  ┌──────────────────────┐
    │ 6. TRIAL │  │ Warlord keeps domain │
    └──┬───────┘  └──────────────────────┘
       │
       v
┌─────────────────────────────────────────────┐
│ 7. CHALLENGER EMERGES                       │
│    Thrall (reputation: 0.72) challenges     │
└────────────┬────────────────────────────────┘
             │
             v
┌─────────────────────────────────────────────┐
│ 8. PARALLEL EXECUTION                       │
│    Both attempt same task:                  │
│    Grok   → TaskResult {response, duration} │
│    Thrall → TaskResult {response, duration} │
└────────────┬────────────────────────────────┘
             │
             v
┌─────────────────────────────────────────────┐
│ 9. ELDER JUDGES                             │
│    Evaluates both submissions               │
│    Returns: Verdict with winner             │
└────────────┬────────────────────────────────┘
             │
             v
┌─────────────────────────────────────────────┐
│ 10. SUCCESSION (if challenged warrior won) │
│    No change: Grok stays warlord            │
│    Reputation updated:                      │
│    - Grok: +0.05 (defense bonus)            │
│    - Thrall: -0.02 (loss penalty)           │
│                                             │
│ OR SUCCESSION (if challenger won)          │
│    Thrall becomes new warlord of "backend"  │
│    Reputation updated:                      │
│    - Thrall: +0.1 (victory bonus)           │
│    - Grok: -0.05 (loss penalty)             │
└────────────┬────────────────────────────────┘
             │
             v
      TASK COMPLETE
```

---

## Warriors

A **Warrior** is an AI agent in The Arena.

```python
from orc import Warrior

warrior = Warrior(
    name="Grok",
    llm_client="gpt-4o",           # LLM to use (string or provider instance)
    system_prompt="You are a...",  # Defines expertise
    temperature=0.7,               # LLM temperature
    capabilities=["code_review"],  # What this warrior can do
    domains=["backend"],           # Domains this warrior claims
)
```

**Properties:**

- `name` — Unique identifier
- `llm_client` — The LLM (OpenAI, Anthropic, Ollama, or "mock")
- `system_prompt` — Expertise definition (system role)
- `temperature` — Creativity (0=deterministic, 1=random)
- `capabilities` — Skills (descriptive)
- `domains` — Claimed expertise areas (triggers competitions)

**Key insight:** Warriors don't request permission. They **claim domains**. If another warrior claims the same domain, competition happens.

---

## Domains and Overlaps

Domains are how ORC triggers competition.

Example:

```python
# Grok claims "backend" and "python"
grok = Warrior(..., domains=["backend", "python"])

# Thrall also claims "backend" — competition!
thrall = Warrior(..., domains=["backend", "infrastructure"])

# Sylvanas claims "python" — also competition!
sylvanas = Warrior(..., domains=["python", "devops"])
```

When a task relates to a domain:

1. The current **Warlord** for that domain handles it
2. Other warriors claiming that domain might **challenge**
3. Challenge probability is controlled by `challenge_probability` config
4. If a challenge happens, a **Trial** is executed

---

## Trials

A **Trial** is head-to-head combat: same task, two warriors, Elder judges.

```python
from orc.arena.trial import Trial

trial = Trial(
    task="Optimize database queries",
    domain="backend",
    warlord=grok,
    challenger=thrall,
    judge=elder.judge,
    timeout=300,  # seconds
    parallel=True,  # Run attempts in parallel
)

result = await trial.execute()
print(f"Winner: {result.winner}")
```

**Trial process:**

1. Both warriors receive the **same task**
2. Both attempt to solve it (in parallel or sequentially)
3. **Elder** receives both TaskResults
4. Elder evaluates based on criteria (accuracy, speed, clarity, etc.)
5. Elder declares a winner (or tie)
6. Reputations are updated
7. If challenger won, they become new Warlord

---

## Reputation System

**Reputation** tracks performance per domain, per warrior.

```python
# Check a warrior's reputation
rep = arena.get_reputation("Grok", "backend")
print(f"Grok's backend reputation: {rep}")

# Get full leaderboard for a domain
leaderboard = arena.get_leaderboard("backend", limit=10)
for entry in leaderboard:
    print(f"{entry['agent']}: {entry['reputation']:.2f}")
    if entry['is_warlord']:
        print("  ^ Current Warlord")
```

**Reputation mechanics:**

- **Starting:** Default value (0.5)
- **On trial win:** +0.1 reputation
- **On trial loss:** -0.05 reputation
- **Defense bonus:** Additional +0.05 per defense (if warlord wins)
- **Decay:** 0.01 per hour without defending (optional)
- **Forced rotation:** After N consecutive defenses, warlord is rotated (prevents stagnation)

---

## The Elder (Judge)

An **Elder** evaluates trial outcomes.

ORC provides three judges:

### MetricsJudge (No LLM)

Uses numeric metrics:

```python
from orc.judges import MetricsJudge
from orc import Elder

judge = MetricsJudge(weights={
    "accuracy": 0.5,
    "speed": 0.3,
    "clarity": 0.2,
})

elder = Elder(judge=judge)
```

Best for: Testing, local development, deterministic evaluation.

### LLMJudge (LLM-powered)

Uses an LLM to evaluate:

```python
from orc.judges import LLMJudge
from orc import Elder
from dynabots_core.providers import OllamaProvider

llm = OllamaProvider(model="qwen2.5:72b")

judge = LLMJudge(
    llm,
    criteria=["accuracy", "completeness", "efficiency"],
)

elder = Elder(judge=judge)
```

Best for: Production, nuanced evaluation, subjective criteria.

### ConsensusJudge (Multiple judges)

Combines multiple judges and votes:

```python
from orc.judges import ConsensusJudge
from orc import Elder

judge = ConsensusJudge([
    LLMJudge(llm1, criteria=["accuracy"]),
    MetricsJudge(weights={"speed": 1.0}),
    LLMJudge(llm2, criteria=["clarity"]),
])

elder = Elder(judge=judge)
```

Best for: High-stakes decisions, reducing bias.

---

## The Arena

**The Arena** is the orchestration engine.

```python
from orc import Arena, ArenaConfig

arena = Arena(
    agents=[grok, thrall, sylvanas],
    judge=elder.judge,
    config=ArenaConfig(
        challenge_probability=0.3,  # 30% chance to challenge
        min_reputation_to_challenge=0.2,  # Min rep to initiate challenge
        challenge_cooldown_seconds=300,  # Cooldown after losing
        max_consecutive_defenses=10,  # Force rotation after 10 wins
    ),
)

# Process a task
result = await arena.process("Your task here")
```

Or use the themed wrapper:

```python
from orc import TheArena

arena = TheArena(
    warriors=[grok, thrall, sylvanas],
    elder=elder,
    challenge_probability=0.3,
)

# Same thing, themed API
result = await arena.battle("Your task here")
```

---

## Configuration

Control arena behavior with `ArenaConfig`:

| Setting | Default | Meaning |
|---------|---------|---------|
| `challenge_probability` | 0.3 | Base probability of challenge on overlap |
| `min_reputation_to_challenge` | 0.2 | Minimum reputation to initiate challenge |
| `challenge_cooldown_seconds` | 300 | Cooldown after losing a challenge |
| `min_trials_for_leadership` | 1 | Trials needed to become warlord |
| `leadership_decay_rate` | 0.01 | Reputation decay per hour idle |
| `max_consecutive_defenses` | 10 | Force rotation after N defenses |
| `trial_timeout_seconds` | 300 | Timeout for a single trial |
| `parallel_trial_execution` | True | Run trial attempts in parallel |
| `default_reputation` | 0.5 | Starting reputation for new agents |

---

## Warchiefs

A **Warchief** is a winning warrior.

```python
from orc import TheArena

arena = TheArena(warriors=[grok, thrall], elder=elder)

# Get the current warchief for a domain
warchief = arena.get_warchief("backend")
print(f"Backend Warchief: {warchief.name}")
print(f"Reputation: {warchief.reputation}")
print(f"Warband size: {len(warchief.warband)}")
```

A Warchief has:

- `name` — Warrior name
- `domain` — Domain they control
- `reputation` — Performance score
- `warband` — Defeated warriors they command

---

## Summary

| Concept | Role |
|---------|------|
| **Warrior** | Competes for domain leadership |
| **Domain** | Category of tasks; overlap triggers competition |
| **Trial** | Head-to-head evaluation; Elder judges |
| **Warchief** | Current domain leader |
| **Reputation** | Performance metric; affects challenge probability |
| **Elder** | Judge; evaluates quality |
| **The Arena** | Engine; orchestrates everything |
| **Succession** | Leadership change; new warchief crowned |

Next: [Model Showdown](../guides/model-showdown.md) — See it in action with real LLMs.
