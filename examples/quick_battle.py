"""
Quick Battle - A minimal example of Warriors fighting in The Arena.

This example requires NO external LLMs - it uses mock agents and MetricsJudge.
Just run: python examples/quick_battle.py
"""

import asyncio
from orc import Warrior, Elder, TheArena
from orc.judges import MetricsJudge


async def main():
    """Run a quick battle between three warriors."""

    print("=" * 60)
    print("WELCOME TO THE ARENA")
    print("=" * 60)
    print()

    # Create three Warriors with mock LLM clients (just strings)
    warriors = [
        Warrior(
            name="Grok",
            llm_client="mock_llm_1",
            system_prompt="You are a powerful orc warrior with exceptional strength.",
            temperature=0.5,
            capabilities=["melee_combat", "strategy", "leadership"],
            domains=["combat", "tactics"],
        ),
        Warrior(
            name="Thrall",
            llm_client="mock_llm_2",
            system_prompt="You are a wise orc shaman with magical powers.",
            temperature=0.3,
            capabilities=["magic", "healing", "elemental_control"],
            domains=["magic", "healing"],
        ),
        Warrior(
            name="Sylvanas",
            llm_client="mock_llm_3",
            system_prompt="You are a skilled orc ranger with unmatched archery.",
            temperature=0.6,
            capabilities=["archery", "stealth", "tracking"],
            domains=["ranged_combat", "hunting"],
        ),
    ]

    print(f"Warriors registered: {', '.join(w.name for w in warriors)}")
    print()

    # Create an Elder judge (uses MetricsJudge by default)
    elder = Elder(
        evaluator_model="metrics_judge",
        evaluation_criteria="Evaluate based on accuracy and speed.",
    )
    print(f"Elder ready to judge")
    print()

    # Create The Arena
    arena = TheArena(
        warriors=warriors,
        elder=elder,
        challenge_probability=0.4,
    )

    # Run a few battles
    challenges = [
        "Defeat the invading army",
        "Retrieve the lost artifact",
        "Protect the village from darkness",
    ]

    for challenge in challenges:
        print(f"\n--- CHALLENGE: {challenge} ---")
        result = await arena.battle(challenge)
        print(f"Victory: {result.winner}")
        if result.verdict:
            print(f"Reasoning: {result.verdict.reasoning[:80]}...")

    print("\n" + "=" * 60)
    print("LEADERBOARD")
    print("=" * 60)

    # Show leaderboard for each domain
    for domain in ["combat", "magic", "ranged_combat"]:
        leaderboard = arena.get_leaderboard(domain)
        print(f"\n{domain.upper()} DOMAIN:")
        for entry in leaderboard:
            status = " (Warlord)" if entry["is_warlord"] else ""
            print(
                f"  {entry['agent']}: rep={entry['reputation']:.2f}, "
                f"wins={entry['wins']}, losses={entry['losses']}{status}"
            )

    print("\n" + "=" * 60)
    print("Battle complete!")


if __name__ == "__main__":
    asyncio.run(main())
