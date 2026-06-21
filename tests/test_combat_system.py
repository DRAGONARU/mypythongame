from src.systems.combat_system import CombatSystem
from src.core.components import Knife, Health, Owner, Enemy, Player, DamageCooldown
from src.core.events import CollisionEvent
from src.core.ecs.entity import Entity
from src.core.ecs.world import World
from config.config_params import ENEMY_CONTACT_DAMAGE, ENEMY_HIT_COOLDOWN
import pytest


@pytest.fixture
def system():
    return CombatSystem()


@pytest.fixture
def world():
    return World()


def _add_knife(world, damage=10, owner=None):
    e = world.create_entity()
    world.add_component(e, Knife(knife_type="normal", damage=damage, speed=5.0))
    if owner is not None:
        world.add_component(e, Owner(entity=owner))
    return e


def _add_enemy(world, hp=100):
    e = world.create_entity()
    world.add_component(e, Health(value=hp, max_value=hp))
    return e


def test_combat_empty_events(system, world):
    """System handles empty events list gracefully."""
    system.update(world)


def test_combat_knife_hits_enemy(system, world):
    """Knife deals damage to enemy."""
    knife = _add_knife(world, damage=30)
    enemy = _add_enemy(world, hp=100)

    world.events.append(CollisionEvent(knife, enemy, world.tick))
    system.update(world)

    assert world.get_component(enemy, Health).value == 70


def test_combat_knife_destroyed_after_hit(system, world):
    """Knife is destroyed after hitting enemy."""
    knife = _add_knife(world, damage=10)
    enemy = _add_enemy(world, hp=100)

    world.events.append(CollisionEvent(knife, enemy, world.tick))
    system.update(world)

    assert not world._is_alive(knife)
    assert world._is_alive(enemy)


def test_combat_knife_kills_enemy(system, world):
    """Knife can reduce health below zero."""
    knife = _add_knife(world, damage=150)
    enemy = _add_enemy(world, hp=100)

    world.events.append(CollisionEvent(knife, enemy, world.tick))
    system.update(world)

    assert world.get_component(enemy, Health).value == -50


def test_combat_owner_not_damaged(system, world):
    """Knife does not damage its owner."""
    owner = _add_enemy(world, hp=100)
    knife = _add_knife(world, damage=50, owner=owner)

    world.events.append(CollisionEvent(knife, owner, world.tick))
    system.update(world)

    assert world.get_component(owner, Health).value == 100


def test_combat_no_knife_no_damage(system, world):
    """Collision between two enemies deals no damage."""
    e1 = _add_enemy(world, hp=100)
    e2 = _add_enemy(world, hp=50)

    world.events.append(CollisionEvent(e1, e2, world.tick))
    system.update(world)

    assert world.get_component(e1, Health).value == 100
    assert world.get_component(e2, Health).value == 50


def test_combat_no_health_no_effect(system, world):
    """Knife hitting entity without Health does nothing."""
    knife = _add_knife(world, damage=10)
    target = world.create_entity()

    world.events.append(CollisionEvent(knife, target, world.tick))
    system.update(world)

    assert world._is_alive(knife)


def test_combat_dead_attacker_skipped(system, world):
    """Already destroyed attacker is skipped."""
    knife = _add_knife(world, damage=10)
    enemy = _add_enemy(world, hp=100)

    world.destroy_entity(knife)
    world.events.append(CollisionEvent(knife, enemy, world.tick))
    system.update(world)

    assert world.get_component(enemy, Health).value == 100


def test_combat_dead_defender_skipped(system, world):
    """Already destroyed defender is skipped."""
    knife = _add_knife(world, damage=10)
    enemy = _add_enemy(world, hp=100)

    world.destroy_entity(enemy)
    world.events.append(CollisionEvent(knife, enemy, world.tick))
    system.update(world)

    assert world._is_alive(knife)


def test_combat_multiple_events(system, world):
    """Multiple collision events are processed independently."""
    knife1 = _add_knife(world, damage=20)
    enemy1 = _add_enemy(world, hp=100)

    knife2 = _add_knife(world, damage=40)
    enemy2 = _add_enemy(world, hp=100)

    world.events.append(CollisionEvent(knife1, enemy1, world.tick))
    world.events.append(CollisionEvent(knife2, enemy2, world.tick))
    system.update(world)

    assert world.get_component(enemy1, Health).value == 80
    assert world.get_component(enemy2, Health).value == 60


# --- enemy contact damage ---


def _add_real_enemy(world, hp=100):
    e = world.create_entity()
    world.add_component(e, Enemy())
    world.add_component(e, Health(value=hp, max_value=hp))
    return e


def _add_player(world, hp=100):
    e = world.create_entity()
    world.add_component(e, Player())
    world.add_component(e, Health(value=hp, max_value=hp))
    return e


