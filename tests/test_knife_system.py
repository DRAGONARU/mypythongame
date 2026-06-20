from src.systems.knife_system import KnifeSystem, KnifeBounceSystem
from src.core.components import (
    Knife, Position, Velocity, Collider, Lifetime, Owner, TimeAffected,
    CollisionFilter, Reflective, Delayed, KnifeLoadout, Player, Enemy,
    InputState, Health, LAYER_KNIFE, LAYER_ENEMY,
)
from src.core.events import CollisionEvent
from src.core.ecs.world import World
import pygame
import pytest


@pytest.fixture
def system():
    return KnifeSystem()


@pytest.fixture
def bounce_system():
    return KnifeBounceSystem()


@pytest.fixture
def world():
    return World()


def _make_keys(*pressed):
    """Build a keys_pressed tuple with given pygame key constants set True."""
    keys = [False] * 300
    for k in pressed:
        keys[k] = True
    return tuple(keys)


def _add_input_state(world, mouse_x=0.0, mouse_y=0.0, mouse_pressed=(False, False, False), keys=None):
    if keys is None:
        keys = _make_keys()
    e = world.create_entity()
    world.add_component(e, InputState(
        mouse_x=mouse_x, mouse_y=mouse_y,
        mouse_pressed=mouse_pressed, keys_pressed=keys,
    ))
    return e


def _add_player(world, x=0.0, y=0.0, current="normal", cooldown=0, keys=None):
    if keys is None:
        keys = _make_keys()
    e = world.create_entity()
    world.add_component(e, Player())
    world.add_component(e, Position(x=x, y=y))
    world.add_component(e, KnifeLoadout(current=current, cooldown=cooldown))
    world.add_component(e, InputState(keys_pressed=keys))
    return e


# --- _handle_selection tests ---

def test_selection_normal(system, world):
    """Pressing 1 selects normal knife."""
    player = _add_player(world, current="delayed")
    world.add_component(player, InputState(keys_pressed=_make_keys(pygame.K_1)))

    system.update(world)

    assert world.get_component(player, KnifeLoadout).current == "normal"


def test_selection_delayed(system, world):
    """Pressing 2 selects delayed knife."""
    player = _add_player(world, current="normal")
    world.add_component(player, InputState(keys_pressed=_make_keys(pygame.K_2)))

    system.update(world)

    assert world.get_component(player, KnifeLoadout).current == "delayed"


def test_selection_reflective(system, world):
    """Pressing 3 selects reflective knife."""
    player = _add_player(world, current="normal")
    world.add_component(player, InputState(keys_pressed=_make_keys(pygame.K_3)))

    system.update(world)

    assert world.get_component(player, KnifeLoadout).current == "reflective"


def test_selection_no_keys_keeps_current(system, world):
    """No keys pressed keeps current selection."""
    player = _add_player(world, current="reflective")
    world.add_component(player, InputState(keys_pressed=()))

    system.update(world)

    assert world.get_component(player, KnifeLoadout).current == "reflective"


def test_selection_unavailable_type_ignored(system, world):
    """Cannot select a knife type not in available."""
    player = _add_player(world, current="normal")
    world.add_component(player, KnifeLoadout(
        current="normal", available=("normal",), cooldown=0))
    world.add_component(player, InputState(keys_pressed=_make_keys(pygame.K_2)))

    system.update(world)

    assert world.get_component(player, KnifeLoadout).current == "normal"


# --- _handle_spawning tests ---

def test_spawn_on_left_click(system, world):
    """Left click spawns a knife."""
    player = _add_player(world, x=0.0, y=0.0)
    world.add_component(player, InputState(
        mouse_x=100.0, mouse_y=0.0,
        mouse_pressed=(True, False, False)))

    system.update(world)

    knives = list(world.query(Knife))
    assert len(knives) == 1


def test_no_spawn_without_click(system, world):
    """No click means no knife spawned."""
    player = _add_player(world)
    world.add_component(player, InputState(
        mouse_pressed=(False, False, False)))

    system.update(world)

    knives = list(world.query(Knife))
    assert len(knives) == 0


def test_spawn_cooldown_prevents_spam(system, world):
    """Cooldown prevents spawning multiple knives per click."""
    player = _add_player(world)
    world.add_component(player, InputState(
        mouse_x=100.0, mouse_pressed=(True, False, False)))

    system.update(world)
    assert len(list(world.query(Knife))) == 1

    system.update(world)
    assert len(list(world.query(Knife))) == 1

    system.update(world)
    assert len(list(world.query(Knife))) == 1


