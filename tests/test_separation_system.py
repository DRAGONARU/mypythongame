from src.systems.separation_system import SeparationSystem
from src.core.components import Position, Collider, Enemy, Player
from src.core.events import CollisionEvent
from src.core.ecs.world import World
import pytest


@pytest.fixture
def system():
    return SeparationSystem()


@pytest.fixture
def world():
    return World()


def _add_enemy(world, x, y, radius=10.0):
    e = world.create_entity()
    world.add_component(e, Enemy())
    world.add_component(e, Position(x=x, y=y))
    world.add_component(e, Collider(radius=radius))
    return e


# --- basic separation ---


def test_overlapping_enemies_separated(system, world):
    """Two overlapping enemies are pushed apart to touching distance."""
    e1 = _add_enemy(world, 0.0, 0.0)
    e2 = _add_enemy(world, 5.0, 0.0)

    system.update(world)

    p1 = world.get_component(e1, Position)
    p2 = world.get_component(e2, Position)
    dist = ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
    assert dist == pytest.approx(20.0, abs=0.01)


def test_non_overlapping_enemies_untouched(system, world):
    """Enemies already separated keep their positions."""
    e1 = _add_enemy(world, 0.0, 0.0)
    e2 = _add_enemy(world, 100.0, 0.0)

    system.update(world)

    p1 = world.get_component(e1, Position)
    p2 = world.get_component(e2, Position)
    assert p1.x == 0.0
    assert p2.x == 100.0


def test_separation_symmetric(system, world):
    """Both enemies move by half the overlap each."""
    e1 = _add_enemy(world, 0.0, 0.0)
    e2 = _add_enemy(world, 8.0, 0.0)

    system.update(world)

    p1 = world.get_component(e1, Position)
    p2 = world.get_component(e2, Position)
    # overlap = 20 - 8 = 12, push = 6 each
    assert p1.x == pytest.approx(-6.0, abs=0.01)
    assert p2.x == pytest.approx(14.0, abs=0.01)


def test_exact_overlap_uses_default_normal(system, world):
    """Coincident enemies separate along default axis without error."""
    e1 = _add_enemy(world, 0.0, 0.0)
    e2 = _add_enemy(world, 0.0, 0.0)

    system.update(world)

    p1 = world.get_component(e1, Position)
    p2 = world.get_component(e2, Position)
    dist = ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
    assert dist == pytest.approx(20.0, abs=0.01)


def test_diagonal_separation(system, world):
    """Separation along diagonal preserves distance correctly."""
    e1 = _add_enemy(world, 0.0, 0.0)
    e2 = _add_enemy(world, 3.0, 3.0)

    system.update(world)

    p1 = world.get_component(e1, Position)
    p2 = world.get_component(e2, Position)
    dist = ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
    assert dist == pytest.approx(20.0, abs=0.01)


# --- non-enemies ignored ---


def test_player_not_separated(system, world):
    """Player-enemy overlap does not trigger separation."""
    pe = world.create_entity()
    world.add_component(pe, Player())
    world.add_component(pe, Position(x=0.0, y=0.0))
    world.add_component(pe, Collider(radius=12.0))
    e2 = _add_enemy(world, 5.0, 0.0)

    system.update(world)

    assert world.get_component(pe, Position).x == 0.0
    assert world.get_component(e2, Position).x == 5.0


def test_no_collision_events_generated(system, world):
    """Separation must not produce CollisionEvents."""
    _add_enemy(world, 0.0, 0.0)
    _add_enemy(world, 5.0, 0.0)

    system.update(world)

    assert world.events == []


# --- multiple enemies ---


def test_three_enemies_cluster_spread(system, world):
    """A cluster of three enemies spreads out without overlap."""
    e1 = _add_enemy(world, 0.0, 0.0)
    e2 = _add_enemy(world, 4.0, 0.0)
    e3 = _add_enemy(world, 2.0, 3.0)

    for _ in range(10):
        system.update(world)

    for a, b in [(e1, e2), (e1, e3), (e2, e3)]:
        pa = world.get_component(a, Position)
        pb = world.get_component(b, Position)
        dist = ((pa.x - pb.x) ** 2 + (pa.y - pb.y) ** 2) ** 0.5
        assert dist >= 20.0 - 0.5


def test_pair_processed_once(system, world):
    """Each overlapping pair is resolved exactly once (id ordering)."""
    e1 = _add_enemy(world, 0.0, 0.0)
    e2 = _add_enemy(world, 5.0, 0.0)
    before1 = world.get_component(e1, Position).x
    before2 = world.get_component(e2, Position).x

    system.update(world)

    after1 = world.get_component(e1, Position).x
    after2 = world.get_component(e2, Position).x
    assert after1 != before1
    assert after2 != before2


# --- edge cases ---


def test_single_enemy_no_crash(system, world):
    _add_enemy(world, 0.0, 0.0)
    system.update(world)


def test_empty_world(system, world):
    system.update(world)


def test_enemy_without_collider_skipped(system, world):
    """Enemy missing Collider is ignored, not crashed on."""
    e1 = _add_enemy(world, 0.0, 0.0)
    e2 = world.create_entity()
    world.add_component(e2, Enemy())
    world.add_component(e2, Position(x=0.0, y=0.0))

    system.update(world)

    assert world.get_component(e1, Position).x == 0.0
