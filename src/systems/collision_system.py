from src.core.ecs.system import System
from src.core.components import Position, Collider
from src.utils.spatial_hash import SpatialHashGrid

class CollisionSystem(System):
    """System for collision detection"""
    def __init__(self, cell_size: float = 64.0):
        self.grid = SpatialHashGrid(cell_size)

    def update(self, world) -> None:
        self.grid.clear()

        for entity, pos, col in world.query(Position, Collider):
            self.grid.insert(entity, pos.x, pos.y)

        for entity, pos, col in world.query(Position, Collider):
            candidates = self.grid.query_circle(pos.x, pos.y, col.radius, exclude=entity)

            for other in candidates:
                if other.id < entity.id:
                    continue    
                other_pos = world.get_component(other, Position)
                other_col = world.get_component(other, Collider)

                dx = pos.x - other_pos.x
                dy = pos.y - other_pos.y
                dist_sq = dx * dx + dy * dy
                min_dist = col.radius + other_col.radius
                if dist_sq <= min_dist * min_dist:
                    self._handle_collision(world, entity, other)

    def _handle_collision(self, world, entity1, entity2):
        pass