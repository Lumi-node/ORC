# Quick Start

Get your first battle running in 5 minutes. No external LLMs needed.

---

## Step 1: Create Your First Warriors

A **Warrior** is an AI agent. It has a name, an LLM client, a system prompt, and domains it claims expertise in.

Create a file called `battle.py`:

```python
import asyncio
from orc import Warrior, Elder, TheArena
from orc.judges import MetricsJudge

# Create first warrior
grok = Warrior(
    name="Grok",
    llm_client="mock",  # Mock mode: simulates variable performance
    system_prompt="You are a powerful orc warrior with combat expertise.",
    capabilities=["melee_combat", "strategy", "leadership"],
    domains=["combat", "strategy"],  # Grok claims these domains
)

# Create second warrior (overlapping domains triggers challenges!)
thrall = Warrior(
    name="Thrall",
    llm_client="mock",
    system_prompt="You are a wise shaman with magical abilities.",
    capabilities=["magic", "healing", "combat_magic"],
    domains=["combat", "magic"],  # Thrall also claims "combat"
)

# Create third warrior
sylvanas = Warrior(
    name="Sylvanas",
    llm_client="mock",
    system_prompt="You are a cunning dark ranger with stealth tactics.",
    capabilities=["archery", "dark_magic", "tactics"],
    domains=["combat", "magic", "strategy"],  # Overlaps with everyone
)

warriors = [grok, thrall, sylvanas]
```

**Key points:**

- `llm_client="mock"` uses mock agents (no API keys needed for testing)
- `domains` are what the warrior claims expertise in
- Overlapping domains trigger challenges (this is how trials happen!)
- `capabilities` describe what the warrior can do (for evaluation)

---

## Step 2: Create an Elder Judge

An **Elder** evaluates battles and declares winners.

Add to `battle.py`:

```python
# Create an Elder with MetricsJudge (no LLM needed)
elder = Elder(
    judge=MetricsJudge(
        weights={
            "accuracy": 0.5,
            "speed": 0.3,
            "clarity": 0.2,
        }
    )
)
```

**Judge types:**

- `MetricsJudge` — Evaluates using metrics (speed, accuracy, etc.) — no LLM needed
- `LLMJudge` — Uses an LLM to evaluate (requires OpenAI, Anthropic, or Ollama)
- `ConsensusJudge` — Combines multiple judges and votes

For quick testing, use `MetricsJudge`. For production, use `LLMJudge` with your preferred LLM provider.

---

## Step 3: Enter The Arena

**TheArena** is the orchestration engine where warriors compete.

Add to `battle.py`:

```python
async def main():
    # Create The Arena
    arena = TheArena(
        warriors=warriors,
        elder=elder,
        challenge_probability=0.8,  # 80% chance of challenge on domain overlap
    )

    # Define some battles
    battles = [
        "Lead the charge against the enemy fortress",
        "Cast a devastating spell on the battlefield",
        "Plan the siege of the northern stronghold",
        "Defend the war camp from a surprise attack",
        "Duel the enemy champion in single combat",
    ]

    # Run each battle
    for battle_task in battles:
        print(f"\n--- CHALLENGE: {battle_task} ---")
        result = await arena.battle(battle_task)
        print(f"Winner: {result.winner}")

        if result.was_challenged and result.verdict:
            print(f"Verdict: {result.verdict.reasoning[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Step 4: Check the Leaderboard

After battles, see who dominates each domain:

```python
async def main():
    # ... [previous code] ...

    # After battles, check the leaderboard
    print("\n" + "=" * 60)
    print("FINAL STANDINGS")
    print("=" * 60)

    for domain in ["combat", "magic", "strategy"]:
        leaderboard = arena.get_leaderboard(domain)
        if leaderboard:
            print(f"\n{domain.upper()} DOMAIN:")
            for i, entry in enumerate(leaderboard):
                crown = " [WARCHIEF]" if entry["is_warlord"] else ""
                print(
                    f"  {i+1}. {entry['agent']:12s} "
                    f"Rep: {entry['reputation']:.2f}  "
                    f"W:{entry['wins']} L:{entry['losses']}{crown}"
                )
```

---

## Complete Example

Here's the full `battle.py`:

```python
import asyncio
from orc import Warrior, Elder, TheArena
from orc.judges import MetricsJudge

