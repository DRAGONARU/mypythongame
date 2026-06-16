from src.systems.movement_system import MovementSystem
from src.core.components import Position, Velocity
from src.core.ecs.world import World
import pytest

@pytest.fixture
def components():
    return Position(x=0.0, y=0.0), Velocity(x=1.0, y=1.0)

@pytest.fixture
def world(components):
    world = World()
    e = world.create_entity()
    world.add_component(e, components[0])
    world.add_component(e, components[1])
    return world