from dataclasses import dataclass
from src.core.ecs.entity import Entity
from src.core.ecs.world import World
from src.core.components import TimeMana, Mana
from config.config_params import REWIND_CAPACITY_TICKS
import copy


@dataclass(slots=True)
class UndoEvent:
    """A reversible mutation recorded for rewind.

    kind:
        "field"     — component fields mutated in-place; old_value = copy.copy(comp) pre-mutation
        "added"     — component added; old_value = None (undo = remove)
        "removed"   — component removed; old_value = copy.copy(comp) (undo = re-add)
        "created"   — entity created; undo = destroy
        "destroyed" — entity destroyed; old_value = dict[type, copy.copy(comp)] of all its components
    """
    kind: str
    entity_id: int
    entity_gen: int
    component_type: type | None = None
    old_value: object | None = None


class EventLog:
    """Ring buffer of per-tick UndoEvents for reverse-replay rewind.

    Lifecycle events (create/destroy/add/remove) are recorded via
    record_* methods called by World hooks. Field mutations are
    captured by capture_fields() which shallow-copies every live
    component BEFORE systems run (the "field" events).

    undo_latest_tick(world) reverses all events of the most recent
    tick in reverse insertion order, restoring the pre-tick state.
    """

    def __init__(self, capacity_ticks: int = REWIND_CAPACITY_TICKS):
        self.capacity_ticks = capacity_ticks
        self._events: dict[int, list[UndoEvent]] = {}
        self._tick_order: list[int] = []
        self._current_tick: int | None = None
        self._undoing: bool = False

    def begin_tick(self, tick: int) -> None:
        """Begin a new tick, creating an empty event bucket.

        Evicts the oldest tick's bucket if capacity is exceeded.
        """
        self._current_tick = tick
        self._events[tick] = []
        self._tick_order.append(tick)
        if len(self._tick_order) > self.capacity_ticks:
            old_tick = self._tick_order.pop(0)
            self._events.pop(old_tick, None)

    _NON_REWOUND_TYPES = (TimeMana, Mana)

    def capture_fields(self, world: World) -> None:
        """Record pre-tick copies of every live component as 'field' events.

        Must be called AFTER begin_tick and BEFORE systems run. Each
        component is shallow-copied so later in-place mutations can
        be reverted by overwriting with the pre-tick copy. Resource
        pools (TimeMana, Mana) are excluded so their drains persist
        across undo.
        """
        if self._current_tick is None:
            return
        bucket = self._events[self._current_tick]
        for comp_type, sparse_set in world._components.items():
            if comp_type in self._NON_REWOUND_TYPES:
                continue
            for entity, comp in sparse_set.iter_with_entities():
                bucket.append(UndoEvent(
                    kind="field",
                    entity_id=entity.id,
                    entity_gen=entity.generation,
                    component_type=comp_type,
                    old_value=copy.copy(comp),
                ))

    def record_created(self, entity: Entity) -> None:
        """Record that an entity was created this tick."""
        if self._current_tick is None:
            return
        self._events[self._current_tick].append(UndoEvent(
            kind="created",
            entity_id=entity.id,
            entity_gen=entity.generation,
        ))

    def record_destroyed(self, entity: Entity, components: dict[type, object]) -> None:
        """Record that an entity was destroyed this tick.

        Args:
            entity: The destroyed entity handle.
            components: Shallow copies of all the entity's components
                keyed by type, so undo can restore them.
        """
        if self._current_tick is None:
            return
        self._events[self._current_tick].append(UndoEvent(
            kind="destroyed",
            entity_id=entity.id,
            entity_gen=entity.generation,
            old_value=components,
        ))

    def record_added(self, entity: Entity, comp_type: type) -> None:
        """Record that a component was added to an entity this tick."""
        if self._current_tick is None:
            return
        self._events[self._current_tick].append(UndoEvent(
            kind="added",
            entity_id=entity.id,
            entity_gen=entity.generation,
            component_type=comp_type,
        ))

    def record_removed(self, entity: Entity, comp_type: type, old_value: object) -> None:
        """Record that a component was removed from an entity this tick.

        Args:
            old_value: Shallow copy of the removed component.
        """
        if self._current_tick is None:
            return
        self._events[self._current_tick].append(UndoEvent(
            kind="removed",
            entity_id=entity.id,
            entity_gen=entity.generation,
            component_type=comp_type,
            old_value=old_value,
        ))

    def undo_latest_tick(self, world: World) -> bool:
        """Undo all events of the most recent tick in reverse order.

        Restores the world to its pre-tick state and decrements
        world.tick. Returns False if there is nothing to undo.
        """
        latest = self.latest_tick()
        if latest is None:
            return False
        if self._undoing:
            return False

        self._undoing = True
        bucket = self._events[latest]
        for event in reversed(bucket):
            self._undo_event(world, event)

        self._events.pop(latest, None)
        self._tick_order.pop()
        self._current_tick = self.latest_tick()
        world.tick = latest - 1
        self._undoing = False
        return True

    def _undo_event(self, world: World, event: UndoEvent) -> None:
        """Apply the reverse of a single UndoEvent to the world."""
        if event.kind == "field":
            self._undo_field(world, event)
        elif event.kind == "added":
            self._undo_added(world, event)
        elif event.kind == "removed":
            self._undo_removed(world, event)
        elif event.kind == "created":
            self._undo_created(world, event)
        elif event.kind == "destroyed":
            self._undo_destroyed(world, event)

    def _undo_field(self, world: World, event: UndoEvent) -> None:
        """Restore a component to its pre-tick value."""
        entity = Entity(id=event.entity_id, generation=event.entity_gen)
        if not world._is_alive(entity):
            return
        old = copy.copy(event.old_value)
        world.add_component(entity, old)

    def _undo_added(self, world: World, event: UndoEvent) -> None:
        """Remove a component that was added this tick."""
        entity = Entity(id=event.entity_id, generation=event.entity_gen)
        world.remove_component(entity, event.component_type)

    def _undo_removed(self, world: World, event: UndoEvent) -> None:
        """Re-add a component that was removed this tick."""
        entity = Entity(id=event.entity_id, generation=event.entity_gen)
        if not world._is_alive(entity):
            return
        old = copy.copy(event.old_value)
        world.add_component(entity, old)

    def _undo_created(self, world: World, event: UndoEvent) -> None:
        """Destroy an entity that was created this tick."""
        entity = Entity(id=event.entity_id, generation=event.entity_gen)
        world.destroy_entity(entity)

    def _undo_destroyed(self, world: World, event: UndoEvent) -> None:
        """Recreate an entity that was destroyed this tick with its components."""
        eid = event.entity_id
        gen = event.entity_gen
        if eid < len(world._generations):
            world._generations[eid] = gen
        else:
            while len(world._generations) <= eid:
                world._generations.append(0)
            world._generations[eid] = gen
        if eid in world._free_ids:
            world._free_ids.remove(eid)
        world._alive += 1
        if eid >= world._next_id:
            world._next_id = eid + 1
        entity = Entity(id=eid, generation=gen)
        components = event.old_value or {}
        for comp_type, comp in components.items():
            world.add_component(entity, copy.copy(comp))

    def latest_tick(self) -> int | None:
        """Return the tick number of the most recent bucket, or None."""
        if self._tick_order:
            return self._tick_order[-1]
        return None

    def clear(self) -> None:
        """Remove all recorded events and ticks."""
        self._events = {}
        self._tick_order = []
        self._current_tick = None
        self._undoing = False
