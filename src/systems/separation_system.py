from src.core.ecs.system import System
from src.core.components import Position, Collider, Enemy, TimeAffected
from src.utils.spatial_hash import SpatialHashGrid


class SeparationSystem(System):
    """Pushes overlapping enemies apart to prevent stacking.

    Enemies all target the player and tend to converge to a single
    point. Without separation this causes severe overlap and turns
    the broad-phase grid into O(n^2) within a single cell. This
    system runs a dedicated SpatialHashGrid pass over enemies only
    and resolves overlaps by moving both enemies apart along the
    center-to-center normal.

    Position is corrected directly (instantaneous), not via velocity,
    so the effect is independent of TimeAffected.scale. Lifecycle
    and collision events are not touched — separation is purely a
    positional correction that must not generate CollisionEvents
    (CombatSystem would otherwise waste cycles on enemy-enemy pairs).
    """

    def __init__(self, cell_size: float = 20.0):
        """Initialise the separation grid.

        Args:
            cell_size: Spatial hash cell size. Should be at least
                twice the largest enemy collider radius so that
                overlapping enemies fall within the 3x3 query window.
        """
        self.grid = SpatialHashGrid(cell_size)

    def update(self, world) -> None:
        self.grid.clear()

        enemies = []
        for entity, enemy, pos, col in world.query(Enemy, Position, Collider):
            self.grid.insert(entity, pos.x, pos.y)
            enemies.append((entity, pos, col))

        for entity, pos, col in enemies:
            candidates = self.grid.query_circle(pos.x, pos.y, col.radius * 2, exclude=entity)
            for other in candidates:
                if other.id <= entity.id:
                    continue
                other_pos = world.get_component(other, Position)
                other_col = world.get_component(other, Collider)
                if other_pos is None or other_col is None:
                    continue

                dx = pos.x - other_pos.x
                dy = pos.y - other_pos.y
                dist_sq = dx * dx + dy * dy
                min_dist = col.radius + other_col.radius
                if dist_sq >= min_dist * min_dist:
                    continue

                dist = dist_sq ** 0.5
                if dist > 0.0001:
                    nx = dx / dist
                    ny = dy / dist
                else:
                    nx = 1.0
                    ny = 0.0

                overlap = min_dist - dist
                push = overlap * 0.5
                pos.x += nx * push
                pos.y += ny * push
                other_pos.x -= nx * push
                other_pos.y -= ny * push
