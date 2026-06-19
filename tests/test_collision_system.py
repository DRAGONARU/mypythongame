from src.systems.collision_system import CollisionSystem
from src.core.components import Position, Collider, CollisionFilter, LAYER_PLAYER, LAYER_ENEMY, LAYER_KNIFE, LAYER_PROJECTILE, LAYER_PICKUP, LAYER_WALL
from src.core.ecs.world import World
import pytest


@pytest.fixture
def system():
    return CollisionSystem(cell_size=64.0)


@pytest.fixture
def world():
    return World()


def _add_entity(world, x, y, radius):
    e = world.create_entity()
    world.add_component(e, Position(x=x, y=y))
    if radius is not None:
        world.add_component(e, Collider(radius=radius))
    return e


def test_collision_empty_world(system, world):
    """System handles empty world gracefully."""
    system.update(world)


def test_collision_no_overlap(system, world):
    """Entities far apart don't collide."""
    _add_entity(world, 0.0, 0.0, 10.0)
    _add_entity(world, 500.0, 500.0, 10.0)

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert calls == []


def test_collision_overlap_detected(system, world):
    """Overlapping entities trigger collision."""
    _add_entity(world, 0.0, 0.0, 15.0)
    _add_entity(world, 20.0, 0.0, 15.0)

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert len(calls) == 1


def test_collision_no_duplicate_pairs(system, world):
    """Each pair is checked only once."""
    _add_entity(world, 0.0, 0.0, 20.0)
    _add_entity(world, 10.0, 0.0, 20.0)

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert len(calls) == 1


def test_collision_just_touching(system, world):
    """Entities touching at exact boundary count as collision."""
    _add_entity(world, 0.0, 0.0, 10.0)
    _add_entity(world, 20.0, 0.0, 10.0)

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert len(calls) == 1


def test_collision_just_apart(system, world):
    """Entities just outside boundary don't collide."""
    _add_entity(world, 0.0, 0.0, 10.0)
    _add_entity(world, 20.001, 0.0, 10.0)

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert calls == []


def test_collision_multiple_entities(system, world):
    """Multiple overlapping entities generate correct pairs."""
    _add_entity(world, 0.0, 0.0, 20.0)
    _add_entity(world, 10.0, 0.0, 20.0)
    _add_entity(world, 5.0, 5.0, 20.0)

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert len(calls) == 3


def test_collision_entity_without_collider_ignored(system, world):
    """Entity without Collider is ignored."""
    _add_entity(world, 0.0, 0.0, 10.0)
    _add_entity(world, 1.0, 0.0, None)

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert calls == []


def test_collision_entity_without_position_ignored(system, world):
    """Entity without Position is ignored."""
    _add_entity(world, 0.0, 0.0, 10.0)
    e2 = world.create_entity()
    world.add_component(e2, Collider(radius=10.0))

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert calls == []


# --- CollisionFilter / _should_collide tests ---

def test_should_collide_knife_enemy_true(system):
    """Knife and enemy should collide."""
    f1 = CollisionFilter(layer=LAYER_KNIFE, mask=LAYER_ENEMY)
    f2 = CollisionFilter(layer=LAYER_ENEMY, mask=LAYER_KNIFE)
    assert system._should_collide(f1, f2)


def test_should_collide_knife_knife_false(system):
    """Two knives should not collide."""
    f1 = CollisionFilter(layer=LAYER_KNIFE, mask=LAYER_ENEMY)
    f2 = CollisionFilter(layer=LAYER_KNIFE, mask=LAYER_ENEMY)
    assert not system._should_collide(f1, f2)


def test_should_collide_player_enemy_true(system):
    """Player and enemy should collide."""
    f1 = CollisionFilter(layer=LAYER_PLAYER, mask=LAYER_ENEMY | LAYER_PROJECTILE)
    f2 = CollisionFilter(layer=LAYER_ENEMY, mask=LAYER_PLAYER | LAYER_KNIFE)
    assert system._should_collide(f1, f2)


def test_should_collide_player_pickup_true(system):
    """Player and pickup should collide."""
    f1 = CollisionFilter(layer=LAYER_PLAYER, mask=LAYER_ENEMY | LAYER_PROJECTILE | LAYER_PICKUP)
    f2 = CollisionFilter(layer=LAYER_PICKUP, mask=LAYER_PLAYER)
    assert system._should_collide(f1, f2)


def test_should_collide_enemy_wall_false(system):
    """Enemy and wall do not collide if wall mask excludes enemy."""
    f1 = CollisionFilter(layer=LAYER_ENEMY, mask=LAYER_KNIFE | LAYER_PLAYER)
    f2 = CollisionFilter(layer=LAYER_WALL, mask=LAYER_KNIFE)
    assert not system._should_collide(f1, f2)


def test_should_collide_one_way_mask_false(system):
    """Collision requires both masks to allow it."""
    f1 = CollisionFilter(layer=LAYER_KNIFE, mask=LAYER_ENEMY)
    f2 = CollisionFilter(layer=LAYER_ENEMY, mask=LAYER_PLAYER)
    assert not system._should_collide(f1, f2)


def test_collision_filter_blocks_pair(system, world):
    """Entities with non-matching filters don't generate collision."""
    e1 = _add_entity(world, 0.0, 0.0, 20.0)
    e2 = _add_entity(world, 5.0, 0.0, 20.0)
    world.add_component(e1, CollisionFilter(layer=LAYER_KNIFE, mask=LAYER_ENEMY))
    world.add_component(e2, CollisionFilter(layer=LAYER_KNIFE, mask=LAYER_ENEMY))

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert calls == []


def test_collision_filter_allows_pair(system, world):
    """Entities with matching filters generate collision."""
    e1 = _add_entity(world, 0.0, 0.0, 20.0)
    e2 = _add_entity(world, 5.0, 0.0, 20.0)
    world.add_component(e1, CollisionFilter(layer=LAYER_KNIFE, mask=LAYER_ENEMY))
    world.add_component(e2, CollisionFilter(layer=LAYER_ENEMY, mask=LAYER_KNIFE))

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert len(calls) == 1


def test_collision_filter_missing_collides_with_all(system, world):
    """Entity without CollisionFilter collides with everything."""
    e1 = _add_entity(world, 0.0, 0.0, 20.0)
    e2 = _add_entity(world, 5.0, 0.0, 20.0)
    world.add_component(e2, CollisionFilter(layer=LAYER_KNIFE, mask=LAYER_ENEMY))

    calls = []
    system._handle_collision = lambda w, a, b: calls.append((a, b))

    system.update(world)

    assert len(calls) == 1


def test_collision_generates_event(system, world):
    """Collision generates CollisionEvent in world.events."""
    e1 = _add_entity(world, 0.0, 0.0, 20.0)
    e2 = _add_entity(world, 5.0, 0.0, 20.0)
    world.tick = 42

    system.update(world)

    assert len(world.events) == 1
    event = world.events[0]
    assert event.tick == 42
    assert {event.a, event.b} == {e1, e2}
