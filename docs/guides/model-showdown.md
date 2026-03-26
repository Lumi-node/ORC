# Model Showdown

A practical guide: **Compare LLM models head-to-head using ORC.**

This is the killer use case. You have multiple models (GPT-4o, Claude, local Ollama). Which performs best on YOUR tasks?

ORC provides the answer: Run them in competition on real tasks, let an Elder judge, and get a leaderboard.

---

## Setup: Three Warriors, Three Models

We'll compare three models on data analysis tasks:

```python
import asyncio
from orc import TheArena, Warrior, Elder
from orc.judges import LLMJudge
from dynabots_core.providers import (
    OllamaProvider,
    OpenAIProvider,
    AnthropicProvider,
)

async def main():
    # Create an LLM for the judge itself
    # Use a high-quality judge model
    judge_llm = OllamaProvider(model="qwen2.5:72b")

    # Create Warriors, each using a different model
    gpt4_warrior = Warrior(
        name="GPT-4o",
        llm_client=OpenAIProvider(model="gpt-4o"),
        system_prompt="""You are an expert data analyst.
Analyze the provided data thoroughly. Provide insights,
identify patterns, and recommend actions. Be concise but thorough.""",
        domains=["data_analysis", "reporting"],
    )

    claude_warrior = Warrior(
        name="Claude",
        llm_client=AnthropicProvider(model="claude-3-opus-20250219"),
        system_prompt="""You are a meticulous data analyst.
Examine data carefully, look for edge cases, and provide
comprehensive analysis with clear recommendations.""",
        domains=["data_analysis", "reporting"],
    )

    ollama_warrior = Warrior(
        name="Llama-2",
        llm_client=OllamaProvider(model="llama2:70b"),
        system_prompt="""You are a data analyst.
Analyze the data provided and offer insights and recommendations
based on what you observe.""",
        domains=["data_analysis", "reporting"],
    )

    # Create Elder judge using LLMJudge
    elder = Elder(
        judge=LLMJudge(
            llm=judge_llm,
            criteria=[
                "accuracy",
                "insight_quality",
                "actionability",
                "clarity",
                "completeness",
            ],
        )
    )

    # Enter The Arena
    arena = TheArena(
        warriors=[gpt4_warrior, claude_warrior, ollama_warrior],
        elder=elder,
        challenge_probability=0.9,  # 90% to ensure trials happen
    )

    print("=" * 70)
    print("MODEL SHOWDOWN: DATA ANALYSIS")
    print("=" * 70)
    print(f"Competing: GPT-4o vs Claude vs Llama-2")
    print(f"Judge: {judge_llm.model}")
    print()

    # Real data analysis tasks
    tasks = [
        """Analyze this sales data:
        Q1: 50k revenue, 100 customers
        Q2: 65k revenue, 130 customers
        Q3: 72k revenue, 145 customers
        Q4: 89k revenue, 180 customers

        What trends do you see? What should the company focus on next quarter?""",

        """A/B test results:
        Control (no email): 2.1% conversion rate, 10k users
        Treatment (email):  3.5% conversion rate, 10k users

        Is the difference significant? What's the business impact?""",

        """Customer churn analysis:
        Total customers: 5000
        Churned this month: 250
        Top churn reasons: Price (40%), Feature gaps (35%), Support (25%)

        What's the annual impact? What should we prioritize?""",

        """Product usage patterns:
        Feature A: 80% daily active users use it
        Feature B: 45% daily active users use it
        Feature C: 12% daily active users use it
        Support tickets mention Feature C 60% of the time.

        What does this tell us? What's one hypotheses to test?""",

        """Revenue per customer (RPC):
        Month 1: $50/customer
        Month 3: $55/customer
        Month 6: $48/customer
        Month 9: $44/customer

        Something's wrong. What's likely happening? How would you investigate?""",
    ]

    # Run the showdown
    for i, task in enumerate(tasks, 1):
        print(f"\n--- TASK {i} ---")
        print(task[:100] + "...")
        result = await arena.battle(task)
        print(f"Winner: {result.winner}")
        if result.was_challenged and result.verdict:
            # Show first 200 chars of verdict
            verdict_text = result.verdict.reasoning[:200]
            print(f"Verdict: {verdict_text}...")

    # Show final leaderboard
    print("\n" + "=" * 70)
    print("FINAL LEADERBOARD")
    print("=" * 70)

    leaderboard = arena.get_leaderboard("data_analysis")
    for i, entry in enumerate(leaderboard, 1):
        crown = " CHAMPION" if entry["is_warlord"] else ""
        print(
            f"{i}. {entry['agent']:15s} "
            f"Rep: {entry['reputation']:.3f}  "
            f"W:{entry['wins']} L:{entry['losses']}{crown}"
        )

    print("\nDone! The best model for your data analysis tasks is clear.")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Setup: Local Ollama (No API Keys)

Don't have API keys? Use Ollama for free, local comparison:

```python
from dynabots_core.providers import OllamaProvider

# Download models first:
# ollama pull qwen2.5:72b
# ollama pull llama2:70b
# ollama pull mistral:latest

judge_llm = OllamaProvider(model="qwen2.5:72b")

