from dataclasses import dataclass
from src.core.ecs.entity import Entity
from src.core.ecs.world import World
from src.core.ecs.sparse_set import SparseSet
import copy


@dataclass(slots=True)
class WorldSnapshot:
    """Deep-capturable snapshot of full World state at one tick.

    Stores shallow copies of every component of every live entity,
    plus entity bookkeeping (generations, free_ids, next_id) so the
    World can be fully restored.
    """
    
    tick: int
    components: dict[type, list[tuple[Entity, object]]]
    generations: list[int]
    free_ids: list[int]
    next_id: int
    alive: int

    @classmethod
    def capture(cls, world: World):
        components = {}
        for comp_type, sparse_set in world._components.items():
            components[comp_type] = [(e, copy.copy(comp)) for e, comp in sparse_set.iter_with_entities()]
        gen = world._generations.copy()
        free = world._free_ids.copy()
        next_id = world._next_id
        alive = world._alive
        return cls(tick=world.tick, components=components, generations=gen, free_ids=free, next_id=next_id, alive=alive)

    def restore(self, world: World) -> None:
        world.tick = self.tick
        world._components = {}
        for comp_type, pairs in self.components.items():
            ss = SparseSet()
            for e, comp in pairs:
                ss.insert(e, copy.copy(comp))
            world._components[comp_type] = ss

        world._generations = self.generations.copy()
        world._free_ids = self.free_ids.copy()
        world._next_id = self.next_id
        world._alive = self.alive

class SnapshotBuffer:
    """Ring buffer of WorldSnapshots, one per tick, capacity ticks.

    Stores the last `capacity` ticks of world state. capture() adds
    the current world state; restore(tick) reverts the world to a
    past tick. Oldest snapshots are overwritten when capacity is
    exceeded.

    Attributes:
        capacity: Max number of ticks stored (e.g. 240 = 2 seconds at 120Hz).
    """

    def __init__(self, capacity: int = 240):
        self.capacity = capacity
        self._buffer: list[WorldSnapshot | None] = [None] * capacity
        self._head: int = 0
        self._count: int = 0
        self._latest_tick: int | None = None

    def capture(self, world: World) -> None:
        snapshot = WorldSnapshot.capture(world)
        self._buffer[self._head] = snapshot
        self._head = (self._head + 1) % self.capacity
        self._count = min(self._count + 1, self.capacity)
        self._latest_tick = snapshot.tick
        

    def restore(self, world: World, tick: int) -> bool:
        if self._count == 0:
            return False
        oldest = self.oldest_tick()
        latest = self.latest_tick()
        if tick < oldest or tick > latest:
            return False
        offset = tick - oldest
        idx = (self._head - self._count + offset) % self.capacity
        snapshot = self._buffer[idx]
        if snapshot is None or snapshot.tick != tick:
            return False
        snapshot.restore(world)
        self._count = offset + 1
        self._head = (idx + 1) % self.capacity
        self._latest_tick = tick
        return True
    
    def latest_tick(self) -> int | None:
        return self._latest_tick if self._count > 0 else None

    def oldest_tick(self) -> int | None:
        if self._count == 0:
            return None
        if self._count < self.capacity:
            return self._buffer[0].tick
        return self._buffer[self._head].tick

    def can_rewind(self, ticks_back: int) -> bool:
        latest = self.latest_tick()
        if latest is None:
            return False
        return latest - ticks_back >= self.oldest_tick()