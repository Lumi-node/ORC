"""
Full Campaign - A complete example showing Warriors, domains, challenge strategies,
and multiple rounds of battles.

This example demonstrates:
- Multiple Warriors with different domains and capabilities
- Challenge strategies on warriors
- An Elder judge with MetricsJudge
- Multiple rounds of battles
- Final leaderboard and Warchief extraction
"""

import asyncio
from orc import Warrior, Elder, TheArena, CooldownStrategy
from orc.judges import MetricsJudge


async def main():
    """Run a full campaign with multiple battles."""

    print("\n" + "=" * 70)
    print("ORC ARENA: FULL CAMPAIGN")
    print("=" * 70 + "\n")

    # Create Warriors with different specializations
    warriors = [
        Warrior(
            name="Durotan",
            llm_client="gpt-4-mock",
            system_prompt="You are Durotan, a master tactician and war leader.",
            temperature=0.4,
            capabilities=["strategy", "leadership", "diplomacy", "combat_planning"],
            domains=["strategy", "leadership", "politics"],
        ),
        Warrior(
            name="Orgrim",
            llm_client="gpt-4-mock",
            system_prompt="You are Orgrim Doomhammer, a legendary warrior and slayer.",
            temperature=0.6,
            capabilities=["melee_combat", "weapon_mastery", "intimidation"],
            domains=["combat", "melee_weapons"],
        ),
        Warrior(
            name="Garona",
            llm_client="gpt-4-mock",
            system_prompt="You are Garona, a cunning rogue and assassin.",
            temperature=0.5,
            capabilities=["stealth", "assassination", "espionage", "theft"],
            domains=["espionage", "assassination", "stealth"],
        ),
        Warrior(
            name="Gul'dan",
            llm_client="gpt-4-mock",
            system_prompt="You are Gul'dan, a powerful warlock and sorcerer.",
            temperature=0.7,
            capabilities=["dark_magic", "summoning", "necromancy", "curse_casting"],
            domains=["magic", "dark_magic", "summoning"],
        ),
        Warrior(
            name="Durotan",
            llm_client="gpt-4-mock",
            system_prompt="You are Grommash Hellscream, a berserker of legend.",
            temperature=0.8,
            capabilities=["rage", "berserker_combat", "heavy_weapons"],
            domains=["combat", "berserker_rage"],
        ),
    ]

    # Set challenge strategies on some warriors
    warriors[1].challenge_strategy = CooldownStrategy(base_cooldown=3600)

    print("Warband assembled:")
    for w in warriors:
        print(f"  - {w.name}: {', '.join(w.domains)}")
    print()

    # Create Elder judge
    elder = Elder(
        evaluator_model="metrics",
        evaluation_criteria="Evaluate submission quality, speed, and effectiveness.",
    )

    # Create The Arena with different settings
    arena = TheArena(
        warriors=warriors,
        elder=elder,
        challenge_probability=0.5,
    )

    # Campaign challenges - grouped by theme
    campaign = {
        "STRATEGY PHASE": [
            "Devise a winning military strategy",
            "Plan a diplomatic alliance",
            "Organize supply lines and logistics",
        ],
        "COMBAT PHASE": [
            "Lead troops into battle",
            "Combat a rival warlord one-on-one",
            "Defend the fortress from invasion",
        ],
        "ESPIONAGE PHASE": [
            "Infiltrate enemy headquarters",
            "Gather intelligence on rivals",
            "Execute a covert assassination",
        ],
        "MAGIC PHASE": [
            "Cast a devastating spell",
            "Summon a powerful demon",
            "Break a powerful curse",
        ],
    }

    # Execute campaign
    for phase_name, challenges in campaign.items():
        print(f"\n{phase_name}")
        print("-" * 70)

        for challenge in challenges:
            print(f"\nChallenge: {challenge}")
            result = await arena.battle(challenge, domain=phase_name.split()[0].lower())
            print(f"  Winner: {result.winner}")
            if result.was_challenged and result.verdict:
                margin = (
                    result.verdict.scores.get(result.winner, 0)
                    - max(
                        [
                            v
                            for k, v in result.verdict.scores.items()
                            if k != result.winner
                        ],
                        default=0,
                    )
                )
                print(f"  Victory margin: {margin:.2f}")

    # Final leaderboard
    print("\n" + "=" * 70)
    print("FINAL LEADERBOARD - ALL DOMAINS")
    print("=" * 70 + "\n")

    # Collect all unique domains
    all_domains = set()
    for w in warriors:
        all_domains.update(w.domains)

    for domain in sorted(all_domains):
        print(f"\n{domain.upper()} DOMAIN:")
        leaderboard = arena.get_leaderboard(domain, limit=10)

        for rank, entry in enumerate(leaderboard, 1):
            status = " [WARCHIEF]" if entry["is_warlord"] else ""
            print(
                f"  {rank}. {entry['agent']:15} - "
                f"Rep: {entry['reputation']:.2f}, "
                f"Wins: {entry['wins']:2}, Losses: {entry['losses']:2}{status}"
            )

    # Extract and announce Warchiefs
    print("\n" + "=" * 70)
    print("WARCHIEFS OF THE REALM")
    print("=" * 70 + "\n")

    for domain in sorted(all_domains):
        warchief = arena.get_warchief(domain)
        if warchief:
            print(
                f"  {domain.upper()}: {warchief.name} "
                f"(Reputation: {warchief.reputation:.2f})"
            )

    print("\n" + "=" * 70)
    print("Campaign complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
