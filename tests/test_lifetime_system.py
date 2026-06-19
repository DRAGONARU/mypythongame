from src.systems.lifetime_system import LifetimeSystem
from src.core.components import Lifetime, Position
from src.core.ecs.world import World
import pytest


@pytest.fixture
def system():
    return LifetimeSystem()


@pytest.fixture
def world():
    return World()


def test_lifetime_empty_world(system, world):
    """System handles empty world gracefully."""
    system.update(world)


def test_lifetime_no_destruction(system, world):
    """Entity with large lifetime is not destroyed."""
    e = world.create_entity()
    world.add_component(e, Lifetime(remaining_ticks=100))

    system.update(world)

    assert world._is_alive(e)
    assert world.get_component(e, Lifetime).remaining_ticks == 99


def test_lifetime_destroyed_after_one_tick(system, world):
    """Entity with remaining_ticks=1 is destroyed after one update."""
    e = world.create_entity()
    world.add_component(e, Lifetime(remaining_ticks=1))

    system.update(world)

    assert not world._is_alive(e)


def test_lifetime_destroyed_at_zero(system, world):
    """Entity with remaining_ticks=0 is destroyed after one update."""
    e = world.create_entity()
    world.add_component(e, Lifetime(remaining_ticks=0))

    system.update(world)

    assert not world._is_alive(e)


def test_lifetime_multiple_ticks(system, world):
    """Entity survives until remaining_ticks reaches 0."""
    e = world.create_entity()
    world.add_component(e, Lifetime(remaining_ticks=3))

    system.update(world)
    assert world._is_alive(e)
    assert world.get_component(e, Lifetime).remaining_ticks == 2

    system.update(world)
    assert world._is_alive(e)
    assert world.get_component(e, Lifetime).remaining_ticks == 1

    system.update(world)
    assert not world._is_alive(e)


def test_lifetime_multiple_entities(system, world):
    """Only entities with expired lifetime are destroyed."""
    e1 = world.create_entity()
    e2 = world.create_entity()
    e3 = world.create_entity()
    world.add_component(e1, Lifetime(remaining_ticks=1))
    world.add_component(e2, Lifetime(remaining_ticks=5))
    world.add_component(e3, Lifetime(remaining_ticks=1))

    system.update(world)

    assert not world._is_alive(e1)
    assert world._is_alive(e2)
    assert not world._is_alive(e3)


def test_lifetime_entity_without_lifetime_ignored(system, world):
    """Entity without Lifetime component is not affected."""
    e = world.create_entity()
    world.add_component(e, Position(x=0.0, y=0.0))

    system.update(world)

    assert world._is_alive(e)


def test_lifetime_decrements_each_tick(system, world):
    """remaining_ticks decrements by 1 each update."""
    e = world.create_entity()
    world.add_component(e, Lifetime(remaining_ticks=10))

    for expected in range(9, -1, -1):
        system.update(world)
        if world._is_alive(e):
            assert world.get_component(e, Lifetime).remaining_ticks == expected

    assert not world._is_alive(e)
