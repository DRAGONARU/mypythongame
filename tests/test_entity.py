import pytest
from src.core.ecs.entity import Entity


def test_creation():
    entity = Entity(id=1, generation=2)
    assert entity.id == 1
    assert entity.generation == 2

def test_equality_same():
    entity1 = Entity(id=1, generation=2)
    entity2 = Entity(id=1, generation=2)
    assert entity1 == entity2

def test_equality_diff_id():
    entity1 = Entity(id=0, generation=2)
    entity2 = Entity(id=1, generation=2)
    assert entity1 != entity2

def test_equality_diff_gen():
    entity1 = Entity(id=1, generation=0)
    entity2 = Entity(id=1, generation=2)
    assert entity1 != entity2

def test_hasable_dict_key():
    e = Entity(id=5, generation=0)
    d = {e: "test_val"}
    assert d[Entity(id=5, generation=0)] == "test_val"

def test_hashable_set():
    s = {Entity(id=5, generation=0), Entity(id=5, generation=0)}
    assert len(s) == 1
    s.add(Entity(id=6, generation=0))
    assert len(s) == 2
    s.add(Entity(id=5, generation=0))
    assert len(s) == 2

def test_frozen_immutable():
    e = Entity(id=5, generation=0)
    with pytest.raises(AttributeError):
        e.id = 10
    with pytest.raises(AttributeError):
        e.generation = 10

def test_no_dict():
    e = Entity(id=5, generation=0)
    assert not hasattr(e, "__dict__")