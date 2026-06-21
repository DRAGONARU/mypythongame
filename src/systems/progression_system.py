import random
from src.core.ecs.system import System
from src.core.components import (
    Player, Enemy, Health, Position, Experience, Mana, TimeMana,
    KnifeLoadout, SpellLoadout, XPOrb, Collider,
)
from config.config_params import (
    XP_ORB_VALUE, XP_ORB_RADIUS, XP_PICKUP_RADIUS, XP_GROWTH,
    UPGRADE_HP, UPGRADE_MANA, UPGRADE_TIMEMANA, UPGRADE_BOUNCES, UPGRADE_KNIVES,
)


class ProgressionSystem(System):
    """Handles XP orb drops, pickup and random stat upgrades on level-up.

    Each tick the system:
      * spawns an XP orb at every dead enemy's position (Health <= 0),
        before EnemySystem destroys the corpse;
      * collects orbs within pickup radius of the player, adding their
        value to the player's Experience component;
      * on level-up (current >= to_next) applies one random upgrade from
        a fixed pool and raises the next threshold.
    """

    def __init__(self):
        self._orb_value: int = XP_ORB_VALUE
        self._orb_radius: float = XP_ORB_RADIUS
        self._pickup_radius: float = XP_PICKUP_RADIUS
        self._growth: float = XP_GROWTH

    def update(self, world) -> None:
        self._drop_orbs(world)
        self._pickup_orbs(world)
        self._check_level_up(world)

    def _drop_orbs(self, world) -> None:
        """Spawn an XP orb at each dead enemy's position."""
        for entity, enemy, health, pos in world.query(Enemy, Health, Position):
            if health.value <= 0:
                orb = world.create_entity()
                world.add_component(orb, Position(x=pos.x, y=pos.y))
                world.add_component(orb, Collider(radius=self._orb_radius))
                world.add_component(orb, XPOrb(value=self._orb_value))

    def _pickup_orbs(self, world) -> None:
        """Collect orbs within pickup radius of the player."""
        player_pos = self._find_player_pos(world)
        if player_pos is None:
            return
        collected = []
        r2 = self._pickup_radius * self._pickup_radius
        for entity, orb, pos in world.query(XPOrb, Position):
            dx = player_pos.x - pos.x
            dy = player_pos.y - pos.y
            if dx * dx + dy * dy <= r2:
                collected.append((entity, orb.value))
        if not collected:
            return
        xp = self._find_xp(world)
        for entity, value in collected:
            world.destroy_entity(entity)
            if xp is not None:
                xp.current += value

    def _check_level_up(self, world) -> None:
        """Apply a random upgrade each time XP crosses the threshold."""
        for entity, player, xp, health, mana, time_mana in world.query(
            Player, Experience, Health, Mana, TimeMana
        ):
            knife_loadout = world.get_component(entity, KnifeLoadout)
            spell_loadout = world.get_component(entity, SpellLoadout)
            while xp.current >= xp.to_next:
                xp.current -= xp.to_next
                xp.level += 1
                xp.to_next = int(xp.to_next * self._growth)
                self._apply_random_upgrade(
                    health, mana, time_mana, knife_loadout, spell_loadout
                )

    def _apply_random_upgrade(self, health, mana, time_mana, knife_loadout, spell_loadout) -> None:
        """Apply one random stat upgrade from the fixed pool."""
        upgrade = random.choice(self._upgrade_pool(knife_loadout, spell_loadout))
        upgrade(health, mana, time_mana, knife_loadout, spell_loadout)

    def _upgrade_pool(self, knife_loadout, spell_loadout):
        """Return the list of available upgrade callables."""
        return [
            self._upgrade_max_hp,
            self._upgrade_max_mana,
            self._upgrade_max_time_mana,
            self._upgrade_bounces,
            self._upgrade_knives,
        ]

    def _upgrade_max_hp(self, health, mana, time_mana, knife_loadout, spell_loadout) -> None:
        health.max_value += UPGRADE_HP
        health.value += UPGRADE_HP

    def _upgrade_max_mana(self, health, mana, time_mana, knife_loadout, spell_loadout) -> None:
        mana.max_value += UPGRADE_MANA
        mana.value += UPGRADE_MANA

    def _upgrade_max_time_mana(self, health, mana, time_mana, knife_loadout, spell_loadout) -> None:
        time_mana.max_value += UPGRADE_TIMEMANA
        time_mana.value += UPGRADE_TIMEMANA

    def _upgrade_bounces(self, health, mana, time_mana, knife_loadout, spell_loadout) -> None:
        if knife_loadout is not None:
            knife_loadout.reflective_bounces += UPGRADE_BOUNCES

    def _upgrade_knives(self, health, mana, time_mana, knife_loadout, spell_loadout) -> None:
        if spell_loadout is not None:
            spell_loadout.knives_count += UPGRADE_KNIVES

    @staticmethod
    def _find_player_pos(world) -> Position | None:
        for entity, player, pos in world.query(Player, Position):
            return pos
        return None

    @staticmethod
    def _find_xp(world) -> Experience | None:
        for entity, player, xp in world.query(Player, Experience):
            return xp
        return None
