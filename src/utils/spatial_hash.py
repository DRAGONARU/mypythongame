from src.core.ecs.entity import Entity


class SpatialHashGrid:
    """Uniform spatial hash grid for broad-phase collision queries.

    Divides 2D space into square cells of fixed size. Each entity is
    stored in exactly one cell based on its centre position. Query
    methods return candidate entities from cells that overlap the
    requested region — narrow-phase distance checks are the caller's
    responsibility.

    Typical per-tick usage:
        grid.clear()
        for entity, pos in all_collidables:
            grid.insert(entity, pos.x, pos.y)
        for entity, pos in all_collidables:
            candidates = grid.query_circle(pos.x, pos.y, search_radius, exclude=entity)
    """

    def __init__(self, cell_size: float):
        """Initialise the grid.

        Args:
            cell_size: Side length of each square cell in world units.
                Should be >= maximum collider radius so that each entity
                fits in a single cell.
        """
        self._cell_size = cell_size
        self._cells: dict[tuple[int, int], set[Entity]] = {}
        self._entity_cells: dict[Entity, tuple[int, int]] = {}

    def insert(self, entity: Entity, x: float, y: float) -> None:
        """Place an entity into the cell corresponding to its centre.

        If the entity was already inserted, it is moved to the new cell.

        Args:
            entity: The entity to insert.
            x: World x-coordinate of the entity centre.
            y: World y-coordinate of the entity centre.
        """
        cell = (int(x // self._cell_size), int(y // self._cell_size))
        
        old_cell = self._entity_cells.get(entity)
        if old_cell is not None and old_cell != cell:
            self._cells[old_cell].discard(entity)
            if not self._cells[old_cell]:
                del self._cells[old_cell]
        
        self._cells.setdefault(cell, set()).add(entity)
        self._entity_cells[entity] = cell

    def remove(self, entity: Entity) -> bool:
        """Remove an entity from the grid.

        Empty cells are deleted to prevent memory leaks during frequent
        spawn/despawn cycles.

        Args:
            entity: The entity to remove.

        Returns:
            True if the entity was found and removed, False otherwise.
        """
        cell = self._entity_cells.pop(entity, None)
        if cell is None:
            return False
        self._cells[cell].discard(entity)
        if not self._cells[cell]:
            del self._cells[cell]
        return True

    def update(self, entity: Entity, x: float, y: float) -> None:
        """Move an entity to a new position (remove + insert).

        Safe to call even if the entity is not currently in the grid.

        Args:
            entity: The entity to move.
            x: New world x-coordinate.
            y: New world y-coordinate.
        """
        self.remove(entity)
        self.insert(entity, x, y)

    def query_circle(self, x: float, y: float, radius: float, exclude: Entity | None = None) -> set[Entity]:
        """Return all entities in cells that overlap the given circle.

        This is a broad-phase query — it returns candidates from cells
        whose bounding box intersects the circle. The caller is
        responsible for narrow-phase distance checks.

        Args:
            x: Centre x of the query circle.
            y: Centre y of the query circle.
            radius: Radius of the query circle in world units.
            exclude: Optional entity to remove from the result
                (typically the querying entity itself).

        Returns:
            Set of candidate entities.
        """
        center_cx = int(x // self._cell_size)
        center_cy = int(y // self._cell_size)
        cell_radius = int(radius // self._cell_size) + 1

        result: set[Entity] = set()
        for cx in range(center_cx - cell_radius, center_cx + cell_radius + 1):
            for cy in range(center_cy - cell_radius, center_cy + cell_radius + 1):
                cell = self._cells.get((cx, cy))
                if cell is None:
                    continue
                result.update(cell)

        if exclude is not None:
            result.discard(exclude)

        return result

    def query_rect(self, x: float, y: float, half_width: float, half_height: float, exclude: Entity | None = None) -> set[Entity]:
        """Return all entities in cells that overlap the given axis-aligned rectangle.

        The rectangle is defined by its centre (x, y) and half-extents.
        This is a broad-phase query — the caller is responsible for
        narrow-phase overlap checks.

        Args:
            x: Centre x of the query rectangle.
            y: Centre y of the query rectangle.
            half_width: Half-width (extent along x) in world units.
            half_height: Half-height (extent along y) in world units.
            exclude: Optional entity to remove from the result.

        Returns:
            Set of candidate entities.
        """
        min_cx = int((x - half_width) // self._cell_size)
        max_cx = int((x + half_width) // self._cell_size)
        min_cy = int((y - half_height) // self._cell_size)
        max_cy = int((y + half_height) // self._cell_size)

        result: set[Entity] = set()
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                cell = self._cells.get((cx, cy))
                if cell is None:
                    continue
                result.update(cell)

        if exclude is not None:
            result.discard(exclude)
        return result
    
    def clear(self) -> None:
        """Remove all entities and cells from the grid.

        Called at the start of each tick before re-populating.
        """
        self._cells.clear()
        self._entity_cells.clear()

    def __repr__(self) -> str:
        """Return a concise string representation of the grid."""
        return f"SpatialHashGrid(cell_size={self._cell_size}, cells={len(self._cells)}, entities={len(self._entity_cells)})"
    