from src.core.ecs.system import System
from src.core.components import Lifetime

class LifetimeSystem(System):
    """System for managing lifetimes of components"""

    def update(self, world) -> None:
        to_DESTROY = []

        for entity, lifetime in world.query(Lifetime):
            lifetime.remaining_ticks -= 1
            if lifetime.remaining_ticks <= 0:
                to_DESTROY.append(entity)
        
        for entity in to_DESTROY:
            world.destroy_entity(entity)