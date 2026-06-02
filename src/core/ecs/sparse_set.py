from typing import TypeVar, Generic
from collections.abc import Iterator
from .entity import Entity

T = TypeVar('T')


class SparseSet(Generic[T]):
    """Sparse set for ECS component storage.

    Provides O(1) insert, get, remove (via swap-with-last trick)
    and O(N) dense iteration over live values with no holes or None checks.

    Internal layout:
        _sparse[eid]  -> dense index (-1 if absent)
        _dense[i]     -> entity id
        _values[i]    -> component value at the same dense index
        _generations  -> per-entity generation to detect stale references
    """

    def __init__(self) -> None:
        self._sparse: list[int] = []
        self._dense: list[int] = []
        self._values: list[T] = []
        self._generations: list[int] = []

    def insert(self, entity: Entity, value: T) -> bool:
        """Insert or update a component for the given entity.

        If the entity with matching id and generation already exists,
        its value is overwritten (update). If the id exists but the
        generation differs, the insert is rejected (stale reference).

        Returns:
            True on successful insert or update, False if generation mismatch.
        """
        eid = entity.id
        gen = entity.generation

        if eid >= len(self._sparse):
            self._sparse.extend([-1] * (eid - len(self._sparse) + 1))
            self._generations.extend([-1] * (eid - len(self._generations) + 1))
        if self._sparse[eid] != -1:
            if self._generations[eid] == gen:
                dense_idx = self._sparse[eid]
                self._values[dense_idx] = value
                return True
            else:
                return False

        dense_idx = len(self._dense)
        self._sparse[eid] = dense_idx
        self._dense.append(eid)
        self._values.append(value)
        self._generations[eid] = gen
        return True

    def remove(self, entity: Entity) -> bool:
        """Remove the component for the given entity using swap-with-last.

        The removed slot is replaced by the last element to keep the
        dense array compact, preserving O(1) removal and hole-free
        iteration.

        Returns:
            True if removed, False if the entity was not present or
            generation mismatch.
        """
        eid = entity.id
        gen = entity.generation

        if eid >= len(self._sparse) or self._sparse[eid] == -1:
            return False

        if self._generations[eid] != gen:
            return False

        dense_idx = self._sparse[eid]
        last_dense_idx = len(self._dense) - 1

        if dense_idx != last_dense_idx:
            last_id = self._dense[last_dense_idx]

            self._dense[dense_idx] = last_id
            self._values[dense_idx] = self._values[last_dense_idx]
            self._sparse[last_id] = dense_idx

        self._sparse[eid] = -1
        self._generations[eid] = -1

        self._dense.pop()
        self._values.pop()

        return True

    def get(self, entity: Entity) -> T | None:
        """Return the component value for the given entity.

        Returns:
            The stored value, or None if the entity is absent or
            generation mismatch.
        """
        eid = entity.id
        gen = entity.generation

        if eid >= len(self._sparse) or self._sparse[eid] == -1:
            return None

        if self._generations[eid] != gen:
            return None

        dense_idx = self._sparse[eid]

        return self._values[dense_idx]

    def contains(self, entity: Entity) -> bool:
        """Check whether the entity with matching generation exists in the set."""
        eid = entity.id
        gen = entity.generation

        if eid >= len(self._sparse) or self._sparse[eid] == -1:
            return False

        return self._generations[eid] == gen

    def __len__(self) -> int:
        """Return the number of live entities in the set."""
        return len(self._dense)

    def __iter__(self) -> Iterator[T]:
        """Iterate over all component values in dense order."""
        for i in range(len(self._dense)):
            yield self._values[i]

    def iter_with_entities(self) -> Iterator[tuple[Entity, T]]:
        """Iterate over (Entity, value) pairs in dense order.

        Useful when the caller needs to know which entity owns
        each component, e.g. during Query resolution.
        """
        for i in range(len(self._dense)):
            eid = self._dense[i]
            gen = self._generations[eid]
            yield (Entity(id=eid, generation=gen), self._values[i])
