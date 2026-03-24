"""
Quick Battle - A minimal example of Warriors fighting in The Arena.

This example requires NO external LLMs - it uses mock agents and MetricsJudge.
Just run: python examples/quick_battle.py
"""

import asyncio
from orc import Warrior, Elder, TheArena


async def main():
    """Run a quick battle between three warriors."""

    print("=" * 60)
    print("WELCOME TO THE ARENA")
    print("=" * 60)
    print()

    # Create three Warriors with OVERLAPPING domains
    # Domain overlap is what triggers challenges and trials!
    warriors = [
        Warrior(
            name="Grok",
            llm_client="mock",
            system_prompt="You are a powerful orc warrior.",
            capabilities=["melee_combat", "strategy", "leadership"],
            domains=["combat", "strategy"],  # overlaps with Thrall on combat
        ),
        Warrior(
            name="Thrall",
            llm_client="mock",
            system_prompt="You are a wise orc shaman.",
            capabilities=["magic", "healing", "combat_magic"],
            domains=["combat", "magic"],  # overlaps with Grok on combat, Sylvanas on magic
        ),
        Warrior(
            name="Sylvanas",
            llm_client="mock",
            system_prompt="You are a cunning dark ranger.",
            capabilities=["archery", "dark_magic", "tactics"],
            domains=["combat", "magic", "strategy"],  # overlaps with everyone
        ),
    ]

    print(f"Warriors: {', '.join(w.name for w in warriors)}")
    print(f"All three claim the 'combat' domain - expect blood!\n")

    # Create an Elder judge (defaults to MetricsJudge)
    elder = Elder(
        evaluator_model="metrics_judge",
        evaluation_criteria="Evaluate based on accuracy and speed.",
    )

    # Create The Arena with HIGH challenge probability for this demo
    arena = TheArena(
        warriors=warriors,
        elder=elder,
        challenge_probability=0.8,  # 80% chance of challenge when domains overlap
    )

    # Run battles - with overlapping domains, challenges WILL happen
    challenges = [
        "Lead the charge against the enemy fortress",
        "Cast a devastating spell on the battlefield",
        "Plan the siege of the northern stronghold",
        "Defend the war camp from a surprise attack",
        "Duel the enemy champion in single combat",
    ]

    for challenge in challenges:
        print(f"\n--- CHALLENGE: {challenge} ---")
        result = await arena.battle(challenge)
        if result.was_challenged and result.verdict:
            reason = result.verdict.reasoning.split("\n")[0][:80]
            print(f"  TRIAL: {reason}")
        print(f"  Victor: {result.winner}")

    # Show final standings
    print("\n" + "=" * 60)
    print("FINAL STANDINGS")
    print("=" * 60)

    for domain in ["combat", "magic", "strategy"]:
        leaderboard = arena.get_leaderboard(domain)
        if leaderboard:
            print(f"\n  {domain.upper()} DOMAIN:")
            for i, entry in enumerate(leaderboard):
                crown = " [WARCHIEF]" if entry["is_warlord"] else ""
                print(
                    f"    {i+1}. {entry['agent']:12s} "
                    f"Rep: {entry['reputation']:.2f}  "
                    f"W:{entry['wins']} L:{entry['losses']}{crown}"
                )

    print("\n" + "=" * 60)
    print("Battle complete!")


if __name__ == "__main__":
    asyncio.run(main())
