from typing import TypeVar
from .sparse_set import SparseSet
from .entity import Entity
from .query import Query
import copy

T = TypeVar('T')


class World:
    """Central ECS registry that manages entities and their components.

    Responsibilities:
        - Create and destroy entities with generation handles.
        - Store components in per-type SparseSets for O(1) access.
        - Provide Query objects to iterate entities by component combination.

    Attributes:
        _components:  Mapping from component type to its SparseSet.
        _generations: Per-entity generation counter; incremented on destroy.
        _free_ids:    Stack of recycled entity ids available for reuse.
        _next_id:     Monotonically increasing id for new entities.
        _alive:       Number of currently living entities.
    """

    def __init__(self):
        self._components: dict[type, SparseSet] = {}
        self._generations: list[int] = []
        self._free_ids: list[int] = []
        self._next_id: int = 0
        self._alive: int = 0
        self.tick: int = 0
        self.events: list = []
        self.event_log = None

    def _is_alive(self, entity: Entity) -> bool:
        """Return True if the entity's generation matches the current World generation.

        An entity is considered alive if its id has been allocated and
        its generation has not been incremented (i.e. not destroyed).
        """
        eid = entity.id
        return eid < len(self._generations) and self._generations[eid] == entity.generation

    def create_entity(self) -> Entity:
        """Create a new entity and return its handle.

        Reuses a freed id (LIFO from _free_ids) if available,
        otherwise allocates a new id. The generation is read from
        _generations[eid] and baked into the returned Entity so that
        stale handles from previous incarnations are detectable.

        Returns:
            Entity handle with id and current generation.
        """
        if self._free_ids:
            eid = self._free_ids.pop()
        else:
            eid = self._next_id
            self._next_id += 1
            while len(self._generations) <= eid:
                self._generations.append(0)
        gen = self._generations[eid]
        self._alive += 1
        entity = Entity(id=eid, generation=gen)
        if self.event_log is not None and not self.event_log._undoing:
            self.event_log.record_created(entity)
        return entity

    def destroy_entity(self, entity: Entity) -> bool:
        """Destroy an entity, removing all its components.

        Increments the generation for the entity's id so that any
        existing Entity handles with the old generation become stale
        and will fail on future access.

        Returns:
            True if the entity was alive and destroyed, False if
            generation mismatch (already destroyed or never existed).
        """
        eid = entity.id
        gen = entity.generation

        if eid >= len(self._generations) or self._generations[eid] != gen:
            return False

        if self.event_log is not None and not self.event_log._undoing:
            comps = {}
            for comp_type, sparse_set in self._components.items():
                comp = sparse_set.get(entity)
                if comp is not None:
                    comps[comp_type] = copy.copy(comp)
            self.event_log.record_destroyed(entity, comps)

        for sparse_set in self._components.values():
            sparse_set.remove(entity)

        self._alive -= 1
        self._free_ids.append(eid)
        self._generations[eid] += 1

        return True

    def add_component(self, entity: Entity, value: T) -> bool:
        """Add or overwrite a component for the given entity.

        Components are stored in a per-type SparseSet, created on
        first use. If the entity already has a component of this type,
        its value is overwritten.

        Returns:
            True on success, False if generation mismatch.
        """
        if not self._is_alive(entity):
            return False

        component_type = type(value)
        existing = None
        if self.event_log is not None and not self.event_log._undoing:
            existing = self.get_component(entity, component_type)
            if existing is None:
                self.event_log.record_added(entity, component_type)
        if component_type not in self._components:
            self._components[component_type] = SparseSet()
        return self._components[component_type].insert(entity, value)

    def get_component(self, entity: Entity, component_type: type[T]) -> T | None:
        """Retrieve a component for the given entity by type.

        Returns:
            The component value, or None if the entity has no such
            component or generation mismatch.
        """

        if not self._is_alive(entity):
            return None

        sparse_set = self._components.get(component_type)
        if sparse_set is None:
            return None
        return sparse_set.get(entity)

    def remove_component(self, entity: Entity, component_type: type[T]) -> bool:
        """Remove a specific component type from the given entity.

        Returns:
            True if removed, False if the component was absent or
            generation mismatch.
        """
        
        if not self._is_alive(entity):
            return False

        sparse_set = self._components.get(component_type)
        if sparse_set is None:
            return False
        if self.event_log is not None and not self.event_log._undoing:
            existing = sparse_set.get(entity)
            if existing is not None:
                self.event_log.record_removed(entity, component_type, copy.copy(existing))
        return sparse_set.remove(entity)

    def query(self, *component_types: type) -> Query:
        """Return a Query over entities that have all specified component types.

        The Query lazily iterates on demand. The smallest SparseSet is
        chosen as the driving set to minimise iterations.

        Example:
            for entity, pos, vel in world.query(Position, Velocity):
                pos.x += vel.x
        """
        return Query(self, component_types)
