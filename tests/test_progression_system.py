from src.systems.progression_system import ProgressionSystem
from src.core.components import (
    Player, Enemy, Health, Position, Experience, Mana, TimeMana,
    KnifeLoadout, SpellLoadout, XPOrb, Collider,
)
from src.core.ecs.world import World
from config.config_params import (
    XP_ORB_VALUE, XP_PICKUP_RADIUS, XP_GROWTH,
    UPGRADE_HP, UPGRADE_MANA, UPGRADE_TIMEMANA, UPGRADE_BOUNCES, UPGRADE_KNIVES,
)
import pytest


@pytest.fixture
def system():
    return ProgressionSystem()


@pytest.fixture
def world():
    return World()


def _add_player(world, to_next=100, xp=0):
    e = world.create_entity()
    world.add_component(e, Player())
    world.add_component(e, Position(x=400.0, y=300.0))
    world.add_component(e, Health(value=100, max_value=100))
    world.add_component(e, Mana(value=100, max_value=100))
    world.add_component(e, TimeMana(value=500, max_value=500))
    world.add_component(e, Experience(level=1, current=xp, to_next=to_next))
    world.add_component(e, KnifeLoadout(current="reflective", reflective_bounces=3))
    world.add_component(e, SpellLoadout(current="knives", knives_count=16))
    return e


def _add_enemy(world, x, y, hp=0):
    e = world.create_entity()
    world.add_component(e, Enemy())
    world.add_component(e, Position(x=x, y=y))
    world.add_component(e, Health(value=hp, max_value=50))
    return e


# --- orb drops ---


def test_dead_enemy_drops_orb(system, world):
    """An enemy with Health <= 0 drops an XP orb at its position."""
    _add_enemy(world, 100.0, 200.0, hp=0)
    system.update(world)
    orbs = list(world.query(XPOrb, Position))
    assert len(orbs) == 1
    _, orb, pos = orbs[0]
    assert orb.value == XP_ORB_VALUE
    assert pos.x == 100.0
    assert pos.y == 200.0


def test_alive_enemy_drops_no_orb(system, world):
    """An enemy with Health > 0 drops nothing."""
    _add_enemy(world, 100.0, 200.0, hp=50)
    system.update(world)
    assert len(list(world.query(XPOrb))) == 0


def test_orb_has_collider(system, world):
    """Dropped orbs carry a Collider for rendering."""
    _add_enemy(world, 0.0, 0.0, hp=0)
    system.update(world)
    for entity, orb, col in world.query(XPOrb, Collider):
        assert col.radius > 0
        return
    pytest.fail("orb missing Collider")


# --- pickup ---


def test_orb_picked_up_within_radius(system, world):
    """An orb within pickup radius is collected and destroyed."""
    _add_player(world)
    orb = world.create_entity()
    world.add_component(orb, Position(x=410.0, y=300.0))
    world.add_component(orb, Collider(radius=5.0))
    world.add_component(orb, XPOrb(value=XP_ORB_VALUE))
    system.update(world)
    assert len(list(world.query(XPOrb))) == 0


def test_orb_outside_radius_not_picked(system, world):
    """An orb beyond pickup radius stays in the world."""
    _add_player(world)
    orb = world.create_entity()
    world.add_component(orb, Position(x=400.0 + XP_PICKUP_RADIUS + 10, y=300.0))
    world.add_component(orb, Collider(radius=5.0))
    world.add_component(orb, XPOrb(value=XP_ORB_VALUE))
    system.update(world)
    assert len(list(world.query(XPOrb))) == 1


def test_pickup_adds_xp(system, world):
    """Collecting an orb adds its value to the player's Experience."""
    _add_player(world, xp=0)
    orb = world.create_entity()
    world.add_component(orb, Position(x=400.0, y=300.0))
    world.add_component(orb, Collider(radius=5.0))
    world.add_component(orb, XPOrb(value=XP_ORB_VALUE))
    system.update(world)
    for entity, player, xp in world.query(Player, Experience):
        assert xp.current == XP_ORB_VALUE
        return
    pytest.fail("player not found")


# --- level up ---


def test_level_up_increments_level(system, world):
    """Crossing the XP threshold increments the level."""
    _add_player(world, to_next=10, xp=10)
    system.update(world)
    for entity, player, xp in world.query(Player, Experience):
        assert xp.level == 2


