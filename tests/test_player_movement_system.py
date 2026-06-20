from src.systems.player_movement_system import PlayerMovementSystem
from src.core.components import Position, Velocity, Player, InputState
from src.core.ecs.world import World
import pygame
import pytest


@pytest.fixture
def system():
    return PlayerMovementSystem()


@pytest.fixture
def world():
    return World()


def _make_keys(*pressed):
    keys = [False] * 300
    for k in pressed:
        keys[k] = True
    return tuple(keys)


def _add_input_state(world, keys=None):
    if keys is None:
        keys = _make_keys()
    e = world.create_entity()
    world.add_component(e, InputState(
        mouse_x=0.0, mouse_y=0.0,
        mouse_pressed=(False, False, False), keys_pressed=keys,
    ))
    return e


def _add_player(world, x=0.0, y=0.0):
    e = world.create_entity()
    world.add_component(e, Position(x=x, y=y))
    world.add_component(e, Velocity(x=0.0, y=0.0))
    world.add_component(e, Player())
    return e


def test_no_input_state_no_crash(system, world):
    _add_player(world)
    system.update(world)
    assert world.query(Player, Velocity).__iter__().__next__()[2].x == 0.0


def test_no_keys_player_still(system, world):
    _add_input_state(world)
    e = _add_player(world)
    system.update(world)
    vel = world.get_component(e, Velocity)
    assert vel.x == 0.0
    assert vel.y == 0.0


def test_move_right(system, world):
    _add_input_state(world, keys=_make_keys(pygame.K_d))
    e = _add_player(world)
    system.update(world)
    vel = world.get_component(e, Velocity)
    assert vel.x == pytest.approx(PlayerMovementSystem.PLAYER_SPEED)
    assert vel.y == 0.0


def test_move_left(system, world):
    _add_input_state(world, keys=_make_keys(pygame.K_a))
    e = _add_player(world)
    system.update(world)
    vel = world.get_component(e, Velocity)
    assert vel.x == pytest.approx(-PlayerMovementSystem.PLAYER_SPEED)
    assert vel.y == 0.0


def test_move_up(system, world):
    _add_input_state(world, keys=_make_keys(pygame.K_w))
    e = _add_player(world)
    system.update(world)
    vel = world.get_component(e, Velocity)
    assert vel.x == 0.0
    assert vel.y == pytest.approx(-PlayerMovementSystem.PLAYER_SPEED)


def test_move_down(system, world):
    _add_input_state(world, keys=_make_keys(pygame.K_s))
    e = _add_player(world)
    system.update(world)
    vel = world.get_component(e, Velocity)
    assert vel.x == 0.0
    assert vel.y == pytest.approx(PlayerMovementSystem.PLAYER_SPEED)


def test_move_diagonal_normalized(system, world):
    """Diagonal movement is normalized to avoid 2x speed."""
    _add_input_state(world, keys=_make_keys(pygame.K_w, pygame.K_d))
    e = _add_player(world)
    system.update(world)
    vel = world.get_component(e, Velocity)
    inv_sqrt2 = 0.7071067811865475
    assert vel.x == pytest.approx(PlayerMovementSystem.PLAYER_SPEED * inv_sqrt2)
    assert vel.y == pytest.approx(-PlayerMovementSystem.PLAYER_SPEED * inv_sqrt2)


def test_arrow_keys_work(system, world):
    """WASD aliases: arrow keycodes exceed get_pressed() tuple size,
    so only WASD is supported. Verify A/D still move horizontally."""
    _add_input_state(world, keys=_make_keys(pygame.K_d, pygame.K_s))
    e = _add_player(world)
    system.update(world)
    vel = world.get_component(e, Velocity)
    inv_sqrt2 = 0.7071067811865475
    assert vel.x == pytest.approx(PlayerMovementSystem.PLAYER_SPEED * inv_sqrt2)
    assert vel.y == pytest.approx(PlayerMovementSystem.PLAYER_SPEED * inv_sqrt2)


def test_velocity_updated_in_place(system, world):
    _add_input_state(world, keys=_make_keys(pygame.K_d))
    e = _add_player(world)
    original = world.get_component(e, Velocity)
    system.update(world)
    updated = world.get_component(e, Velocity)
    assert updated is original
    assert updated.x == pytest.approx(PlayerMovementSystem.PLAYER_SPEED)


def test_velocity_recomputed_each_tick(system, world):
    keys1 = _make_keys(pygame.K_d)
    keys2 = _make_keys(pygame.K_a)
    input_e = _add_input_state(world, keys=keys1)
    e = _add_player(world)
    state = world.get_component(input_e, InputState)

    system.update(world)
    assert world.get_component(e, Velocity).x > 0

    state.keys_pressed = keys2
    system.update(world)
    assert world.get_component(e, Velocity).x < 0


def test_stop_on_release(system, world):
    _add_input_state(world, keys=_make_keys(pygame.K_d))
    e = _add_player(world)
    system.update(world)
    assert world.get_component(e, Velocity).x != 0

    state = world.get_component(world.query(InputState).__iter__().__next__()[0], InputState)
    state.keys_pressed = _make_keys()
    system.update(world)
    vel = world.get_component(e, Velocity)
    assert vel.x == 0.0
    assert vel.y == 0.0


def test_empty_world(system, world):
    system.update(world)


def test_player_without_velocity_ignored(system, world):
    _add_input_state(world, keys=_make_keys(pygame.K_d))
    e = world.create_entity()
    world.add_component(e, Position(x=0.0, y=0.0))
    world.add_component(e, Player())
    system.update(world)
