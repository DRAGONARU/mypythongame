from src.systems.collision_system import CollisionSystem
from src.core.components import Position, Collider
from src.core.ecs.world import World
import pytest


@pytest.fixture
def system():
    return CollisionSystem(cell_size=64.0)


@pytest.fixture
def world():
    return World()


def _add_entity(world, x, y, radius):
    e = world.create_entity()
    world.add_component(e, Position(x=x, y=y))
    if radius is not None:
        world.add_component(e, Collider(radius=radius))
    return e


def test_collision_empty_world(system, world):
    """System handles empty world gracefully."""
    system.update(world)


def test_collision_no_overlap(system, world):
    """Entities far apart don't collide."""
    _add_entity(world, 0.0, 0.0, 10.0)
    _add_entity(world, 500.0, 500.0, 10.0)

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert calls == []


def test_collision_overlap_detected(system, world):
    """Overlapping entities trigger collision."""
    _add_entity(world, 0.0, 0.0, 15.0)
    _add_entity(world, 20.0, 0.0, 15.0)

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert len(calls) == 1


def test_collision_no_duplicate_pairs(system, world):
    """Each pair is checked only once."""
    _add_entity(world, 0.0, 0.0, 20.0)
    _add_entity(world, 10.0, 0.0, 20.0)

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert len(calls) == 1


def test_collision_just_touching(system, world):
    """Entities touching at exact boundary count as collision."""
    _add_entity(world, 0.0, 0.0, 10.0)
    _add_entity(world, 20.0, 0.0, 10.0)

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert len(calls) == 1


def test_collision_just_apart(system, world):
    """Entities just outside boundary don't collide."""
    _add_entity(world, 0.0, 0.0, 10.0)
    _add_entity(world, 20.001, 0.0, 10.0)

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert calls == []


def test_collision_multiple_entities(system, world):
    """Multiple overlapping entities generate correct pairs."""
    _add_entity(world, 0.0, 0.0, 20.0)
    _add_entity(world, 10.0, 0.0, 20.0)
    _add_entity(world, 5.0, 5.0, 20.0)

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert len(calls) == 3


def test_collision_entity_without_collider_ignored(system, world):
    """Entity without Collider is ignored."""
    _add_entity(world, 0.0, 0.0, 10.0)
    _add_entity(world, 1.0, 0.0, None)

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert calls == []


def test_collision_entity_without_position_ignored(system, world):
    """Entity without Position is ignored."""
    _add_entity(world, 0.0, 0.0, 10.0)
    e2 = world.create_entity()
    world.add_component(e2, Collider(radius=10.0))

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert calls == []
