from src.core.ecs.system import System
from src.core.components import Lifetime

class LifetimeSystem(System):
    """System for managing lifetimes of components"""

    def update(self, world) -> None:
        to_destroy = []

        for entity, lifetime in world.query(Lifetime):
            lifetime.remaining_ticks -= 1
            if lifetime.remaining_ticks <= 0:
                to_destroy.append(entity)
        
        for entity in to_destroy:
            world.destroy_entity(entity)