def test_enemy_contact_damage_to_player(system, world):
    """Enemy touching player deals ENEMY_CONTACT_DAMAGE."""
    enemy = _add_real_enemy(world)
    player = _add_player(world, hp=100)

    world.events.append(CollisionEvent(enemy, player, world.tick))
    system.update(world)

    assert world.get_component(player, Health).value == 100 - ENEMY_CONTACT_DAMAGE


def test_enemy_contact_sets_cooldown(system, world):
    """Player gets a DamageCooldown after being hit."""
    enemy = _add_real_enemy(world)
    player = _add_player(world)

    world.events.append(CollisionEvent(enemy, player, world.tick))
    system.update(world)

    cd = world.get_component(player, DamageCooldown)
    assert cd is not None
    assert cd.remaining_ticks == ENEMY_HIT_COOLDOWN


def test_enemy_contact_respects_cooldown(system, world):
    """While on cooldown, contact deals no damage."""
    enemy = _add_real_enemy(world)
    player = _add_player(world, hp=100)
    world.add_component(player, DamageCooldown(remaining_ticks=ENEMY_HIT_COOLDOWN))

    world.events.append(CollisionEvent(enemy, player, world.tick))
    system.update(world)

    assert world.get_component(player, Health).value == 100


def test_enemy_contact_direction_agnostic(system, world):
    """Damage applies regardless of event argument order."""
    enemy = _add_real_enemy(world)
    player = _add_player(world, hp=100)

    world.events.append(CollisionEvent(player, enemy, world.tick))
    system.update(world)

    assert world.get_component(player, Health).value == 100 - ENEMY_CONTACT_DAMAGE


def test_enemy_not_destroyed_on_contact(system, world):
    """Enemy survives contact (only knives are destroyed)."""
    enemy = _add_real_enemy(world, hp=50)
    player = _add_player(world)

    world.events.append(CollisionEvent(enemy, player, world.tick))
    system.update(world)

    assert world._is_alive(enemy)


def test_cooldown_decrements_each_tick(system, world):
    """DamageCooldown counts down over ticks."""
    player = _add_player(world)
    world.add_component(player, DamageCooldown(remaining_ticks=5))

    system.update(world)
    assert world.get_component(player, DamageCooldown).remaining_ticks == 4

    system.update(world)
    assert world.get_component(player, DamageCooldown).remaining_ticks == 3


def test_cooldown_removed_when_expired(system, world):
    """DamageCooldown is removed when it reaches zero."""
    player = _add_player(world)
    world.add_component(player, DamageCooldown(remaining_ticks=1))

    system.update(world)

    assert world.get_component(player, DamageCooldown) is None


def test_multiple_enemies_one_damage_per_cooldown(system, world):
    """Several enemies hitting same tick: only first deals damage."""
    enemies = [_add_real_enemy(world) for _ in range(3)]
    player = _add_player(world, hp=100)

    for enemy in enemies:
        world.events.append(CollisionEvent(enemy, player, world.tick))
    system.update(world)

    assert world.get_component(player, Health).value == 100 - ENEMY_CONTACT_DAMAGE


def test_knife_and_enemy_contact_in_one_tick(system, world):
    """Knife damage to enemy and enemy contact to player coexist."""
    knife = _add_knife(world, damage=25)
    enemy = _add_real_enemy(world, hp=100)
    player = _add_player(world, hp=100)
    world.add_component(knife, Owner(entity=player))

    world.events.append(CollisionEvent(knife, enemy, world.tick))
    world.events.append(CollisionEvent(enemy, player, world.tick))
    system.update(world)

    assert world.get_component(enemy, Health).value == 75
    assert world.get_component(player, Health).value == 100 - ENEMY_CONTACT_DAMAGE


def test_enemy_contact_no_health_no_crash(system, world):
    """Player without Health is skipped without error."""
    enemy = _add_real_enemy(world)
    player = world.create_entity()
    world.add_component(player, Player())

    world.events.append(CollisionEvent(enemy, player, world.tick))
    system.update(world)


def test_non_enemy_non_knife_attacker_no_damage(system, world):
    """A generic entity (no Knife, no Enemy) deals no contact damage."""
    attacker = world.create_entity()
    player = _add_player(world, hp=100)

    world.events.append(CollisionEvent(attacker, player, world.tick))
    system.update(world)

    assert world.get_component(player, Health).value == 100


def test_cooldown_expires_then_damage_again(system, world):
    """After cooldown expires, the player can be hit again."""
    enemy = _add_real_enemy(world)
    player = _add_player(world, hp=100)

    world.events.append(CollisionEvent(enemy, player, world.tick))
    system.update(world)
    assert world.get_component(player, Health).value == 100 - ENEMY_CONTACT_DAMAGE
    world.events.clear()

    for _ in range(ENEMY_HIT_COOLDOWN):
        system.update(world)
    assert world.get_component(player, DamageCooldown) is None

    world.events.append(CollisionEvent(enemy, player, world.tick))
    system.update(world)
    assert world.get_component(player, Health).value == 100 - 2 * ENEMY_CONTACT_DAMAGE
