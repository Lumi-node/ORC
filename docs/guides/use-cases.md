# Use Cases

**Real-world applications of competitive multi-agent orchestration.**

---

## 1. Model Selection (Which LLM?)

**Problem:** You have multiple LLM options (GPT-4, Claude, Llama). Which one is best for YOUR tasks?

Benchmarks are generic. You need empirical evidence on your specific use cases.

### Solution

Run ORC's Model Showdown:

```python
import asyncio
from orc import TheArena, Warrior, Elder
from orc.judges import LLMJudge
from dynabots_core.providers import OllamaProvider, OpenAIProvider, AnthropicProvider

async def main():
    # Judge model
    judge_llm = OllamaProvider(model="qwen2.5:72b")

    # Warriors using different models
    gpt4 = Warrior(
        name="GPT-4o",
        llm_client=OpenAIProvider(model="gpt-4o"),
        system_prompt="You are an expert...",
        domains=["analysis"],
    )

    claude = Warrior(
        name="Claude",
        llm_client=AnthropicProvider(model="claude-3-opus-20250219"),
        system_prompt="You are an expert...",
        domains=["analysis"],
    )

    mistral = Warrior(
        name="Mistral",
        llm_client=OllamaProvider(model="mistral:latest"),
        system_prompt="You are an expert...",
        domains=["analysis"],
    )

    elder = Elder(judge=LLMJudge(judge_llm, criteria=["accuracy", "clarity"]))

    arena = TheArena(
        warriors=[gpt4, claude, mistral],
        elder=elder,
        challenge_probability=0.9,
    )

    # Your real tasks
    tasks = [
        "Analyze customer feedback...",
        "Summarize financial report...",
        "Evaluate product requirements...",
    ]

    for task in tasks:
        result = await arena.battle(task)

    # Winner: clear choice for your domain
    leaderboard = arena.get_leaderboard("analysis")
    best_model = leaderboard[0]["agent"]
    print(f"Deploy: {best_model}")

asyncio.run(main())
```

### Benefit

- **Empirical** — Based on your real tasks, not generic benchmarks
- **Clear winner** — Leaderboard shows the best model for YOU
- **Cost-aware** — Pick the cheapest model that's "good enough"
- **Reproducible** — Run quarterly to see if new models are better

---

## 2. Prompt Engineering (Which Prompt?)

**Problem:** Different system prompts produce different results. Which system prompt is best?

ORC lets you compare prompts head-to-head.

### Solution

Same model, different prompts:

```python
from orc import Warrior, Elder, TheArena
from orc.judges import LLMJudge
from dynabots_core.providers import OpenAIProvider

judge_llm = OpenAIProvider(model="gpt-4o")

# Same model, different prompts
analytical = Warrior(
    name="Analytical",
    llm_client=OpenAIProvider(model="gpt-4o"),
    system_prompt="""You are a data analyst. Focus on numbers and trends.
Be precise. Avoid speculation.""",
    domains=["analysis"],
)

creative = Warrior(
    name="Creative",
    llm_client=OpenAIProvider(model="gpt-4o"),
    system_prompt="""You are a creative analyst. Find novel insights.
Look for interesting patterns. Be imaginative.""",
    domains=["analysis"],
)

concise = Warrior(
    name="Concise",
    llm_client=OpenAIProvider(model="gpt-4o"),
    system_prompt="""You are a concise analyst. Be brief and direct.
Skip fluff. Deliver actionable insights fast.""",
    domains=["analysis"],
)

elder = Elder(judge=LLMJudge(judge_llm))

arena = TheArena(
    warriors=[analytical, creative, concise],
    elder=elder,
)

# Run on your tasks...
# Winner: best system prompt for your use case
```

### Benefit

- **Optimize without cost** — Try unlimited prompts (cheap compared to new models)
- **Domain-specific** — Find the prompt that works best for YOUR tasks
- **Iterative** — Refine winning prompt, test again
- **Team-driven** — Sales team suggests prompt, test it

---

## 3. Agent Routing (Self-Optimizing)

**Problem:** You have multiple agents (data team, code team, writing team). Which agent should handle each task?

Static routing is hard-coded. ORC's competitive system automatically routes to the best agent.

### Solution

Multi-domain arena:

```python
from orc import Warrior, Elder, TheArena
from orc.judges import LLMJudge

# Specialist agents
data_agent = Warrior(
    name="DataAgent",
    llm_client=...,
    system_prompt="You specialize in data analysis and SQL...",
    domains=["data_analysis", "sql", "metrics"],
)

code_agent = Warrior(
    name="CodeAgent",
    llm_client=...,
    system_prompt="You specialize in Python development...",
    domains=["backend", "python", "architecture"],
)

docs_agent = Warrior(
    name="DocsAgent",
    llm_client=...,
    system_prompt="You specialize in technical writing...",
    domains=["documentation", "copywriting", "communication"],
)

# Single judge
elder = Elder(judge=LLMJudge(...))

# Arena with multiple domains
arena = TheArena(
    warriors=[data_agent, code_agent, docs_agent],
    elder=elder,
)

# Incoming tasks
async def route_task(task_description):
    # Let the arena decide
    result = await arena.battle(task_description)
    # Winner is the best agent for this task
    return result.winner

# Over time, warchiefs emerge for each domain
data_warchief = arena.get_warchief("data_analysis")
code_warchief = arena.get_warchief("backend")
docs_warchief = arena.get_warchief("documentation")
```