async def main():
    # Create Warriors
    grok = Warrior(
        name="Grok",
        llm_client="mock",
        system_prompt="You are a powerful orc warrior with combat expertise.",
        capabilities=["melee_combat", "strategy", "leadership"],
        domains=["combat", "strategy"],
    )

    thrall = Warrior(
        name="Thrall",
        llm_client="mock",
        system_prompt="You are a wise shaman with magical abilities.",
        capabilities=["magic", "healing", "combat_magic"],
        domains=["combat", "magic"],
    )

    sylvanas = Warrior(
        name="Sylvanas",
        llm_client="mock",
        system_prompt="You are a cunning dark ranger with stealth tactics.",
        capabilities=["archery", "dark_magic", "tactics"],
        domains=["combat", "magic", "strategy"],
    )

    # Create Elder judge
    elder = Elder(judge=MetricsJudge())

    # Enter The Arena
    arena = TheArena(
        warriors=[grok, thrall, sylvanas],
        elder=elder,
        challenge_probability=0.8,
    )

    # Run battles
    print("=" * 60)
    print("WELCOME TO THE ARENA")
    print("=" * 60)

    battles = [
        "Lead the charge against the enemy fortress",
        "Cast a devastating spell on the battlefield",
        "Plan the siege of the northern stronghold",
        "Defend the war camp from a surprise attack",
        "Duel the enemy champion in single combat",
    ]

    for battle_task in battles:
        print(f"\n--- CHALLENGE: {battle_task} ---")
        result = await arena.battle(battle_task)
        print(f"Victor: {result.winner}")

    # Show final standings
    print("\n" + "=" * 60)
    print("FINAL STANDINGS")
    print("=" * 60)

    for domain in ["combat", "magic", "strategy"]:
        leaderboard = arena.get_leaderboard(domain)
        if leaderboard:
            print(f"\n{domain.upper()} DOMAIN:")
            for i, entry in enumerate(leaderboard):
                crown = " [WARCHIEF]" if entry["is_warlord"] else ""
                print(
                    f"  {i+1}. {entry['agent']:12s} "
                    f"Rep: {entry['reputation']:.2f}  "
                    f"W:{entry['wins']} L:{entry['losses']}{crown}"
                )

    print("\nBattle complete!")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Run It

```bash
python battle.py
```

Expected output:

```
============================================================
WELCOME TO THE ARENA
============================================================

--- CHALLENGE: Lead the charge against the enemy fortress ---
Victor: Grok

--- CHALLENGE: Cast a devastating spell on the battlefield ---
Victor: Thrall

--- CHALLENGE: Plan the siege of the northern stronghold ---
Victor: Sylvanas

============================================================
FINAL STANDINGS
============================================================

COMBAT DOMAIN:
  1. Sylvanas      Rep: 0.95   W:3 L:1 [WARCHIEF]
  2. Grok          Rep: 0.72   W:2 L:2
  3. Thrall        Rep: 0.68   W:1 L:3

MAGIC DOMAIN:
  1. Sylvanas      Rep: 0.92   W:2 L:0 [WARCHIEF]
  2. Thrall        Rep: 0.70   W:1 L:1

STRATEGY DOMAIN:
  1. Sylvanas      Rep: 0.90   W:2 L:0 [WARCHIEF]
  2. Grok          Rep: 0.68   W:1 L:1

Battle complete!
```

---

## What Just Happened?

1. **Grok** claimed "combat" and "strategy" domains
2. **Thrall** claimed "combat" and "magic" domains
3. **Sylvanas** claimed all three (overlapping with everyone)
4. On each task, overlapping Warriors competed
5. The **Elder** judged quality based on metrics
6. **Warchiefs** (domain leaders) emerged
7. **Reputation** scores track performance

---

## Next Steps

- **[Core Concepts](concepts.md)** — Understand the architecture in depth
- **[Model Showdown](../guides/model-showdown.md)** — Compare real LLMs (GPT-4, Claude, Ollama)
- **[Custom Judges](../guides/custom-judges.md)** — Build your own evaluation logic
- **[Challenge Strategies](../guides/strategies.md)** — Control when warriors challenge for leadership
