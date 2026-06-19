from dataclasses import dataclass
from src.core.ecs.entity import Entity

@dataclass(slots=True)
class CollisionEvent:
    """Event for collision between two entities"""
    a: Entity
    b: Entity
    tick: int