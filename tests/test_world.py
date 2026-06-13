from src.core.ecs.world import World
from src.core.ecs.entity import Entity
import pytest


@pytest.fixture
def world():
    return World()


# --- create_entity ---

def test_create_entity_sequential_ids(world):
    e0 = world.create_entity()
    e1 = world.create_entity()
    e2 = world.create_entity()
    assert e0.id == 0
    assert e1.id == 1
    assert e2.id == 2
    assert e0.generation == 0
    assert e1.generation == 0
    assert e2.generation == 0


def test_create_entity_alive_counter(world):
    world.create_entity()
    world.create_entity()
    assert world._alive == 2


# --- destroy_entity ---

def test_destroy_entity_alive(world):
    e = world.create_entity()
    assert world.destroy_entity(e) is True


def test_destroy_entity_double(world):
    e = world.create_entity()
    world.destroy_entity(e)
    assert world.destroy_entity(e) is False


def test_destroy_entity_never_created(world):
    ghost = Entity(id=999, generation=0)
    assert world.destroy_entity(ghost) is False


def test_destroy_entity_stale_handle(world):
    e = world.create_entity()
    world.destroy_entity(e)
    stale = Entity(id=e.id, generation=e.generation)
    assert world.destroy_entity(stale) is False


def test_destroy_entity_decrements_alive(world):
    e = world.create_entity()
    world.create_entity()
    world.destroy_entity(e)
    assert world._alive == 1


def test_destroy_entity_frees_id(world):
    e = world.create_entity()
    world.destroy_entity(e)
    assert e.id in world._free_ids


def test_destroy_entity_increments_generation(world):
    e = world.create_entity()
    gen_before = world._generations[e.id]
    world.destroy_entity(e)
    assert world._generations[e.id] == gen_before + 1


def test_destroy_entity_removes_all_components(world):
    e = world.create_entity()
    world.add_component(e, "pos_value")
    world.add_component(e, "vel_value")
    world.destroy_entity(e)
    assert world.get_component(e, str) is None


# --- id reuse after destroy ---

def test_create_after_destroy_reuses_id(world):
    e = world.create_entity()
    world.destroy_entity(e)
    e2 = world.create_entity()
    assert e2.id == e.id
    assert e2.generation == e.generation + 1


def test_stale_handle_unusable_after_reuse(world):
    e = world.create_entity()
    world.add_component(e, "old_data")
    world.destroy_entity(e)
    e2 = world.create_entity()
    world.add_component(e2, "new_data")
    assert world.get_component(e, str) is None
    assert world.get_component(e2, str) == "new_data"
    assert world.add_component(e, "x") is False
    assert world.remove_component(e, str) is False


def test_reuse_lifo_order(world):
    e0 = world.create_entity()
    e1 = world.create_entity()
    world.destroy_entity(e0)
    world.destroy_entity(e1)
    reused_first = world.create_entity()
    reused_second = world.create_entity()
    assert reused_first.id == e1.id
    assert reused_second.id == e0.id


# --- add_component ---

def test_add_component_alive(world):
    e = world.create_entity()
    assert world.add_component(e, "value") is True


def test_add_component_dead(world):
    e = world.create_entity()
    world.destroy_entity(e)
    assert world.add_component(e, "value") is False


def test_add_component_stale(world):
    e = world.create_entity()
    world.destroy_entity(e)
    e2 = world.create_entity()
    stale = Entity(id=e.id, generation=e.generation)
    assert world.add_component(stale, "value") is False


def test_add_component_update_overwrites(world):
    e = world.create_entity()
    world.add_component(e, "old")
    world.add_component(e, "new")
    assert world.get_component(e, str) == "new"


def test_add_component_creates_sparse_set(world):
    e = world.create_entity()
    world.add_component(e, "val")
    assert str in world._components


def test_add_component_multiple_types(world):
    e = world.create_entity()
    world.add_component(e, "string_val")
    world.add_component(e, 42)
    assert world.get_component(e, str) == "string_val"
    assert world.get_component(e, int) == 42


