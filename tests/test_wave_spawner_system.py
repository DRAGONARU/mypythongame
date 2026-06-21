from src.systems.wave_spawner_system import WaveSpawner
from src.core.components import Enemy, Health, Position
from src.core.ecs.world import World
import pytest


@pytest.fixture
def world():
    return World()


def _make_spawner(count=5, cooldown=3, max_enemies=10, screen=(800, 600)):
    spawner = WaveSpawner(screen)
    spawner._spawn_count = count
    spawner._cooldown = cooldown
    spawner._max_enemies = max_enemies
    return spawner


# --- basic spawning ---


def test_first_pulse_spawns_immediately(world):
    """The first pulse fires on the first update (no initial wait)."""
    spawner = _make_spawner(count=5, cooldown=3, max_enemies=10)
    spawner.update(world)
    assert spawner.total_spawned == 5
    assert len(list(world.query(Enemy))) == 5


def test_cooldown_delays_next_pulse(world):
    """Pulses only fire once the cooldown has elapsed."""
    spawner = _make_spawner(count=2, cooldown=3, max_enemies=10)
    spawner.update(world)  # fire -> total 2, cooldown_ticks=3
    assert spawner.total_spawned == 2
    spawner.update(world)  # 3 -> 2
    assert spawner.total_spawned == 2
    spawner.update(world)  # 2 -> 1
    assert spawner.total_spawned == 2
    spawner.update(world)  # 1 -> 0
    assert spawner.total_spawned == 2
    spawner.update(world)  # fire -> total 4
    assert spawner.total_spawned == 4


# --- max budget ---


def test_spawn_capped_at_max(world):
    """Spawning stops once the configured maximum is reached."""
    spawner = _make_spawner(count=5, cooldown=1, max_enemies=12)
    for _ in range(10):
        spawner.update(world)
    assert spawner.total_spawned == 12
    assert spawner.all_spawned


def test_pulse_respects_remaining_budget(world):
    """The last pulse only spawns the remaining count, not a full pulse."""
    spawner = _make_spawner(count=5, cooldown=1, max_enemies=12)
    spawner.update(world)  # 5, cooldown_ticks=1
    spawner.update(world)  # idle
    spawner.update(world)  # 10, cooldown_ticks=1
    spawner.update(world)  # idle
    spawner.update(world)  # capped to 12
    assert spawner.total_spawned == 12


def test_no_spawn_after_all_spawned(world):
    """Once all_spawned is True, update does nothing."""
    spawner = _make_spawner(count=10, cooldown=1, max_enemies=5)
    spawner.update(world)
    assert spawner.total_spawned == 5
    spawner.update(world)
    assert spawner.total_spawned == 5


# --- edge positions ---


def test_spawn_positions_on_border(world):
    """Every spawned enemy sits on the screen border."""
    spawner = _make_spawner(count=20, cooldown=1, max_enemies=20)
    spawner.update(world)
    for entity, enemy, pos in world.query(Enemy, Position):
        on_x = pos.x <= 0.0 or pos.x >= 800.0
        on_y = pos.y <= 0.0 or pos.y >= 600.0
        assert on_x or on_y


def test_spawned_enemy_has_required_components(world):
    """A spawned enemy has Health, Position and Enemy components."""
    spawner = _make_spawner(count=1, cooldown=1, max_enemies=1)
    spawner.update(world)
    for entity, enemy, health, pos in world.query(Enemy, Health, Position):
        assert health.value > 0
        return
    pytest.fail("no enemy spawned")


# --- all_spawned flag ---


def test_all_spawned_false_initially():
    spawner = _make_spawner(max_enemies=10)
    assert not spawner.all_spawned


def test_all_spawned_true_after_budget_reached(world):
    spawner = _make_spawner(count=10, cooldown=1, max_enemies=10)
    spawner.update(world)
    assert spawner.all_spawned