# Warriors use different Ollama models
gpt4_warrior = Warrior(
    name="Qwen",
    llm_client=OllamaProvider(model="qwen2.5:72b"),
    system_prompt="You are a data analyst...",
    domains=["data_analysis"],
)

claude_warrior = Warrior(
    name="Llama",
    llm_client=OllamaProvider(model="llama2:70b"),
    system_prompt="You are a data analyst...",
    domains=["data_analysis"],
)

mistral_warrior = Warrior(
    name="Mistral",
    llm_client=OllamaProvider(model="mistral:latest"),
    system_prompt="You are a data analyst...",
    domains=["data_analysis"],
)
```

---

## Expected Output

```
======================================================================
MODEL SHOWDOWN: DATA ANALYSIS
======================================================================
Competing: GPT-4o vs Claude vs Llama-2
Judge: qwen2.5:72b

--- TASK 1 ---
Analyze this sales data...
Winner: GPT-4o

--- TASK 2 ---
A/B test results...
TRIAL: GPT-4o vs Claude
Verdict: Claude's analysis is more thorough, but GPT-4o's...
Winner: Claude

--- TASK 3 ---
Customer churn analysis...
Winner: Claude

--- TASK 4 ---
Product usage patterns...
Winner: GPT-4o

--- TASK 5 ---
Revenue per customer...
TRIAL: Claude vs Llama-2
Winner: Claude

======================================================================
FINAL LEADERBOARD
======================================================================
1. Claude          Rep: 0.890  W:4 L:1 CHAMPION
2. GPT-4o          Rep: 0.810  W:3 L:2
3. Llama-2         Rep: 0.620  W:0 L:5

Done! The best model for your data analysis tasks is clear.
```

---

## What This Tells You

The leaderboard shows:

- **Claude** is the best data analyst for your tasks (rep 0.890, 4 wins)
- **GPT-4o** is solid but slightly weaker (rep 0.810, 3 wins)
- **Llama-2** struggles on this domain (rep 0.620, 0 wins)

**You can use this to:**

1. **Pick a default model** — Deploy Claude as your data analyst
2. **Optimize cost** — GPT-4o is cheaper; maybe it's "good enough"?
3. **Route intelligently** — Send complex analysis to Claude, simple stuff to GPT-4o
4. **Test improvements** — Add a Warrior with a new system prompt, see if it ranks higher
5. **Evaluate new models** — New model released? Drop it in, run the showdown, see where it ranks

---

## Comparing Prompts

**Same model, different system prompts:**

```python
# Analytical prompt
analyst = Warrior(
    name="Analyst-Prompt",
    llm_client=OpenAIProvider(model="gpt-4o"),
    system_prompt="""You are a data analyst.
Focus on numbers, trends, and statistical significance.
Be precise and avoid speculation.""",
    domains=["data_analysis"],
)

# Strategic prompt
strategist = Warrior(
    name="Strategist-Prompt",
    llm_client=OpenAIProvider(model="gpt-4o"),
    system_prompt="""You are a business strategist.
Analyze data for strategic insights and recommendations.
Think about competitive advantage and market dynamics.""",
    domains=["data_analysis"],
)

# Creative prompt
creative = Warrior(
    name="Creative-Prompt",
    llm_client=OpenAIProvider(model="gpt-4o"),
    system_prompt="""You are a creative data storyteller.
Find compelling narratives in the data. Make insights memorable.
Use metaphors and examples to explain findings.""",
    domains=["data_analysis"],
)

arena = TheArena(
    warriors=[analyst, strategist, creative],
    elder=elder,
    challenge_probability=0.9,
)

# Run tasks... which prompt wins?
```

Now you know: **Which system prompt performs best on YOUR tasks?**

---

## Key Insights

**ORC is perfect for model/prompt selection because:**

1. **Real tasks** — Evaluate on your actual use cases, not benchmarks
2. **Objective judging** — Elder compares fairly using consistent criteria
3. **Leaderboard** — Clear winner(s) emerge over multiple trials
4. **Cost tracking** — Note which model costs less (if relevant)
5. **Iteration** — Add new prompts/models, run again, see improvement

**Next steps:**

- Run a showdown on your specific tasks
- Deploy the winner (or top 2) in production
- Periodically re-run with new models/prompts to stay competitive
- Use reputation scores to auto-route tasks (best agent handles each domain)

---

## Advanced: Custom Judge Criteria

For your domain-specific evaluation:

```python
elder = Elder(
    judge=LLMJudge(
        llm=judge_llm,
        criteria=[
            "technical_accuracy - Does the analysis correctly interpret the data?",
            "business_insight - Does it reveal actionable business insights?",
            "clarity - Is the explanation clear to a non-technical stakeholder?",
            "depth - Does it go beyond surface-level observations?",
            "risk_awareness - Does it identify potential pitfalls or risks?",
        ],
        system_prompt="""You are an expert evaluator of data analysis work.
Assess each submission across multiple dimensions.
Be fair and detailed in your evaluation.
Provide scores (0.0-1.0) for each criterion.""",
    )
)
```

The judge will now evaluate based on YOUR criteria.

---

See also: [Custom Judges](custom-judges.md) for building domain-specific evaluation logic.
