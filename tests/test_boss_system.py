import math
from src.systems.boss_system import BossSystem
from src.systems.wave_spawner_system import WaveSpawner
from src.systems.time_system import TimeSystem
from src.core.components import (
    Boss, Enemy, Player, Position, Velocity, Collider, Health,
    TimeAffected, CollisionFilter, Projectile, Lifetime,
    LAYER_ENEMY, LAYER_PLAYER, LAYER_PROJECTILE, LAYER_KNIFE,
)
from src.core.ecs.world import World
from src.core.events import CollisionEvent
from config.config_params import (
    BOSS_HP, BOSS_RADIUS, BOSS_SPEED, BOSS_PROJECTILE_DAMAGE, BOSS_PROJECTILE_RADIUS,
    BOSS_FIRE_COOLDOWN, BOSS_SPREAD_DEGREES, BOSS_PROJECTILE_SPEED,
    ENEMY_HIT_COOLDOWN, NORMAL, AMOUNT_OF_BOSSES,
)
import pytest


@pytest.fixture
def wave_spawner():
    ws = WaveSpawner((800, 600))
    ws._max_enemies = 5
    ws.total_spawned = 5
    return ws


@pytest.fixture
def time_system():
    ts = TimeSystem()
    ts.current_mode = NORMAL
    return ts


@pytest.fixture
def system(wave_spawner, time_system):
    return BossSystem(wave_spawner, time_system, (800, 600))


@pytest.fixture
def world():
    return World()


def _add_player(world, x=100.0, y=300.0):
    e = world.create_entity()
    world.add_component(e, Player())
    world.add_component(e, Position(x=x, y=y))
    world.add_component(e, Collider(radius=12.0))
    world.add_component(e, Health(value=100, max_value=100))
    return e


# --- boss spawning ---


def test_boss_not_spawned_if_waves_remain(system, world, wave_spawner):
    """Boss does not spawn while WaveSpawner still has budget."""
    wave_spawner.total_spawned = 3
    system.update(world)
    assert not system.boss_spawned
    assert len(list(world.query(Boss))) == 0


def test_boss_not_spawned_if_enemies_alive(system, world):
    """Boss does not spawn while regular enemies are still alive."""
    e = world.create_entity()
    world.add_component(e, Enemy())
    world.add_component(e, Position(x=400, y=300))
    system.update(world)
    assert not system.boss_spawned


def test_boss_spawns_when_cleared(system, world):
    """Boss spawns once all waves are done and no enemies remain."""
    system.update(world)
    assert system.boss_spawned
    bosses = list(world.query(Boss))
    assert len(bosses) == AMOUNT_OF_BOSSES


def test_boss_has_high_hp(system, world):
    """Boss spawns with the configured large HP pool."""
    system.update(world)
    for entity, boss, health in world.query(Boss, Health):
        assert health.value == BOSS_HP
        assert health.max_value == BOSS_HP
        return
    pytest.fail("no boss spawned")


def test_boss_has_large_collider(system, world):
    """Boss collider radius matches the config."""
    system.update(world)
    for entity, boss, col in world.query(Boss, Collider):
        assert col.radius == BOSS_RADIUS
        return
    pytest.fail("no boss spawned")


def test_boss_spawns_at_centre(system, world):
    """Boss appears at the screen centre."""
    system.update(world)
    for entity, boss, pos in world.query(Boss, Position):
        assert pos.x == 400.0
        assert pos.y == 300.0
        return
    pytest.fail("no boss spawned")


def test_boss_has_enemy_component(system, world):
    """Boss carries an Enemy marker so EnemySystem handles its death."""
    system.update(world)
    for entity, boss, enemy in world.query(Boss, Enemy):
        return
    pytest.fail("boss missing Enemy component")


# --- firing ---


def test_boss_fires_three_projectiles(system, world):
    """Each boss fires a 3-round spread on the first fire tick."""
    _add_player(world)
    system.update(world)  # spawn boss
    system.update(world)  # fire
    projectiles = list(world.query(Projectile))
    assert len(projectiles) == AMOUNT_OF_BOSSES * 3


def test_all_bosses_fire(system, world):
    """Every boss sets its fire cooldown, proving each one fired."""
    _add_player(world)
    system.update(world)
    system.update(world)
    for entity, boss in world.query(Boss):
        assert boss.fire_cooldown == BOSS_FIRE_COOLDOWN


def test_centre_projectile_aims_at_player(system, world):
    """The centre projectile flies directly toward the player."""
    _add_player(world, x=700.0, y=300.0)
    system.update(world)
    system.update(world)
    boss_pos = None
    for entity, boss, pos in world.query(Boss, Position):
        boss_pos = pos
        break
    expected = math.atan2(300.0 - boss_pos.y, 700.0 - boss_pos.x)
    angles = [math.atan2(vel.y, vel.x)
              for entity, proj, pos, vel in world.query(Projectile, Position, Velocity)]
    assert expected == pytest.approx(0.0, abs=0.001)
    assert any(a == pytest.approx(expected, abs=0.001) for a in angles)