# --- get_component ---

def test_get_component_existing(world):
    e = world.create_entity()
    world.add_component(e, "val")
    assert world.get_component(e, str) == "val"


def test_get_component_missing_type(world):
    e = world.create_entity()
    assert world.get_component(e, str) is None


def test_get_component_entity_no_component(world):
    e = world.create_entity()
    world.add_component(e, 42)
    assert world.get_component(e, str) is None


def test_get_component_dead_entity(world):
    e = world.create_entity()
    world.add_component(e, "val")
    world.destroy_entity(e)
    assert world.get_component(e, str) is None


def test_get_component_stale_entity(world):
    e = world.create_entity()
    world.add_component(e, "val")
    world.destroy_entity(e)
    stale = Entity(id=e.id, generation=e.generation)
    assert world.get_component(stale, str) is None


# --- remove_component ---

def test_remove_component_existing(world):
    e = world.create_entity()
    world.add_component(e, "val")
    assert world.remove_component(e, str) is True
    assert world.get_component(e, str) is None


def test_remove_component_absent(world):
    e = world.create_entity()
    assert world.remove_component(e, str) is False


def test_remove_component_dead_entity(world):
    e = world.create_entity()
    world.add_component(e, "val")
    world.destroy_entity(e)
    assert world.remove_component(e, str) is False


def test_remove_component_unknown_type(world):
    e = world.create_entity()
    assert world.remove_component(e, float) is False


# --- _is_alive ---

def test_is_alive_true(world):
    e = world.create_entity()
    assert world._is_alive(e) is True


def test_is_alive_never_created(world):
    ghost = Entity(id=0, generation=0)
    assert world._is_alive(ghost) is False


def test_is_alive_after_destroy(world):
    e = world.create_entity()
    world.destroy_entity(e)
    assert world._is_alive(e) is False


# --- query ---

def test_query_basic(world):
    e = world.create_entity()
    world.add_component(e, "pos")
    world.add_component(e, 10)
    results = list(world.query(str, int))
    assert len(results) == 1
    entity, pos, vel = results[0]
    assert entity == e
    assert pos == "pos"
    assert vel == 10


def test_query_missing_component_skipped(world):
    e1 = world.create_entity()
    world.add_component(e1, "pos")
    world.add_component(e1, 10)
    e2 = world.create_entity()
    world.add_component(e2, "pos_only")
    results = list(world.query(str, int))
    assert len(results) == 1
    assert results[0][0] == e1


def test_query_no_match(world):
    e = world.create_entity()
    world.add_component(e, "pos")
    results = list(world.query(str, int))
    assert results == []


def test_query_empty_world(world):
    results = list(world.query(str, int))
    assert results == []


def test_query_duplicate_types_raises(world):
    with pytest.raises(ValueError):
        world.query(str, str)


def test_query_type_not_in_components(world):
    e = world.create_entity()
    world.add_component(e, "pos")
    results = list(world.query(str, float))
    assert results == []


# --- full lifecycle integration ---

def test_full_lifecycle(world):
    e = world.create_entity()
    world.add_component(e, "pos")
    world.add_component(e, 5)
    assert world.get_component(e, str) == "pos"
    assert world.get_component(e, int) == 5
    results = list(world.query(str, int))
    assert len(results) == 1
    world.destroy_entity(e)
    assert world.get_component(e, str) is None
    assert world.get_component(e, int) is None
    results = list(world.query(str, int))
    assert results == []


def test_lifecycle_with_id_reuse(world):
    e1 = world.create_entity()
    world.add_component(e1, "old_pos")
    world.destroy_entity(e1)
    e2 = world.create_entity()
    world.add_component(e2, "new_pos")
    assert world.get_component(e1, str) is None
    assert world.get_component(e2, str) == "new_pos"
    results = list(world.query(str))
    assert len(results) == 1
    assert results[0][0] == e2