def test_spawn_after_cooldown_expires(system, world):
    """Knife can spawn again after cooldown expires."""
    player = _add_player(world)
    world.add_component(player, InputState(
        mouse_x=100.0, mouse_pressed=(True, False, False)))

    for _ in range(KnifeSystem.SPAWN_COOLDOWN + 2):
        system.update(world)

    assert len(list(world.query(Knife))) == 2


def test_spawn_direction_toward_cursor(system, world):
    """Knife velocity points toward cursor."""
    player = _add_player(world, x=0.0, y=0.0)
    world.add_component(player, InputState(
        mouse_x=100.0, mouse_y=0.0,
        mouse_pressed=(True, False, False)))

    system.update(world)

    for entity, knife, vel in world.query(Knife, Velocity):
        assert vel.x > 0
        assert abs(vel.y) < 0.01
        assert abs(vel.x) == pytest.approx(KnifeSystem.KNIFE_SPEED)


def test_spawn_direction_diagonal(system, world):
    """Knife velocity is normalized toward diagonal cursor."""
    player = _add_player(world, x=0.0, y=0.0)
    world.add_component(player, InputState(
        mouse_x=100.0, mouse_y=100.0,
        mouse_pressed=(True, False, False)))

    system.update(world)

    for entity, knife, vel in world.query(Knife, Velocity):
        expected = KnifeSystem.KNIFE_SPEED / (2 ** 0.5)
        assert vel.x == pytest.approx(expected)
        assert vel.y == pytest.approx(expected)


# --- spawn component tests ---

def test_spawn_normal_has_all_components(system, world):
    """Normal knife has the correct component set."""
    player = _add_player(world)
    world.add_component(player, InputState(
        mouse_x=100.0, mouse_pressed=(True, False, False)))

    system.update(world)

    for entity, knife in world.query(Knife):
        assert world.get_component(entity, Position) is not None
        assert world.get_component(entity, Velocity) is not None
        assert world.get_component(entity, Collider) is not None
        assert world.get_component(entity, Lifetime) is not None
        assert world.get_component(entity, Owner) is not None
        assert world.get_component(entity, TimeAffected) is not None
        assert world.get_component(entity, CollisionFilter) is not None
        assert world.get_component(entity, Delayed) is None
        assert world.get_component(entity, Reflective) is None
        assert world.get_component(entity, TimeAffected).scale == 1.0


def test_spawn_delayed_is_frozen(system, world):
    """Delayed knife starts frozen (scale=0) and has Delayed component."""
    player = _add_player(world, current="delayed")
    world.add_component(player, InputState(
        mouse_x=100.0, mouse_pressed=(True, False, False)))

    system.update(world)

    for entity, knife in world.query(Knife):
        assert world.get_component(entity, Delayed) is not None
        assert world.get_component(entity, TimeAffected).scale == 0.0
        assert world.get_component(entity, Reflective) is None


def test_spawn_reflective_has_bounces(system, world):
    """Reflective knife has Reflective component with bounces."""
    player = _add_player(world, current="reflective")
    world.add_component(player, InputState(
        mouse_x=100.0, mouse_pressed=(True, False, False)))

    system.update(world)

    for entity, knife in world.query(Knife):
        reflective = world.get_component(entity, Reflective)
        assert reflective is not None
        assert reflective.bounces_remaining == KnifeSystem.REFLECTIVE_BOUNCES
        assert world.get_component(entity, TimeAffected).scale == 1.0
        assert world.get_component(entity, Delayed) is None


def test_spawn_knife_owner_is_player(system, world):
    """Spawned knife owner is the player entity."""
    player = _add_player(world)
    world.add_component(player, InputState(
        mouse_x=100.0, mouse_pressed=(True, False, False)))

    system.update(world)

    for entity, knife, owner in world.query(Knife, Owner):
        assert owner.entity == player


def test_spawn_knife_collision_filter(system, world):
    """Spawned knife collides only with enemies."""
    player = _add_player(world)
    world.add_component(player, InputState(
        mouse_x=100.0, mouse_pressed=(True, False, False)))

    system.update(world)

    for entity, knife, cf in world.query(Knife, CollisionFilter):
        assert cf.layer == LAYER_KNIFE
        assert cf.mask == LAYER_ENEMY


# --- _activate_delayed tests ---