### Benefit

- **No manual routing** — Arena figures out the best agent automatically
- **Adapts over time** — If an agent improves, it naturally wins more domains
- **Self-optimizing** — Leadership changes as agents perform
- **Fair competition** — Every agent gets a chance to prove itself

---

## 4. Research (Emergent Behavior)

**Problem:** How do multiple agents interact? Can we study emergent hierarchies?

ORC provides a framework for multi-agent research.

### Solution

```python
import asyncio
from orc import Arena, ArenaConfig, MetricsJudge
from dynabots_core import Agent  # Implement custom agents

class ResearchAgent(Agent):
    """Custom agent for research."""
    def __init__(self, name, strategy):
        self.name = name
        self.strategy = strategy

    async def process_task(self, task, context=None):
        # Your research logic
        pass

async def main():
    # Create agents with different strategies
    agents = [
        ResearchAgent("Aggressive", strategy="always_challenge"),
        ResearchAgent("Conservative", strategy="reputation_based"),
        ResearchAgent("Patient", strategy="cooldown"),
        ResearchAgent("Specialist", strategy="specialist"),
    ]

    judge = MetricsJudge()
    arena = Arena(
        agents=agents,
        judge=judge,
        config=ArenaConfig(
            challenge_probability=0.5,
            max_consecutive_defenses=5,
        ),
    )

    # Run long trial
    tasks = ["Task A", "Task B", "Task C"] * 100  # 300 tasks

    for i, task in enumerate(tasks):
        result = await arena.process(task)

        # Track over time
        if i % 30 == 0:
            for domain in ["research"]:
                lb = arena.get_leaderboard(domain)
                print(f"Task {i}: Leaderboard")
                for entry in lb:
                    print(f"  {entry['agent']}: rep={entry['reputation']:.2f}")

    # Analyze emergent patterns
    print("\nFinal Leaderboard:")
    for entry in arena.get_leaderboard("research"):
        print(f"{entry['agent']}: {entry['reputation']:.3f} "
              f"(W:{entry['wins']} L:{entry['losses']})")

asyncio.run(main())
```

### Research Questions

- Do aggressive agents succeed or burn out?
- What strategy wins over time?
- Does leadership concentration (Zipfian distribution) emerge?
- How does diversity affect system performance?
- What causes leadership transitions?

### Benefit

- **Novel insights** — Observe multi-agent dynamics
- **Configurable** — Adjust parameters, re-run, compare
- **Reproducible** — Same code, different seeds, different outcomes (or same)
- **Publication-ready** — Clear metrics, leaderboards, verdicts

---

## 5. Feature A/B Testing (Agile Decisions)

**Problem:** We built two versions of a feature. Which is better?

Instead of beta testing with users, pit them against each other in ORC.

### Solution

```python
# Version A: Current implementation
current = Warrior(
    name="FeatureA-Current",
    llm_client=...,
    system_prompt="""Implement the feature using the current approach:
single database query, real-time updates.""",
    domains=["feature_implementation"],
)

# Version B: Proposed implementation
proposed = Warrior(
    name="FeatureB-Proposed",
    llm_client=...,
    system_prompt="""Implement the feature using the proposed approach:
caching layer, eventual consistency.""",
    domains=["feature_implementation"],
)

elder = Elder(judge=LLMJudge(
    llm,
    criteria=[
        "Performance",
        "Maintainability",
        "User Experience",
        "Scalability",
    ],
))

arena = TheArena(warriors=[current, proposed], elder=elder)

# Test cases (user scenarios)
scenarios = [
    "100 concurrent users...",
    "10,000 user dataset...",
    "Mobile client use case...",
    "Offline then online scenario...",
]

for scenario in scenarios:
    result = await arena.battle(scenario)
    print(f"{scenario} -> Winner: {result.winner}")

# Leaderboard tells you which is better overall
winner = arena.get_leaderboard("feature_implementation")[0]["agent"]
print(f"Deploy: {winner}")
```

### Benefit

- **Quick decisions** — No beta testing, get answer in minutes
- **Objective comparison** — Judge compares fairly
- **Cheap** — Running LLM scenarios costs less than beta
- **Repeatable** — Run again with new scenarios

---

## Which Use Case Is For You?

| Use Case | Goal | Tools | Effort |
|----------|------|-------|--------|
| Model Selection | Find best LLM | Multiple LLM providers + LLMJudge | Low |
| Prompt Engineering | Find best prompt | One LLM + custom prompts | Low |
| Agent Routing | Auto-route to best agent | Multi-domain arena | Medium |
| Research | Study multi-agent dynamics | Custom agents + metrics | High |
| Feature A/B Testing | Compare implementations | Domain-specific agents | Medium |

---

## General Recipe

1. **Identify the competition** — What are you comparing? (Models, prompts, agents, implementations)
2. **Create Warriors** — One for each option
3. **Create Elder judge** — Aligned with your evaluation criteria
4. **Run trials** — On your real tasks/scenarios
5. **Read leaderboard** — Clear winner emerges
6. **Deploy or iterate** — Act on the results

---

## Next Steps

- Pick a use case above
- Follow the pattern
- Adapt for your domain
- See results in minutes

**ORC makes multi-agent competition simple, fast, and objective.**

