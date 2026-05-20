from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Entity:
    """Basic entity identifier."""
    id: int
    generation: int
