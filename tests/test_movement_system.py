from src.systems.movement_system import MovementSystem
from src.core.components import Position, Velocity, TimeAffected
from src.core.ecs.world import World
import pytest


@pytest.fixture
def system():
    return MovementSystem()


@pytest.fixture
def world():
    return World()


def test_movement_basic(system, world):
    """Entity moves according to velocity."""
    e = world.create_entity()
    pos = Position(x=0.0, y=0.0)
    vel = Velocity(x=1.0, y=2.0)
    time = TimeAffected(scale=1.0)
    world.add_component(e, pos)
    world.add_component(e, vel)
    world.add_component(e, time)
    
    system.update(world)
    
    assert pos.x == 1.0
    assert pos.y == 2.0


def test_movement_with_timescale(system, world):
    """Velocity is multiplied by timescale."""
    e = world.create_entity()
    pos = Position(x=0.0, y=0.0)
    vel = Velocity(x=10.0, y=10.0)
    time = TimeAffected(scale=0.5)
    world.add_component(e, pos)
    world.add_component(e, vel)
    world.add_component(e, time)
    
    system.update(world)
    
    assert pos.x == 5.0
    assert pos.y == 5.0


def test_movement_time_stopped(system, world):
    """Entity doesn't move when timescale is 0."""
    e = world.create_entity()
    pos = Position(x=0.0, y=0.0)
    vel = Velocity(x=10.0, y=10.0)
    time = TimeAffected(scale=0.0)
    world.add_component(e, pos)
    world.add_component(e, vel)
    world.add_component(e, time)
    
    system.update(world)
    
    assert pos.x == 0.0
    assert pos.y == 0.0


def test_movement_multiple_entities(system, world):
    """Multiple entities move independently."""
    e1 = world.create_entity()
    e2 = world.create_entity()
    
    pos1 = Position(x=0.0, y=0.0)
    vel1 = Velocity(x=1.0, y=1.0)
    time1 = TimeAffected(scale=1.0)
    
    pos2 = Position(x=100.0, y=100.0)
    vel2 = Velocity(x=2.0, y=2.0)
    time2 = TimeAffected(scale=1.0)
    
    world.add_component(e1, pos1)
    world.add_component(e1, vel1)
    world.add_component(e1, time1)
    world.add_component(e2, pos2)
    world.add_component(e2, vel2)
    world.add_component(e2, time2)
    
    system.update(world)
    
    assert pos1.x == 1.0
    assert pos1.y == 1.0
    assert pos2.x == 102.0
    assert pos2.y == 102.0


def test_movement_no_velocity_component(system, world):
    """Entity without Velocity doesn't move."""
    e = world.create_entity()
    pos = Position(x=5.0, y=5.0)
    time = TimeAffected(scale=1.0)
    world.add_component(e, pos)
    world.add_component(e, time)
    
    system.update(world)
    
    assert pos.x == 5.0
    assert pos.y == 5.0


def test_movement_empty_world(system, world):
    """System handles empty world gracefully."""
    system.update(world)


def test_movement_multiple_ticks(system, world):
    """Position accumulates over multiple ticks."""
    e = world.create_entity()
    pos = Position(x=0.0, y=0.0)
    vel = Velocity(x=1.0, y=1.0)
    time = TimeAffected(scale=1.0)
    world.add_component(e, pos)
    world.add_component(e, vel)
    world.add_component(e, time)
    
    system.update(world)
    system.update(world)
    system.update(world)
    
    assert pos.x == 3.0
    assert pos.y == 3.0