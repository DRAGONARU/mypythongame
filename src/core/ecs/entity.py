from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Entity:
    """Lightweight entity identifier used by the ECS World.

    Consists of an id and a generation. Two Entities with the same id
    but different generations refer to different logical entities,
    which prevents dangling references when an entity is destroyed
    and its id is reused.

    Frozen dataclass: immutable, hashable, usable as dict key.
    """

    id: int
    generation: int
