"""ORC Themed API - Fun wrapper around the standard Arena.

This module provides themed classes for a more engaging ORC experience:
- Warrior: An agent that fights in the Arena
- Elder: A judge that evaluates trials
- Warchief: The victorious warrior granted command
- TheArena: The stage where warriors compete
"""

from orc.themed.elder import Elder
from orc.themed.the_arena import TheArena
from orc.themed.warchief import Warchief
from orc.themed.warrior import Warrior

__all__ = ["Warrior", "Elder", "Warchief", "TheArena"]
