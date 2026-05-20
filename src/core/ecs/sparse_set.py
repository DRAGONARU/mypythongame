from typing import TypeVar, Generic
from сollections.abc import Iterator
from .entity import Entity

T = TypeVar('T')

class SparseSet(Generic[T]):
    """Sparse set for ECS component storage."""
    def __init__(self) -> None:
        self._sparse : list[int] = []
        self._dense : list[int] = []
        self._values : list[T] = []
        self._generations : list[int] = []

    def insert(self, entity: Entity, value: T) -> bool:
        """Inserts entity into the set.
        Returns True if the entity was inserted, False if it already existed."""

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
        """Removes entity from the set.
        Returns True if the entity was removed, False if it didn't exist."""
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
        """Returns value associated with the entity, or None if it doesn't exist."""
        eid = entity.id
        gen = entity.generation

        if eid >= len(self._sparse) or self._sparse[eid] == -1:
            return None

        if self._generations[eid] != gen:
            return None
        
        dense_idx = self._sparse[eid]
        
        return self._values[dense_idx]
    
    def contains(self, entity: Entity) -> bool:
        """Returns True if the entity exists in the set, False otherwise."""
        eid = entity.id
        gen = entity.generation

        if eid >= len(self._sparse) or self._sparse[eid] == -1:
            return False
        
        return self._generations[eid] == gen
    
    def __len__(self) -> int:
        """Returns number of entities in the set."""
        return len(self._dense)

    def __iter__(self) -> Iterator[T]:
        """Returns iterator over values in the set."""
        for i in range(len(self._dense)):
            yield self._values[i]

    def iter_with_entities(self) -> Iterator[tuple[Entity, T]]:
        """Returns iterator over (entity, value) pairs in the set."""
        for i in range(len(self._dense)):
            eid = self._dense[i]
            gen = self._generations[eid]
            yield (Entity(id=eid, generation=gen), self._values[i])