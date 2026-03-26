# Custom Judges

Learn how to evaluate submissions your way: using metrics, LLMs, consensus, or custom logic.

---

## Judge Types

ORC provides three built-in judges. Pick the one that fits your evaluation criteria.

---

## 1. MetricsJudge (Numeric Evaluation)

Evaluate based on measurable metrics. No LLM needed, deterministic results.

### Simple Metrics

```python
from orc.judges import MetricsJudge
from orc import Elder

# Evaluate on speed and accuracy
judge = MetricsJudge(weights={
    "speed": 0.6,      # 60% weight on speed (lower is better)
    "accuracy": 0.4,   # 40% weight on accuracy (higher is better)
})

elder = Elder(judge=judge)
```

### Multiple Metrics

```python
judge = MetricsJudge(weights={
    "response_time_ms": 0.3,  # Faster is better
    "token_count": 0.1,        # Shorter is better
    "accuracy_score": 0.4,     # Higher is better
    "cost_cents": 0.2,         # Lower is better
})
```

### How It Works

When a trial executes:

1. Each warrior's `TaskResult` contains `data` dict
2. MetricsJudge looks for metric keys in the data
3. Weighs them according to the config
4. Declares a winner

**Ensure your TaskResult includes metrics:**

```python
TaskResult.success(
    task_id="task_123",
    data={
        "response": "Analysis complete",
        "response_time_ms": 234,
        "token_count": 512,
        "accuracy_score": 0.95,
        "cost_cents": 1.50,
    }
)
```

### Use Case

- **Testing/Development** — No external LLM, fast evaluation
- **Deterministic criteria** — Speed, token count, cost
- **Automated evaluation** — Pure metrics, no subjectivity

---

## 2. LLMJudge (AI Evaluation)

Use an LLM (OpenAI, Anthropic, Ollama) as the judge. Evaluates quality, correctness, creativity, etc.

### Basic Setup

```python
from orc.judges import LLMJudge
from orc import Elder
from dynabots_core.providers import OllamaProvider

llm = OllamaProvider(model="qwen2.5:72b")

judge = LLMJudge(
    llm=llm,
    criteria=["accuracy", "completeness", "clarity"],
)

elder = Elder(judge=judge)
```

### Custom Criteria

```python
judge = LLMJudge(
    llm=llm,
    criteria=[
        "Does the response accurately address the task?",
        "Is the reasoning clear and well-structured?",
        "Are there any errors or misconceptions?",
        "How insightful is the analysis?",
        "Would a non-expert understand this?",
    ],
)
```

### Custom System Prompt

Define exactly how the judge should evaluate:

```python
judge = LLMJudge(
    llm=llm,
    criteria=["accuracy", "helpfulness", "tone"],
    system_prompt="""You are an expert evaluator.
You are judging AI assistant responses.

Criteria:
- Accuracy: Is the information correct and factual?
- Helpfulness: Does it address the user's need effectively?
- Tone: Is the response professional and respectful?

For each criterion, score 0.0-1.0.
Declare a winner (A or B).
Be fair and explain your reasoning.""",
)
```

### Use Case

- **Production evaluations** — Real quality assessment
- **Subjective criteria** — Insights, completeness, creativity
- **Multi-dimensional evaluation** — Look at multiple aspects
- **Model comparison** — LLM judges other LLMs fairly

---

## 3. ConsensusJudge (Multiple Judges)

Combine multiple judges. Each votes, majority rules.

### Basic Setup

```python
from orc.judges import ConsensusJudge, MetricsJudge, LLMJudge
from orc import Elder

judge = ConsensusJudge([
    MetricsJudge(weights={"speed": 1.0}),
    LLMJudge(llm, criteria=["accuracy"]),
])

elder = Elder(judge=judge)
```

### Multiple LLM Judges

Use different LLMs to judge (reduces bias):

```python
from dynabots_core.providers import (
    OpenAIProvider,
    AnthropicProvider,
    OllamaProvider,
)

judge = ConsensusJudge([
    LLMJudge(
        OpenAIProvider(model="gpt-4o"),
        criteria=["accuracy", "completeness"],
    ),
    LLMJudge(
        AnthropicProvider(model="claude-3-opus-20250219"),
        criteria=["accuracy", "clarity"],
    ),
    LLMJudge(
        OllamaProvider(model="qwen2.5:72b"),
        criteria=["accuracy", "helpfulness"],
    ),
])
```

### Weighted Consensus

Give some judges more say:

```python
# Not directly supported, but you can:
judge = ConsensusJudge([
    LLMJudge(llm1, criteria=["quality"]),  # 2x votes
    LLMJudge(llm1, criteria=["quality"]),
    MetricsJudge(weights={"speed": 1.0}),  # 1x vote
])
```

### Use Case

- **High-stakes decisions** — Reduce individual judge bias
- **Balanced evaluation** — Mix objective and subjective criteria
- **Research** — Study how different judges correlate
- **Insurance** — If one judge fails, others still vote

---

## 4. Building Your Own Judge

Implement the `Judge` protocol for complete control.

