from typing import Iterator
from .entity import Entity


class Query:
    """Lazy iterator over entities matching a set of component types.

    Given a World and a tuple of component types, iterates over all
    entities that possess every requested type and yields tuples of
    their component values in the same order as the requested types.

    Optimisation: the smallest SparseSet is used as the driving set
    so that the outer loop has the fewest iterations. All other types
    are checked via O(1) SparseSet.get per candidate entity.

    Example:
        for entity, pos, vel in world.query(Position, Velocity):
            pos.x += vel.x
    """

    def __init__(self, world: 'World', component_types: tuple[type, ...]):
        """
        Args:
            world: The World registry to query against.
            component_types: Tuple of component types an entity must have.
        """
        self._world = world
        self._component_types = component_types

        if len(set(component_types)) != len(component_types):
            raise ValueError("Duplicate component types in query")

    def __iter__(self) -> Iterator[tuple[Entity, ...]]:
        """Yield tuples of component values for matching entities.

        Steps:
            1. Find the SparseSet with the fewest entries (driving set).
            2. Iterate over its (Entity, value) pairs.
            3. For each entity, check all other requested types.
            4. If all are present, assemble a result tuple in the
               order of component_types and yield it.

        Yields:
            Tuple of component values ordered by component_types.
        """
        first_set = None
        first_type = None
        for component_type in self._component_types:
            sparse_set = self._world._components.get(component_type)
            if sparse_set is None:
                return
            if first_set is None or len(sparse_set) < len(first_set):
                first_set = sparse_set
                first_type = component_type

        other_types = tuple(t for t in self._component_types if t != first_type)
        type_to_index = {t: i for i, t in enumerate(self._component_types)}

        for entity, first_component in first_set.iter_with_entities():
            others = []
            for ct in other_types:
                comp = self._world._components[ct].get(entity)
                if comp is None:
                    break
                others.append(comp)
            else:
                result = [None] * len(self._component_types)
                result[type_to_index[first_type]] = first_component
                for ct, val in zip(other_types, others):
                    result[type_to_index[ct]] = val
                yield (entity, *result)

                
    def __repr__(self) -> str:
        type_names = ", ".join(t.__name__ for t in self._component_types)
        return f"Query({type_names})"