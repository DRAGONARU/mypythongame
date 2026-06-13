from src.core.ecs.world import World
from src.core.ecs.entity import Entity
from src.core.ecs.query import Query
import pytest


@pytest.fixture
def world():
    w = World()
    e1 = w.create_entity()
    w.add_component(e1, "pos1")
    w.add_component(e1, 10)
    w.add_component(e1, 1.0)

    e2 = w.create_entity()
    w.add_component(e2, "pos2")
    w.add_component(e2, 20)

    e3 = w.create_entity()
    w.add_component(e3, "pos3")

    return w


# --- basic iteration ---

def test_query_single_type(world):
    results = list(world.query(str))
    assert len(results) == 3
    for entity, val in results:
        assert isinstance(val, str)


def test_query_two_types(world):
    results = list(world.query(str, int))
    assert len(results) == 2
    for entity, s, i in results:
        assert isinstance(s, str)
        assert isinstance(i, int)


def test_query_three_types(world):
    results = list(world.query(str, int, float))
    assert len(results) == 1
    entity, s, i, f = results[0]
    assert s == "pos1"
    assert i == 10
    assert f == 1.0


def test_query_no_match(world):
    results = list(world.query(int, float))
    assert len(results) == 1


def test_query_empty_world():
    w = World()
    results = list(w.query(str))
    assert results == []


# --- entity in yield ---

def test_query_yields_entity_first(world):
    results = list(world.query(str, int))
    for item in results:
        assert isinstance(item[0], Entity)


def test_query_entity_matches_real(world):
    results = list(world.query(str, int))
    entity_ids = {r[0].id for r in results}
    e1 = world.create_entity()
    world.add_component(e1, "x")
    world.add_component(e1, 99)
    new_results = list(world.query(str, int))
    found = any(r[0] == e1 and r[1] == "x" and r[2] == 99 for r in new_results)
    assert found


def test_query_entity_usable_for_get_component(world):
    results = list(world.query(str, int))
    for entity, s, i in results:
        extra = world.get_component(entity, str)
        assert extra == s


# --- component order matches requested types ---

def test_query_order_matches_types(world):
    results = list(world.query(int, str))
    for entity, i, s in results:
        assert isinstance(i, int)
        assert isinstance(s, str)


def test_query_order_reversed(world):
    r1 = list(world.query(str, int))
    r2 = list(world.query(int, str))
    assert len(r1) == len(r2)
    for (e1, s1, i1), (e2, i2, s2) in zip(r1, r2):
        assert e1 == e2
        assert s1 == s2
        assert i1 == i2


# --- missing component types ---

def test_query_type_not_in_world():
    w = World()
    e = w.create_entity()
    w.add_component(e, "val")
    results = list(w.query(str, float))
    assert results == []


def test_query_entity_missing_one_component(world):
    results = list(world.query(str, int, float))
    entity_ids = {r[0].id for r in results}
    e2_results = [r for r in results if r[1] == "pos2"]
    assert len(e2_results) == 0


# --- duplicate types guard ---

def test_query_duplicate_types_raises(world):
    with pytest.raises(ValueError, match="Duplicate"):
        world.query(str, str)


# --- query after mutation ---

def test_query_after_entity_destroyed(world):
    all_results = list(world.query(str, int))
    entity = all_results[0][0]
    world.destroy_entity(entity)
    new_results = list(world.query(str, int))
    assert all(r[0] != entity for r in new_results)


def test_query_after_component_removed(world):
    all_results = list(world.query(str, int))
    entity = all_results[0][0]
    world.remove_component(entity, int)
    new_results = list(world.query(str, int))
    assert all(r[0] != entity for r in new_results)


def test_query_after_component_added(world):
    e3_results = list(filter(lambda r: r[1] == "pos3", list(world.query(str, int))))
    assert len(e3_results) == 0
    e3 = [r[0] for r in list(world.query(str)) if r[1] == "pos3"][0]
    world.add_component(e3, 30)
    e3_results = list(filter(lambda r: r[1] == "pos3", list(world.query(str, int))))
    assert len(e3_results) == 1


# --- smallest-set optimisation ---

def test_query_uses_smallest_set():
    w = World()
    for i in range(100):
        e = w.create_entity()
        w.add_component(e, f"pos_{i}")
    for i in range(5):
        e = w.create_entity()
        w.add_component(e, f"pos_rare_{i}")
        w.add_component(e, i * 10)
    results = list(w.query(str, int))
    assert len(results) == 5


# --- __repr__ ---

def test_query_repr():
    w = World()
    q = w.query(str, int)
    assert "str" in repr(q)
    assert "int" in repr(q)


# --- single type with multiple entities ---

def test_query_single_type_all_returned():
    w = World()
    for i in range(10):
        e = w.create_entity()
        w.add_component(e, f"val_{i}")
    results = list(w.query(str))
    assert len(results) == 10


# --- lazy evaluation ---

def test_query_lazy_not_consumed():
    w = World()
    e = w.create_entity()
    w.add_component(e, "a")
    w.add_component(e, 1)
    q = w.query(str, int)
    w.add_component(e, 3.14)
    results = list(q)
    assert len(results) == 1