### The Judge Protocol

From `dynabots_core`:

```python
from dynabots_core.protocols.judge import Judge, Submission
from dynabots_core import Verdict

class MyCustomJudge(Judge):
    """Your custom judge."""

    async def evaluate(
        self,
        task: str,
        submissions: list[Submission],
    ) -> Verdict:
        """
        Evaluate submissions and return a verdict.

        Args:
            task: The task description
            submissions: List of Submission objects (typically 2)
                - submission.agent_name: str
                - submission.result: TaskResult

        Returns:
            Verdict(
                winner="agent_name",
                reasoning="Why this agent won",
                scores={"agent1": 0.8, "agent2": 0.6},
                confidence=0.95
            )
        """
        # Your evaluation logic here
        pass
```

### Example: Custom Business Judge

```python
from dynabots_core.protocols.judge import Judge, Submission
from dynabots_core import Verdict

class BusinessValueJudge(Judge):
    """Evaluates based on business value."""

    def __init__(self, revenue_weight=0.5, user_impact_weight=0.5):
        self.revenue_weight = revenue_weight
        self.user_impact_weight = user_impact_weight

    async def evaluate(self, task: str, submissions: list[Submission]) -> Verdict:
        """Score each submission on business metrics."""
        scores = {}

        for sub in submissions:
            data = sub.result.data or {}

            # Extract business metrics from the response
            revenue_impact = data.get("estimated_revenue_impact", 0)
            user_impact = data.get("user_satisfaction_impact", 0)

            # Normalize (example: revenue in $1000s, satisfaction 0-1)
            normalized_revenue = min(revenue_impact / 100, 1.0)  # Max $100k
            normalized_users = user_impact  # 0-1

            # Calculate score
            score = (
                normalized_revenue * self.revenue_weight
                + normalized_users * self.user_impact_weight
            )

            scores[sub.agent_name] = score

        # Determine winner
        winner = max(scores, key=scores.get)
        loser = min(scores, key=scores.get)

        verdict = Verdict(
            winner=winner,
            reasoning=f"{winner} delivers better business value "
                     f"({scores[winner]:.2f} vs {scores[loser]:.2f})",
            scores=scores,
            confidence=0.9 if abs(scores[winner] - scores[loser]) > 0.2 else 0.7,
        )

        return verdict
```

### Use in Arena

```python
from orc import TheArena, Elder

judge = BusinessValueJudge(revenue_weight=0.6, user_impact_weight=0.4)
elder = Elder(judge=judge)

arena = TheArena(warriors=[agent1, agent2], elder=elder)
result = await arena.battle("Recommend a new feature")
```

---

## Example: Code Quality Judge

```python
class CodeQualityJudge(Judge):
    """Evaluates code quality."""

    async def evaluate(self, task: str, submissions: list[Submission]) -> Verdict:
        """Score code submissions."""
        scores = {}

        for sub in submissions:
            code = sub.result.data.get("code", "")

            # Simple metrics
            has_docstrings = code.count('"""') >= 2 or code.count("'''") >= 2
            has_tests = "test_" in code or "@pytest" in code
            line_count = len(code.split("\n"))
            complexity_estimate = code.count("if ") + code.count("for ") + code.count("while ")

            # Score (not meant to be real evaluation logic)
            score = 0.0
            score += 0.3 if has_docstrings else 0
            score += 0.2 if has_tests else 0
            score += 0.3 if 100 < line_count < 500 else 0.1
            score += 0.2 if complexity_estimate < 10 else 0

            scores[sub.agent_name] = score

        winner = max(scores, key=scores.get)

        return Verdict(
            winner=winner,
            reasoning=f"{winner} produced higher quality code",
            scores=scores,
            confidence=0.85,
        )
```

---

## Recommendation: Which Judge?

| Use Case | Judge | Why |
|----------|-------|-----|
| Testing locally | `MetricsJudge` | No API keys, fast, deterministic |
| Comparing models | `LLMJudge` | Evaluate quality subjectively |
| Production (high-stakes) | `ConsensusJudge` | Reduce bias, more confident verdicts |
| Custom evaluation | Custom Judge | Full control, domain-specific logic |

---

## Tips

1. **MetricsJudge is reproducible** — Same inputs always give same winner. Good for testing.

2. **LLMJudge uses tokens** — Might be expensive with large responses. Consider cost.

3. **ConsensusJudge is slower** — Multiple judges = multiple evaluations. But more confidence.

4. **Custom judges can access anything** — TaskResult.data, TaskResult.duration_ms, anything you put there.

5. **Define clear criteria** — Judges perform better with explicit evaluation instructions.

6. **Consider domain-specific judges** — A judge tailored to YOUR domain will produce better verdicts.

---

## Next Steps

- Try `MetricsJudge` for quick testing
- Move to `LLMJudge` for production
- Build a custom judge if you need domain-specific evaluation
- Combine judges with `ConsensusJudge` for high-confidence decisions

See also: [Challenge Strategies](strategies.md) — Control when warriors challenge for leadership.
