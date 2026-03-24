"""
Model Showdown - Real LLMs compete in the Arena.

Three different models (or prompting strategies) compete on coding tasks.
An LLM Judge evaluates their output quality. The best model earns Warchief.

Requirements:
    pip install orc-arena ollama

Setup:
    1. Install Ollama: https://ollama.ai
    2. Pull models:
        ollama pull qwen2.5:14b
        ollama pull phi4-mini
        ollama pull gemma3:1b
    3. Run: python examples/model_showdown.py

Works with whatever Ollama models you have installed.
Falls back to mock warriors if Ollama isn't available.
"""

import asyncio
import sys


# ─── Arena Setup ─────────────────────────────────────────────────────

CODING_CHALLENGES = [
    "Write a Python function that checks if a string is a valid palindrome, ignoring spaces and punctuation. Include edge cases.",
    "Write a Python function to find the two numbers in a list that add up to a target sum. Return their indices.",
    "Write a Python class for a simple LRU cache with get() and put() methods. Use O(1) time complexity.",
    "Write a Python function that flattens a deeply nested dictionary into dot-notation keys. Example: {'a': {'b': 1}} -> {'a.b': 1}",
    "Write a Python async function that fetches multiple URLs concurrently with a max concurrency limit of 5.",
]


async def run_with_ollama():
    """Run the showdown with real Ollama models."""
    from dynabots_core.providers import OllamaProvider
    from orc import Warrior, Elder, TheArena
    from orc.judges import LLMJudge

    # Check which models are available
    probe = OllamaProvider(model="qwen2.5:14b")
    try:
        available = await probe.list_models()
    except Exception as e:
        print(f"  Ollama probe failed: {type(e).__name__}: {e}")
        return False

    available_names = [m.split(":")[0] for m in available]
    print(f"  Ollama models found: {', '.join(available)}\n")

    # Pick 3 models — prefer variety in size/family
    # Order of preference for each warrior slot
    warrior_configs = [
        {
            "name": "Qwen",
            "prefer": ["qwen2.5:14b", "qwen3.5-35b-a3b:latest", "qwen2.5:7b"],
            "prompt": "You are a senior Python engineer. Write clean, efficient, well-documented code. Include type hints.",
            "temp": 0.2,
        },
        {
            "name": "Phi",
            "prefer": ["phi4:latest", "phi4-mini:latest", "phi3:latest"],
            "prompt": "You are an expert Python developer. Write concise, production-ready code with error handling.",
            "temp": 0.3,
        },
        {
            "name": "Gemma",
            "prefer": ["gemma3:1b", "gemma2:latest", "gemma:latest"],
            "prompt": "You are a Python programmer. Write simple, correct code. Focus on readability.",
            "temp": 0.4,
        },
    ]

    # Match warriors to available models
    warriors = []
    used_models = set()
    for config in warrior_configs:
        model = None
        for pref in config["prefer"]:
            if pref in available and pref not in used_models:
                model = pref
                break
        if not model:
            # Fall back to any unused model
            for m in available:
                if m not in used_models:
                    model = m
                    break
        if not model:
            continue

        used_models.add(model)
        llm = OllamaProvider(model=model)
        warriors.append(
            Warrior(
                name=f"{config['name']} ({model})",
                llm_client=llm,
                system_prompt=config["prompt"],
                temperature=config["temp"],
                domains=["coding", "python"],
                capabilities=["code_generation", "problem_solving"],
            )
        )

    if len(warriors) < 2:
        print("  Need at least 2 models. Pull more with: ollama pull <model>")
        return False

    print(f"  Warriors entering the Arena:")
    for w in warriors:
        print(f"    - {w.name}")
    print()

    # The Elder uses the strongest available model to judge
    judge_model = warriors[0].llm_client  # Use the first (typically strongest) model
    elder = Elder(
        llm=judge_model,
        evaluation_criteria="correctness, code quality, efficiency, edge case handling",
    )

    # Create the Arena
    arena = TheArena(
        warriors=warriors,
        elder=elder,
        challenge_probability=0.9,  # High probability — we want to see fights
    )

    # ─── The Showdown ────────────────────────────────────────────────

    print("=" * 70)
    print("THE SHOWDOWN BEGINS")
    print("=" * 70)

    for i, challenge in enumerate(CODING_CHALLENGES, 1):
        short = challenge.split(".")[0][:60]
        print(f"\n{'─' * 70}")
        print(f"  ROUND {i}: {short}...")
        print(f"{'─' * 70}")

        result = await arena.battle(challenge)

        # Show the winning response (truncated)
        if result.winner_result and result.winner_result.data:
            response = result.winner_result.data.get("response", "")
            duration = result.winner_result.duration_ms or 0

            # Show first few lines of the winning code
            lines = response.strip().split("\n")
            preview = "\n".join(lines[:8])
            if len(lines) > 8:
                preview += f"\n  ... ({len(lines) - 8} more lines)"

            print(f"\n  Winner: {result.winner} ({duration}ms)")

            if result.was_challenged and result.verdict:
                reason = result.verdict.reasoning.split("\n")[0][:80]
                print(f"  Reason: {reason}")

            print(f"\n  Code preview:")
            for line in preview.split("\n"):
                print(f"    {line}")

    # ─── Final Leaderboard ───────────────────────────────────────────

    print(f"\n\n{'=' * 70}")
    print("FINAL LEADERBOARD")
    print(f"{'=' * 70}")

    leaderboard = arena.get_leaderboard("coding")
    for i, entry in enumerate(leaderboard, 1):
        crown = " [WARCHIEF]" if entry["is_warlord"] else ""
        print(
            f"  {i}. {entry['agent']:30s} "
            f"Rep: {entry['reputation']:.2f}  "
            f"W:{entry['wins']} L:{entry['losses']}{crown}"
        )

    # Show trial history
    history = arena.get_trial_history()
    if history:
        print(f"\n  Trials fought: {len(history)}")
        for trial in history:
            if trial.verdict:
                print(
                    f"    {trial.verdict.reasoning.split(chr(10))[0][:70]}"
                )

    print(f"\n{'=' * 70}")
    print("Showdown complete!")
    print(f"{'=' * 70}")
    return True