def test_spread_projectiles_at_twenty_degrees(system, world):
    """Flanking projectiles deviate by +/- 20 degrees from the centre."""
    _add_player(world, x=900.0, y=300.0)
    system.update(world)
    system.update(world)
    boss_pos = None
    for entity, boss, pos in world.query(Boss, Position):
        boss_pos = pos
        break
    base_angle = math.atan2(300.0 - boss_pos.y, 900.0 - boss_pos.x)
    spread = math.radians(BOSS_SPREAD_DEGREES)
    angles = [math.atan2(vel.y, vel.x)
              for entity, proj, pos, vel in world.query(Projectile, Position, Velocity)]
    assert len(angles) == AMOUNT_OF_BOSSES * 3
    expected = [base_angle - spread, base_angle, base_angle + spread]
    for exp in expected:
        assert any(a == pytest.approx(exp, abs=0.01) for a in angles), (
            f"expected angle {exp} not found in {angles}"
        )


def test_fire_cooldown_blocks_shots(system, world):
    """Boss does not fire again until the cooldown elapses."""
    _add_player(world)
    system.update(world)
    system.update(world)
    assert len(list(world.query(Projectile))) == AMOUNT_OF_BOSSES * 3
    system.update(world)
    assert len(list(world.query(Projectile))) == AMOUNT_OF_BOSSES * 3


def test_fire_resumes_after_cooldown(system, world):
    """After the cooldown the boss fires another spread."""
    _add_player(world)
    system.update(world)
    system.update(world)
    for _ in range(BOSS_FIRE_COOLDOWN):
        system.update(world)
    system.update(world)
    assert len(list(world.query(Projectile))) == AMOUNT_OF_BOSSES * 6


def test_no_fire_during_time_stop(system, world, time_system):
    """Boss does not fire while Time Stop is active."""
    time_system.current_mode = "stop"
    _add_player(world)
    system.update(world)
    system.update(world)
    assert len(list(world.query(Projectile))) == 0


def test_no_fire_without_player(system, world):
    """Boss does not fire if there is no player to aim at."""
    system.update(world)
    system.update(world)
    assert len(list(world.query(Projectile))) == 0


def test_projectile_has_lifetime(system, world):
    """Each projectile carries a Lifetime so it despawns eventually."""
    _add_player(world)
    system.update(world)
    system.update(world)
    for entity, proj, lifetime in world.query(Projectile, Lifetime):
        assert lifetime.remaining_ticks > 0
        return
    pytest.fail("no projectile spawned")


def test_projectile_has_collision_filter(system, world):
    """Projectiles collide with the player layer only."""
    _add_player(world)
    system.update(world)
    system.update(world)
    for entity, proj, cf in world.query(Projectile, CollisionFilter):
        assert cf.layer == LAYER_PROJECTILE
        assert cf.mask == LAYER_PLAYER
        return
    pytest.fail("no projectile spawned")


# --- boss death ---


def test_boss_moves_toward_player(system, world):
    """Boss sets its velocity toward the player each tick."""
    _add_player(world, x=100.0, y=300.0)
    system.update(world)  # spawn
    system.update(world)  # move + fire
    for entity, boss, pos, vel in world.query(Boss, Position, Velocity):
        dx = 100.0 - pos.x
        dy = 300.0 - pos.y
        dist = (dx * dx + dy * dy) ** 0.5 or 1.0
        assert vel.x == pytest.approx((dx / dist) * BOSS_SPEED, abs=0.001)
        assert vel.y == pytest.approx((dy / dist) * BOSS_SPEED, abs=0.001)
        return
    pytest.fail("no boss spawned")


def test_boss_no_move_during_time_stop(system, world, time_system):
    """Boss does not move while Time Stop is active."""
    time_system.current_mode = "stop"
    _add_player(world, x=100.0, y=300.0)
    system.update(world)
    system.update(world)
    for entity, boss, vel in world.query(Boss, Velocity):
        assert vel.x == 0.0
        assert vel.y == 0.0
        return
    pytest.fail("no boss spawned")


def test_boss_no_move_without_player(system, world):
    """Boss stays still if there is no player to chase."""
    system.update(world)
    system.update(world)
    for entity, boss, vel in world.query(Boss, Velocity):
        assert vel.x == 0.0
        assert vel.y == 0.0
        return
    pytest.fail("no boss spawned")


# --- boss death ---


def test_boss_death_removes_entity(system, world):
    """Boss with Health <= 0 is destroyed by EnemySystem death check."""
    from src.systems.enemy_system import EnemySystem
    enemy_system = EnemySystem()
    system.update(world)
    for entity, boss, health in world.query(Boss, Health):
        health.value = 0
    enemy_system.update(world)
    assert len(list(world.query(Boss))) == 0
