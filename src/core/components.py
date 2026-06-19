from dataclasses import dataclass
from src.core.ecs.entity import Entity


@dataclass(slots=True)
class Position:
    """ Position in 2D space. """
    x: float
    y: float

@dataclass(slots=True)
class Velocity:
    """ Velocity in 2D space. """
    x: float
    y: float

@dataclass(slots=True)
class Collider:
    """ Collider in 2D space. """
    radius: float
    
@dataclass(slots=True)
class Health:
    """ Health and maximum health. """
    value: int
    max_value: int
    
@dataclass(slots=True)
class Mana:
    """ Mana and maximum mana. """
    value: int
    max_value: int

@dataclass(slots=True)
class TimeMana:
    """ Time mana and maximum time mana. """
    value: int
    max_value: int

@dataclass(slots=True)
class Experience:
    """ current experience and next level experience. """
    level: int
    current: int
    to_next: int

@dataclass(slots=True)
class TimeAffected:
    """Local timescale multiplier"""
    scale: float = 1.0

@dataclass(slots=True)
class Owner:
    """Entity that owns the component"""
    entity: Entity

@dataclass(slots=True)
class Lifetime:
    """Ticks until the component is destroyed"""
    remaining_ticks: int

@dataclass(slots=True)
class Knife:
    """Knife projectile type"""
    knife_type: str
    damage: int
    speed: float


@dataclass(slots=True)
class Reflective:
    """Tracks remaining bounces for reflective knives."""
    bounces_remaining: int

@dataclass(slots=True)
class Delayed:
    """Tracks remaining ticks until knife activation."""
    activate_ticks: int

LAYER_PLAYER     = 1 << 0
LAYER_ENEMY      = 1 << 1
LAYER_KNIFE      = 1 << 2
LAYER_PROJECTILE = 1 << 3
LAYER_PICKUP     = 1 << 4
LAYER_WALL       = 1 << 5

@dataclass(slots=True)
class CollisionFilter:
    """Filters entities for collision."""
    layer: int
    mask: int