def _add_delayed_knife(world, owner, activate_ticks=3):
    e = world.create_entity()
    world.add_component(e, Position(x=0.0, y=0.0))
    world.add_component(e, Velocity(x=100.0, y=0.0))
    world.add_component(e, Collider(radius=4.0))
    world.add_component(e, Knife(knife_type="delayed", damage=25, speed=300.0))
    world.add_component(e, Lifetime(remaining_ticks=240))
    world.add_component(e, Owner(entity=owner))
    world.add_component(e, TimeAffected(scale=0.0))
    world.add_component(e, Delayed(activate_ticks=activate_ticks))
    world.add_component(e, CollisionFilter(layer=LAYER_KNIFE, mask=LAYER_ENEMY))
    return e


def test_delayed_does_not_activate_immediately(system, world):
    """Delayed knife is still delayed after one tick."""
    owner = _add_player(world)
    knife = _add_delayed_knife(world, owner, activate_ticks=3)

    system.update(world)

    assert world.get_component(knife, Delayed) is not None
    assert world.get_component(knife, TimeAffected).scale == 0.0


def test_delayed_activates_after_ticks(system, world):
    """Delayed knife activates after activate_ticks reach zero."""
    owner = _add_player(world)
    knife = _add_delayed_knife(world, owner, activate_ticks=3)

    system.update(world)
    system.update(world)
    system.update(world)

    assert world.get_component(knife, Delayed) is None
    assert world.get_component(knife, TimeAffected).scale == 1.0


def test_delayed_activation_removes_delayed_component(system, world):
    """After activation, Delayed component is removed."""
    owner = _add_player(world)
    knife = _add_delayed_knife(world, owner, activate_ticks=1)

    system.update(world)

    assert world.get_component(knife, Delayed) is None


def test_multiple_delayed_knives_activate_same_tick(system, world):
    """Multiple delayed knives activating in one tick do not raise or skip."""
    owner = _add_player(world)
    knives = [_add_delayed_knife(world, owner, activate_ticks=1) for _ in range(5)]

    system.update(world)

    for knife in knives:
        assert world.get_component(knife, Delayed) is None
        assert world.get_component(knife, TimeAffected).scale == 1.0


def test_multiple_delayed_knives_partial_activation(system, world):
    """Some knives ready, some not: only ready ones activate, none skipped."""
    owner = _add_player(world)
    ready = [_add_delayed_knife(world, owner, activate_ticks=1) for _ in range(3)]
    not_ready = [_add_delayed_knife(world, owner, activate_ticks=5) for _ in range(3)]

    system.update(world)

    for knife in ready:
        assert world.get_component(knife, Delayed) is None
        assert world.get_component(knife, TimeAffected).scale == 1.0
    for knife in not_ready:
        assert world.get_component(knife, Delayed) is not None
        assert world.get_component(knife, TimeAffected).scale == 0.0


# --- _bounce_reflective tests ---

def _add_reflective_knife(world, owner, x=0.0, y=0.0, vx=100.0, vy=0.0, bounces=3):
    e = world.create_entity()
    world.add_component(e, Position(x=x, y=y))
    world.add_component(e, Velocity(x=vx, y=vy))
    world.add_component(e, Collider(radius=4.0))
    world.add_component(e, Knife(knife_type="reflective", damage=25, speed=300.0))
    world.add_component(e, Lifetime(remaining_ticks=240))
    world.add_component(e, Owner(entity=owner))
    world.add_component(e, TimeAffected(scale=1.0))
    world.add_component(e, Reflective(bounces_remaining=bounces))
    world.add_component(e, CollisionFilter(layer=LAYER_KNIFE, mask=LAYER_ENEMY))
    return e


def _add_enemy(world, x=0.0, y=0.0, radius=10.0):
    e = world.create_entity()
    world.add_component(e, Enemy())
    world.add_component(e, Position(x=x, y=y))
    world.add_component(e, Collider(radius=radius))
    return e


def test_bounce_changes_velocity(bounce_system, world):
    """Reflective knife velocity changes after bouncing off enemy."""
    owner = _add_player(world)
    knife = _add_reflective_knife(world, owner, x=0.0, y=0.0, vx=100.0, vy=0.0)
    enemy = _add_enemy(world, x=10.0, y=0.0, radius=10.0)

    world.events.append(CollisionEvent(knife, enemy, world.tick))
    bounce_system.update(world)

    vel = world.get_component(knife, Velocity)
    assert vel.x < 0


