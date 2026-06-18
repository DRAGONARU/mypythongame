from src.core.ecs.system import System
from src.core.components import Position, Velocity, TimeAffected
from src.core.ecs.world import World

class MovementSystem(System):
    """Movement system for entities with Position and Velocity components"""

    def update(self, world: World) -> None:
        for entity, pos, vel, time_affected in world.query(Position, Velocity, TimeAffected):
            pos.x += vel.x * time_affected.scale
            pos.y += vel.y * time_affected.scale