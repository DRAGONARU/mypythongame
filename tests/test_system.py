from src.core.ecs.world import World
from src.core.ecs.system import System
from src.core.ecs.entity import Entity
import pytest


# --- abstract class enforcement ---

def test_cannot_instantiate_system():
    with pytest.raises(TypeError):
        System()


def test_subclass_without_update_cannot_instantiate():
    class BadSystem(System):
        pass

    with pytest.raises(TypeError):
        BadSystem()


def test_subclass_with_update_instantiates():
    class GoodSystem(System):
        def update(self, world: World) -> None:
            pass

    s = GoodSystem()
    assert isinstance(s, System)


# --- update receives world ---

def test_update_receives_world():
    class SpySystem(System):
        received_world = None

        def update(self, world: World) -> None:
            SpySystem.received_world = world

    w = World()
    s = SpySystem()
    s.update(w)
    assert SpySystem.received_world is w


# --- system interacts with world: read ---

def test_system_reads_components():
    class ReadSystem(System):
        result = None

        def update(self, world: World) -> None:
            ReadSystem.result = list(world.query(str, int))

    w = World()
    e = w.create_entity()
    w.add_component(e, "hello")
    w.add_component(e, 42)
    ReadSystem().update(w)
    assert len(ReadSystem.result) == 1


# --- system interacts with world: write ---

def test_system_modifies_components():
    class ModifySystem(System):
        def update(self, world: World) -> None:
            for entity, s, i in world.query(str, int):
                world.add_component(entity, s + "_modified")
                world.add_component(entity, i * 2)

    w = World()
    e = w.create_entity()
    w.add_component(e, "val")
    w.add_component(e, 5)
    ModifySystem().update(w)
    assert w.get_component(e, str) == "val_modified"
    assert w.get_component(e, int) == 10


# --- system creates entities ---

def test_system_creates_entities():
    class SpawnSystem(System):
        def update(self, world: World) -> None:
            e = world.create_entity()
            world.add_component(e, "spawned")

    w = World()
    SpawnSystem().update(w)
    results = list(w.query(str))
    assert len(results) == 1
    assert results[0][1] == "spawned"


# --- system destroys entities ---

def test_system_destroys_entities():
    class CleanupSystem(System):
        def update(self, world: World) -> None:
            for entity, s in list(world.query(str)):
                if s == "remove_me":
                    world.destroy_entity(entity)

    w = World()
    e1 = w.create_entity()
    w.add_component(e1, "keep")
    e2 = w.create_entity()
    w.add_component(e2, "remove_me")
    CleanupSystem().update(w)
    assert w.get_component(e1, str) == "keep"
    assert w.get_component(e2, str) is None


# --- multiple systems in sequence ---

def test_systems_in_sequence():
    class AddSystem(System):
        def update(self, world: World) -> None:
            for entity, s in world.query(str):
                world.add_component(entity, len(s))

    class DoubleSystem(System):
        def update(self, world: World) -> None:
            for entity, i in world.query(int):
                world.add_component(entity, i * 2)

    w = World()
    e = w.create_entity()
    w.add_component(e, "hello")
    AddSystem().update(w)
    assert w.get_component(e, int) == 5
    DoubleSystem().update(w)
    assert w.get_component(e, int) == 10


# --- system is stateless ---

def test_system_stateless():
    class CounterSystem(System):
        count = 0

        def update(self, world: World) -> None:
            CounterSystem.count = len(list(world.query(str)))

    w1 = World()
    e1 = w1.create_entity()
    w1.add_component(e1, "a")
    w2 = World()
    e2a = w2.create_entity()
    w2.add_component(e2a, "x")
    e2b = w2.create_entity()
    w2.add_component(e2b, "y")

    s = CounterSystem()
    s.update(w1)
    assert CounterSystem.count == 1
    s.update(w2)
    assert CounterSystem.count == 2


# --- isinstance check ---

def test_isinstance_system():
    class MySystem(System):
        def update(self, world: World) -> None:
            pass

    assert isinstance(MySystem(), System)


# --- systems list pattern ---

def test_systems_list_iteration():
    class SysA(System):
        def update(self, world: World) -> None:
            for entity, s in world.query(str):
                world.add_component(entity, s + "_a")

    class SysB(System):
        def update(self, world: World) -> None:
            for entity, s in world.query(str):
                world.add_component(entity, s + "_b")

    w = World()
    e = w.create_entity()
    w.add_component(e, "val")

    systems: list[System] = [SysA(), SysB()]
    for system in systems:
        system.update(w)

    assert w.get_component(e, str) == "val_a_b"