def test_bounce_decrements_bounces(bounce_system, world):
    """Each bounce decrements bounces_remaining."""
    owner = _add_player(world)
    knife = _add_reflective_knife(world, owner, bounces=3)
    enemy = _add_enemy(world, x=10.0, y=0.0)

    world.events.append(CollisionEvent(knife, enemy, world.tick))
    bounce_system.update(world)

    assert world.get_component(knife, Reflective).bounces_remaining == 2


def test_bounce_removes_reflective_at_zero(bounce_system, world):
    """Reflective component removed when bounces reach zero."""
    owner = _add_player(world)
    knife = _add_reflective_knife(world, owner, bounces=1)
    enemy = _add_enemy(world, x=10.0, y=0.0)

    world.events.append(CollisionEvent(knife, enemy, world.tick))
    bounce_system.update(world)

    assert world.get_component(knife, Reflective) is None


def test_bounce_ignores_non_reflective_knife(bounce_system, world):
    """Non-reflective knife is not affected by bounce logic."""
    owner = _add_player(world)
    knife = _add_reflective_knife(world, owner)
    world.remove_component(knife, Reflective)
    enemy = _add_enemy(world, x=10.0, y=0.0)

    original_vx = world.get_component(knife, Velocity).x
    world.events.append(CollisionEvent(knife, enemy, world.tick))
    bounce_system.update(world)

    assert world.get_component(knife, Velocity).x == original_vx


def test_bounce_ignores_non_enemy(bounce_system, world):
    """Bounce only triggers off enemies, not other entities."""
    owner = _add_player(world)
    knife = _add_reflective_knife(world, owner)
    other = world.create_entity()
    world.add_component(other, Position(x=10.0, y=0.0))
    world.add_component(other, Collider(radius=10.0))

    original_vx = world.get_component(knife, Velocity).x
    world.events.append(CollisionEvent(knife, other, world.tick))
    bounce_system.update(world)

    assert world.get_component(knife, Velocity).x == original_vx


def test_bounce_separates_knife_from_enemy(bounce_system, world):
    """After bounce, knife is pushed out of overlap with enemy."""
    owner = _add_player(world)
    knife = _add_reflective_knife(world, owner, x=5.0, y=0.0, vx=100.0, vy=0.0)
    enemy = _add_enemy(world, x=10.0, y=0.0, radius=10.0)

    world.events.append(CollisionEvent(knife, enemy, world.tick))
    bounce_system.update(world)

    knife_pos = world.get_component(knife, Position)
    enemy_pos = world.get_component(enemy, Position)
    dist = ((knife_pos.x - enemy_pos.x) ** 2 + (knife_pos.y - enemy_pos.y) ** 2) ** 0.5
    assert dist >= 14.0 - 0.01


def test_bounce_dead_knife_skipped(bounce_system, world):
    """Already destroyed knife is skipped in bounce."""
    owner = _add_player(world)
    knife = _add_reflective_knife(world, owner)
    enemy = _add_enemy(world, x=10.0, y=0.0)

    world.destroy_entity(knife)
    world.events.append(CollisionEvent(knife, enemy, world.tick))
    bounce_system.update(world)


# --- empty world ---

def test_knife_system_empty_world(system, world):
    """System handles empty world gracefully."""
    system.update(world)


# --- integration: bounce must run after collision+combat ---


def test_reflective_knife_does_not_repeat_damage(bounce_system, world):
    """Reflective knife deals damage once per bounce, not every tick.

    Regression: previously bounce ran before collision events were
    generated, so the knife never bounced and dealt damage every
    tick while overlapping the enemy, killing it instantly.
    """
    from src.systems.combat_system import CombatSystem
    owner = _add_player(world)
    knife = _add_reflective_knife(world, owner, x=0.0, y=0.0, vx=100.0, vy=0.0)
    enemy = _add_enemy(world, x=10.0, y=0.0, radius=10.0)
    world.add_component(enemy, Health(value=50, max_value=50))

    combat = CombatSystem()

    world.events.append(CollisionEvent(knife, enemy, world.tick))
    combat.update(world)
    bounce_system.update(world)
    world.events.clear()

    health_after_first_hit = world.get_component(enemy, Health).value
    assert health_after_first_hit == 25

    knife_pos = world.get_component(knife, Position)
    knife_vel = world.get_component(knife, Velocity)
    knife_pos.x += knife_vel.x
    knife_pos.y += knife_vel.y

    if world.get_component(knife, Collider) is not None:
        from src.systems.collision_system import CollisionSystem
        collision = CollisionSystem()
        collision.update(world)
    combat.update(world)
    bounce_system.update(world)
    world.events.clear()

    assert world.get_component(enemy, Health).value == 25
