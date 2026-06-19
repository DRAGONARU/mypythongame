from src.systems.combat_system import CombatSystem
from src.core.components import Knife, Health, Owner
from src.core.events import CollisionEvent
from src.core.ecs.entity import Entity
from src.core.ecs.world import World
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