def test_level_up_resets_current(system, world):
    """Excess XP carries over after a level-up."""
    _add_player(world, to_next=10, xp=12)
    system.update(world)
    for entity, player, xp in world.query(Player, Experience):
        assert xp.current == 2


def test_level_up_grows_threshold(system, world):
    """The next threshold scales by XP_GROWTH on level-up."""
    _add_player(world, to_next=100, xp=100)
    system.update(world)
    for entity, player, xp in world.query(Player, Experience):
        assert xp.to_next == int(100 * XP_GROWTH)


def test_multiple_level_ups_in_one_tick(system, world):
    """Enough XP for several levels applies them all at once.

    to_next=10, xp=50: L1 (->40, thr 15), L2 (->25, thr 22),
    L3 (->3, thr 33); stops at 3 levels, current=3.
    """
    _add_player(world, to_next=10, xp=50)
    system.update(world)
    for entity, player, xp in world.query(Player, Experience):
        assert xp.level == 1 + 3
        assert xp.current == 3


def test_upgrade_applied_once_per_level(system, world, monkeypatch):
    """Each level-up applies exactly one upgrade."""
    _add_player(world, to_next=10, xp=50)
    calls = []
    original = system._apply_random_upgrade
    def spy(*a, **k):
        calls.append(1)
        original(*a, **k)
    monkeypatch.setattr(system, "_apply_random_upgrade", spy)
    system.update(world)
    assert len(calls) == 3


def test_upgrade_max_hp(system, world, monkeypatch):
    """The max-hp upgrade raises max and current Health."""
    _add_player(world, to_next=10, xp=10)
    monkeypatch.setattr(system, "_apply_random_upgrade",
                        lambda *a: system._upgrade_max_hp(*a))
    system.update(world)
    for entity, player, health in world.query(Player, Health):
        assert health.max_value == 100 + UPGRADE_HP
        assert health.value == 100 + UPGRADE_HP
        return
    pytest.fail("player not found")


def test_upgrade_max_mana(system, world, monkeypatch):
    _add_player(world, to_next=10, xp=10)
    monkeypatch.setattr(system, "_apply_random_upgrade",
                        lambda *a: system._upgrade_max_mana(*a))
    system.update(world)
    for entity, player, mana in world.query(Player, Mana):
        assert mana.max_value == 100 + UPGRADE_MANA


def test_upgrade_max_time_mana(system, world, monkeypatch):
    _add_player(world, to_next=10, xp=10)
    monkeypatch.setattr(system, "_apply_random_upgrade",
                        lambda *a: system._upgrade_max_time_mana(*a))
    system.update(world)
    for entity, player, tm in world.query(Player, TimeMana):
        assert tm.max_value == 500 + UPGRADE_TIMEMANA


def test_upgrade_bounces(system, world, monkeypatch):
    """The bounces upgrade raises KnifeLoadout.reflective_bounces."""
    player = _add_player(world, to_next=10, xp=10)
    monkeypatch.setattr(system, "_apply_random_upgrade",
                        lambda *a: system._upgrade_bounces(*a))
    system.update(world)
    loadout = world.get_component(player, KnifeLoadout)
    assert loadout.reflective_bounces == 3 + UPGRADE_BOUNCES


def test_upgrade_knives(system, world, monkeypatch):
    """The knives upgrade raises SpellLoadout.knives_count."""
    player = _add_player(world, to_next=10, xp=10)
    monkeypatch.setattr(system, "_apply_random_upgrade",
                        lambda *a: system._upgrade_knives(*a))
    system.update(world)
    loadout = world.get_component(player, SpellLoadout)
    assert loadout.knives_count == 16 + UPGRADE_KNIVES


# --- integration: drop then pickup ---


def test_drop_then_pickup_grants_xp(system, world):
    """A dead enemy's orb is picked up by the nearby player next tick."""
    _add_player(world, xp=0)
    _add_enemy(world, 400.0, 300.0, hp=0)
    system.update(world)
    orbs = list(world.query(XPOrb))
    assert len(orbs) == 0
    for entity, player, xp in world.query(Player, Experience):
        assert xp.current == XP_ORB_VALUE


# --- no player ---


def test_no_player_no_crash(system, world):
    """Missing player does not raise."""
    _add_enemy(world, 0.0, 0.0, hp=0)
    system.update(world)
    assert len(list(world.query(XPOrb))) == 1
