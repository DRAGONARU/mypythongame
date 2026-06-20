from src.systems.enemy_system import EnemySystem
from src.core.components import Position, Velocity, Enemy, Health, Player
from src.core.ecs.world import World
import pytest


@pytest.fixture
def system():
    return EnemySystem()


@pytest.fixture
def world():
    return World()


def _spawn_player(world, x=0.0, y=0.0):
    e = world.create_entity()
    world.add_component(e, Position(x=x, y=y))
    world.add_component(e, Player())
    return e


def _spawn_enemy(world, x, y, hp=10):
    e = world.create_entity()
    world.add_component(e, Position(x=x, y=y))
    world.add_component(e, Enemy())
    world.add_component(e, Health(value=hp, max_value=hp))
    return e


# --- movement ---


def test_no_player_no_crash(system, world):
    """Enemy system handles missing player gracefully."""
    e = _spawn_enemy(world, 50.0, 0.0)
    system.update(world)
    assert world.get_component(e, Velocity) is None


def test_enemy_moves_towards_player(system, world):
    """Enemy gains velocity pointing at the player."""
    _spawn_player(world, 100.0, 0.0)
    e = _spawn_enemy(world, 0.0, 0.0)

    system.update(world)

    vel = world.get_component(e, Velocity)
    assert vel is not None
    assert vel.x == pytest.approx(EnemySystem.ENEMY_SPEED)
    assert vel.y == pytest.approx(0.0)


def test_enemy_moves_left_when_player_on_left(system, world):
    """Velocity x is negative when player is to the left."""
    _spawn_player(world, -100.0, 0.0)
    e = _spawn_enemy(world, 0.0, 0.0)

    system.update(world)

    vel = world.get_component(e, Velocity)
    assert vel.x == pytest.approx(-EnemySystem.ENEMY_SPEED)
    assert vel.y == pytest.approx(0.0)


def test_enemy_moves_up_when_player_above(system, world):
    """Velocity y is negative when player is above."""
    _spawn_player(world, 0.0, -100.0)
    e = _spawn_enemy(world, 0.0, 0.0)

    system.update(world)

    vel = world.get_component(e, Velocity)
    assert vel.x == pytest.approx(0.0)
    assert vel.y == pytest.approx(-EnemySystem.ENEMY_SPEED)


def test_enemy_speed_normalized(system, world):
    """Velocity magnitude equals ENEMY_SPEED regardless of distance."""
    _spawn_player(world, 30.0, 40.0)
    e = _spawn_enemy(world, 0.0, 0.0)

    system.update(world)

    vel = world.get_component(e, Velocity)
    mag = (vel.x ** 2 + vel.y ** 2) ** 0.5
    assert mag == pytest.approx(EnemySystem.ENEMY_SPEED)


def test_enemy_on_player_no_division_by_zero(system, world):
    """Zero distance does not raise."""
    _spawn_player(world, 0.0, 0.0)
    e = _spawn_enemy(world, 0.0, 0.0)

    system.update(world)

    vel = world.get_component(e, Velocity)
    assert vel is not None


def test_multiple_enemies_all_target_player(system, world):
    """Every enemy receives velocity towards the player."""
    _spawn_player(world, 100.0, 0.0)
    e1 = _spawn_enemy(world, 0.0, 0.0)
    e2 = _spawn_enemy(world, 0.0, 100.0)
    e3 = _spawn_enemy(world, -50.0, -50.0)

    system.update(world)

    for e in (e1, e2, e3):
        vel = world.get_component(e, Velocity)
        assert vel is not None
        dx = 100.0 - world.get_component(e, Position).x
        dy = 0.0 - world.get_component(e, Position).y
        dist = (dx * dx + dy * dy) ** 0.5
        assert vel.x == pytest.approx((dx / dist) * EnemySystem.ENEMY_SPEED)
        assert vel.y == pytest.approx((dy / dist) * EnemySystem.ENEMY_SPEED)


def test_velocity_updated_in_place(system, world):
    """Existing Velocity component is mutated, not replaced."""
    _spawn_player(world, 100.0, 0.0)
    e = _spawn_enemy(world, 0.0, 0.0)
    world.add_component(e, Velocity(x=999.0, y=999.0))
    original = world.get_component(e, Velocity)

    system.update(world)

    updated = world.get_component(e, Velocity)
    assert updated is original
    assert updated.x == pytest.approx(EnemySystem.ENEMY_SPEED)
    assert updated.y == pytest.approx(0.0)


def test_velocity_recomputed_each_tick(system, world):
    """Velocity follows the player as it conceptually moves."""
    player = _spawn_player(world, 100.0, 0.0)
    e = _spawn_enemy(world, 0.0, 0.0)

    system.update(world)
    assert world.get_component(e, Velocity).x > 0

    world.get_component(player, Position).x = -100.0
    system.update(world)
    assert world.get_component(e, Velocity).x < 0


# --- death ---


def test_enemy_destroyed_on_zero_health(system, world):
    """Enemy with health <= 0 is removed."""
    _spawn_player(world, 0.0, 0.0)
    e = _spawn_enemy(world, 10.0, 0.0, hp=0)

    system.update(world)

    assert not world._is_alive(e)


def test_enemy_destroyed_on_negative_health(system, world):
    """Enemy with negative health is removed."""
    _spawn_player(world, 0.0, 0.0)
    e = _spawn_enemy(world, 10.0, 0.0, hp=-5)

    system.update(world)

    assert not world._is_alive(e)


def test_alive_enemy_not_destroyed(system, world):
    """Enemy with positive health survives."""
    _spawn_player(world, 0.0, 0.0)
    e = _spawn_enemy(world, 10.0, 0.0, hp=50)

    system.update(world)

    assert world._is_alive(e)


def test_multiple_dead_enemies_all_removed(system, world):
    """All dead enemies removed without index errors."""
    _spawn_player(world, 0.0, 0.0)
    dead = [_spawn_enemy(world, float(i), 0.0, hp=0) for i in range(5)]
    alive = [_spawn_enemy(world, float(i), 50.0, hp=10) for i in range(5)]

    system.update(world)

    for e in dead:
        assert not world._is_alive(e)
    for e in alive:
        assert world._is_alive(e)


def test_dead_enemy_without_player_removed(system, world):
    """Death check runs even when no player exists."""
    e = _spawn_enemy(world, 0.0, 0.0, hp=0)

    system.update(world)

    assert not world._is_alive(e)


# --- empty / edge ---


def test_empty_world(system, world):
    """System handles empty world gracefully."""
    system.update(world)


def test_player_without_enemies(system, world):
    """System handles player but no enemies."""
    _spawn_player(world, 50.0, 50.0)
    system.update(world)
