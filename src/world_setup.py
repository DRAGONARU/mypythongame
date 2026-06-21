import random
import math
from src.core.ecs.world import World
from src.core.components import (
    Position, Velocity, Collider, Health, Mana, TimeMana, Experience,
    TimeAffected, Player, Enemy, KnifeLoadout, SpellLoadout, CollisionFilter,
    LAYER_PLAYER, LAYER_ENEMY, LAYER_KNIFE, LAYER_PROJECTILE,
)
from config.config_params import (
    PLAYER_RADIUS, PLAYER_HP, PLAYER_MANA, PLAYER_TIME_MANA, PLAYER_XP_TO_NEXT,
    ENEMY_RADIUS, ENEMY_HP, SPAWN_RING_RADIUS,
    KNIFE_REFLECTIVE_BOUNCES, SPELL_KNIVES_COUNT,
)

class ArenaSetup:
    """Factory for creating the player and enemies in a World."""

    PLAYER_RADIUS: float = PLAYER_RADIUS
    PLAYER_HP: int = PLAYER_HP
    PLAYER_MANA: int = PLAYER_MANA
    PLAYER_TIME_MANA: int = PLAYER_TIME_MANA
    PLAYER_XP_TO_NEXT: int = PLAYER_XP_TO_NEXT
    ENEMY_RADIUS: float = ENEMY_RADIUS
    ENEMY_HP: int = ENEMY_HP
    SPAWN_RING_RADIUS: float = SPAWN_RING_RADIUS

    @staticmethod
    def setup(world: World, enemy_count: int = 10, center: tuple[float, float] = (400.0, 300.0)) -> None:
        """Create player at center and enemies in a ring around it.

        Args:
            world: World to populate.
            enemy_count: Number of enemies to spawn.
            center: Player spawn position (x, y).
        """
        ArenaSetup._spawn_player(world, center)
        ArenaSetup._spawn_enemies(world, enemy_count, center)

    @staticmethod
    def _spawn_player(world: World, center: tuple[float, float]) -> None:
        """Create the player entity with all required components."""
        player = world.create_entity()
        world.add_component(player, Position(x=center[0], y=center[1]))
        world.add_component(player, Velocity(x=0.0, y=0.0))
        world.add_component(player, Collider(radius=ArenaSetup.PLAYER_RADIUS))
        world.add_component(player, Health(value=ArenaSetup.PLAYER_HP, max_value=ArenaSetup.PLAYER_HP))
        world.add_component(player, Mana(value=ArenaSetup.PLAYER_MANA, max_value=ArenaSetup.PLAYER_MANA))
        world.add_component(player, TimeMana(value=ArenaSetup.PLAYER_TIME_MANA, max_value=ArenaSetup.PLAYER_TIME_MANA))
        world.add_component(player, Experience(level=1, current=0, to_next=ArenaSetup.PLAYER_XP_TO_NEXT))
        world.add_component(player, TimeAffected(scale=1.0))
        world.add_component(player, Player())
        world.add_component(player, CollisionFilter(layer=LAYER_PLAYER, mask=LAYER_ENEMY | LAYER_PROJECTILE))
        world.add_component(player, KnifeLoadout(current="normal", available=("normal", "delayed", "reflective"), cooldown=0, reflective_bounces=KNIFE_REFLECTIVE_BOUNCES))
        world.add_component(player, SpellLoadout(current="knives", available=("knives", "teleport"), cooldown=0, knives_count=SPELL_KNIVES_COUNT))

    @staticmethod
    def _spawn_enemies(world: World, count: int, center: tuple[float, float]) -> None:
        """Create enemy entities in a ring around the center."""
        for i in range(count):
            angle = 2 * math.pi * i / count
            x = center[0] + ArenaSetup.SPAWN_RING_RADIUS * math.cos(angle)
            y = center[1] + ArenaSetup.SPAWN_RING_RADIUS * math.sin(angle)
            enemy = world.create_entity()
            world.add_component(enemy, Position(x=x, y=y))
            world.add_component(enemy, Velocity(x=0.0, y=0.0))
            world.add_component(enemy, Collider(radius=ArenaSetup.ENEMY_RADIUS))
            world.add_component(enemy, Health(value=ArenaSetup.ENEMY_HP, max_value=ArenaSetup.ENEMY_HP))
            world.add_component(enemy, Enemy())
            world.add_component(enemy, CollisionFilter(layer=LAYER_ENEMY, mask=LAYER_PLAYER | LAYER_KNIFE))
            world.add_component(enemy, TimeAffected(scale=1.0))