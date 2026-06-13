from src.core.ecs.entity import Entity
from src.core.ecs.sparse_set import SparseSet
import pytest

@pytest.fixture
def ss():
    return SparseSet()


def _e(eid, gen=0):
    return Entity(id=eid, generation=gen)

def test_insert_new(ss):
    assert ss.insert(_e(0), "a") is True
    assert len(ss) == 1


def test_insert_update_same_generation(ss):
    ss.insert(_e(0), "a")
    assert ss.insert(_e(0), "b") is True
    assert ss.get(_e(0)) == "b"
    assert len(ss) == 1


def test_insert_stale_generation_rejected(ss):
    ss.insert(_e(0, gen=0), "a")
    assert ss.insert(_e(0, gen=1), "b") is False
    assert ss.get(_e(0, gen=0)) == "a"


def test_insert_large_eid_extends_sparse(ss):
    ss.insert(_e(100), "far")
    assert len(ss) == 1
    assert ss.get(_e(100)) == "far"


def test_insert_multiple(ss):
    ss.insert(_e(0), "a")
    ss.insert(_e(1), "b")
    ss.insert(_e(2), "c")
    assert len(ss) == 3


def test_get_existing(ss):
    ss.insert(_e(5), "val")
    assert ss.get(_e(5)) == "val"


def test_get_absent(ss):
    assert ss.get(_e(0)) is None


def test_get_stale_generation(ss):
    ss.insert(_e(0, gen=0), "a")
    assert ss.get(_e(0, gen=1)) is None


def test_get_after_remove(ss):
    ss.insert(_e(0), "a")
    ss.remove(_e(0))
    assert ss.get(_e(0)) is None


def test_contains_existing(ss):
    ss.insert(_e(0), "a")
    assert ss.contains(_e(0)) is True


def test_contains_absent(ss):
    assert ss.contains(_e(0)) is False


def test_contains_stale_generation(ss):
    ss.insert(_e(0, gen=0), "a")
    assert ss.contains(_e(0, gen=1)) is False


def test_remove_existing(ss):
    ss.insert(_e(0), "a")
    assert ss.remove(_e(0)) is True
    assert len(ss) == 0


def test_remove_absent(ss):
    assert ss.remove(_e(0)) is False


def test_remove_stale_generation(ss):
    ss.insert(_e(0, gen=0), "a")
    assert ss.remove(_e(0, gen=1)) is False
    assert len(ss) == 1


def test_remove_double(ss):
    ss.insert(_e(0), "a")
    ss.remove(_e(0))
    assert ss.remove(_e(0)) is False


def test_remove_middle_preserves_last(ss):
    ss.insert(_e(0), "a")
    ss.insert(_e(1), "b")
    ss.insert(_e(2), "c")
    ss.remove(_e(0))
    assert len(ss) == 2
    assert ss.get(_e(1)) == "b"
    assert ss.get(_e(2)) == "c"
    assert ss.get(_e(0)) is None


def test_remove_first_of_two(ss):
    ss.insert(_e(0), "a")
    ss.insert(_e(1), "b")
    ss.remove(_e(0))
    assert len(ss) == 1
    assert ss.get(_e(1)) == "b"


def test_remove_last_of_three(ss):
    ss.insert(_e(0), "a")
    ss.insert(_e(1), "b")
    ss.insert(_e(2), "c")
    ss.remove(_e(2))
    assert len(ss) == 2
    assert ss.get(_e(0)) == "a"
    assert ss.get(_e(1)) == "b"


def test_iter_values(ss):
    ss.insert(_e(0), "a")
    ss.insert(_e(1), "b")
    assert list(ss) == ["a", "b"]


def test_iter_after_remove(ss):
    ss.insert(_e(0), "a")
    ss.insert(_e(1), "b")
    ss.insert(_e(2), "c")
    ss.remove(_e(1))
    result = list(ss)
    assert "a" in result
    assert "c" in result
    assert "b" not in result


def test_iter_with_entities(ss):
    ss.insert(_e(0, gen=0), "a")
    ss.insert(_e(3, gen=0), "b")
    pairs = list(ss.iter_with_entities())
    assert pairs[0] == (Entity(id=0, generation=0), "a")
    assert pairs[1] == (Entity(id=3, generation=0), "b")


def test_iter_empty(ss):
    assert list(ss) == []


def test_generation_cycle(ss):
    e1 = _e(0, gen=0)
    ss.insert(e1, "first")
    ss.remove(e1)

    e2 = _e(0, gen=1)
    ss.insert(e2, "second")
    assert ss.get(e1) is None
    assert ss.get(e2) == "second"
    assert len(ss) == 1