async def run_mock_fallback():
    """Fallback demo with mock warriors (no LLM needed)."""
    from orc import Warrior, Elder, TheArena

    print("  Running with mock warriors (no real LLM).")
    print("  Install Ollama for the real experience: https://ollama.ai\n")

    warriors = [
        Warrior(
            name="GPT-4o (mock)",
            llm_client="gpt-4o",
            system_prompt="Senior engineer",
            domains=["coding", "python"],
            capabilities=["code_generation"],
        ),
        Warrior(
            name="Claude (mock)",
            llm_client="claude-sonnet",
            system_prompt="Expert developer",
            domains=["coding", "python"],
            capabilities=["code_generation"],
        ),
        Warrior(
            name="Qwen (mock)",
            llm_client="qwen2.5",
            system_prompt="Python programmer",
            domains=["coding", "python"],
            capabilities=["code_generation"],
        ),
    ]

    elder = Elder(evaluator_model="metrics")

    arena = TheArena(
        warriors=warriors,
        elder=elder,
        challenge_probability=0.8,
    )

    for challenge in CODING_CHALLENGES[:3]:
        short = challenge.split(".")[0][:50]
        print(f"\n  Round: {short}...")
        result = await arena.battle(challenge)
        print(f"  Victor: {result.winner}")

    print(f"\n  Leaderboard:")
    for entry in arena.get_leaderboard("coding"):
        crown = " [WARCHIEF]" if entry["is_warlord"] else ""
        print(
            f"    {entry['agent']:20s} Rep: {entry['reputation']:.2f}  "
            f"W:{entry['wins']} L:{entry['losses']}{crown}"
        )


async def main():
    print()
    print("=" * 70)
    print("  ORC!! MODEL SHOWDOWN")
    print("  Real LLMs compete for the coding throne")
    print("=" * 70)
    print()

    # Try Ollama first, fall back to mock
    try:
        success = await run_with_ollama()
        if not success:
            await run_mock_fallback()
    except Exception as e:
        print(f"  Failed to use Ollama: {type(e).__name__}: {e}\n")
        await run_mock_fallback()


if __name__ == "__main__":
    asyncio.run(main())
