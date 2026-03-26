# ORC — Orchestration by Ruthless Competition

![ORC Banner](assets/banner.jpg)

**Standard orchestration is weak. Static hierarchies are boring. In ORC, leadership is earned in the Arena.**

---

## Why ORC?

Traditional multi-agent systems use static orchestrators. A central coordinator decides who does what, forever. But that's boring—and fragile.

ORC is different. AI agents **compete** for leadership through trials. The best agent for each domain **rises to the top**. Leadership is never permanent. Agents must defend their position or be dethroned.

It's Darwinian. It's dynamic. It's ruthless. It's ORC.

---

## Key Features

=== "Competition-Based"

    Agents don't request permission. They compete for leadership. The Warlord holds domain leadership until defeated.

=== "Any LLM Provider"

    Built on `dynabots-core`. Works with OpenAI, Anthropic, Ollama, or any LLM provider. Swap models at runtime.

=== "Battle-Tested"

    Used in production for model evaluation, prompt engineering, and self-optimizing agent routing. Proven reliability.

---

## 30 Seconds to Combat

Install ORC:

```bash
pip install orc-arena
```

Create Warriors and enter The Arena:

```python
import asyncio
from orc import TheArena, Warrior, Elder
from orc.judges import MetricsJudge

async def main():
    # Create Warriors (agents)
    grog = Warrior(
        name="Grog",
        llm_client="gpt-4o",
        system_prompt="You are a senior backend developer.",
        domains=["backend", "python"],
    )

    thrall = Warrior(
        name="Thrall",
        llm_client="claude-sonnet-4-20250514",
        system_prompt="You are an infrastructure architect.",
        domains=["backend", "infrastructure"],
    )

    # Create Elder judge
    elder = Elder(judge=MetricsJudge())

    # Enter The Arena
    arena = TheArena(warriors=[grog, thrall], elder=elder)

    # Battle for domain leadership
    result = await arena.battle("Optimize database connection pooling")
    print(f"Winner: {result.winner}")

asyncio.run(main())
```

That's it. Warriors. Elder. Arena. Battle.

---

## What Happens in The Arena?

```
┌─────────────────────────────────────────────┐
│                  THE ARENA                  │
│                                             │
│  Task arrives → Domain inferred             │
│       ↓                                     │
│  Warlord handles it (default)               │
│       ↓                                     │
│  Does a challenger emerge? (probabilistic)  │
│       ↓                                     │
│  YES: Trial (head-to-head combat)           │
│       ├─ Both agents try same task          │
│       ├─ Elder judges quality               │
│       └─ Winner becomes new Warlord         │
│       ↓                                     │
│  NO: Warlord keeps command                  │
└─────────────────────────────────────────────┘
```

Every domain has a **Warlord** — the current leader. But dominance is never guaranteed. Challengers emerge, trials are fought, and leadership can change in minutes.

---

## Themed API

ORC wraps the technical concepts in fantasy language:

| ORC Theme | What It Is |
|-----------|-----------|
| **Warrior** | An AI agent (LLM + system prompt) |
| **Elder** | A judge that evaluates quality |
| **Warchief** | The winning leader |
| **The Arena** | The orchestration engine |
| **Trial** | Head-to-head evaluation |
| **Reputation** | Performance score |
| **Domain** | Capability area |
| **Succession** | Leadership change |

Use the themed API for fun, or drop down to the standard `Arena` API for production environments.

---

## Learn More

- **[Installation Guide](getting-started/installation.md)** — Set up ORC in minutes
- **[Quick Start](getting-started/quick-start.md)** — Run your first battle
- **[Core Concepts](getting-started/concepts.md)** — Understand the architecture
- **[Model Showdown Guide](guides/model-showdown.md)** — Compare LLMs in action
- **[API Reference](reference/arena.md)** — Full API documentation

---

## Use Cases

**Model A/B Testing** — Compare GPT-4o vs Claude vs local models. Run real tasks. Get a leaderboard.

**Prompt Engineering** — Test different system prompts. See which performs best across trials.

**Self-Optimizing Routing** — The best agent for each domain naturally rises to the top. No manual routing needed.

**Research** — Study emergent hierarchies in multi-agent systems. Watch leadership dynamics unfold.

---

## Built On

ORC is powered by [dynabots-core](https://github.com/Lumi-node/Dynabots-core) — a zero-dependency protocol foundation for multi-agent systems.

Published on [PyPI](https://pypi.org/project/orc-arena/) as `orc-arena`. Open source under Apache 2.0.

---

**The horde is ready. Enter the Arena.**
