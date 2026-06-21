from dataclasses import dataclass
from src.core.snapshots import WorldSnapshot, SnapshotBuffer
from src.core.ecs.entity import Entity
from src.core.ecs.world import World


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
    component_type: type | None
    old_value: object | None

class EventLog:
    """Ring buffer of per-tick UndoEvents for reverse-replay rewind.

    Lifecycle events (create/destroy/add/remove) are recorded via
    record_* methods called by World hooks. Field mutations are
    captured by capture_tick() which shallow-copies every live
    component BEFORE systems run (the "field" events).

    undo_latest_tick(world) reverses all events of the most recent
    tick in reverse insertion order, restoring the pre-tick state.
    """
    def __init__(self, capacity_ticks: int = 240):
        self.capacity_ticks = capacity_ticks

    def begin_tick(self, tick: int) -> None: ...
    def capture_fields(self, world: World) -> None: ...
    def record_created(self, entity: Entity) -> None: ...
    def record_destroyed(self, entity: Entity, components: dict[type, object]) -> None: ...
    def record_added(self, entity: Entity, comp_type: type) -> None: ...
    def record_removed(self, entity: Entity, comp_type: type, old_value: object) -> None: ...
    def undo_latest_tick(self, world: World) -> bool: ...
    def latest_tick(self) -> int | None: ...
    def clear(self) -> None: ...
