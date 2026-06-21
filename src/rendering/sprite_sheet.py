import pygame


class SpriteSheet:
    """Loads a sprite sheet image and slices it into individual sprites.

    The sheet is a grid of equal-sized cells. Sprites are accessed
    by (column, row) index. Uses subsurface (zero-copy view into the
    source image) for fast slicing.
    """

    def __init__(self, path: str, cell_width: int = 0, cell_height: int = 0,
                 scale: float = 1.0, color_key: tuple[int, int, int] | None = None):
        """Load a sprite sheet from disk.

        Args:
            path: Path to the sprite sheet PNG.
            cell_width: Width of one grid cell in pixels. Set to 0 when
                using explicit rects via get_rect() instead of a grid.
            cell_height: Height of one grid cell in pixels. 0 = no grid.
            scale: Uniform scale factor (1.0 = original size).
            color_key: Transparent color (magenta etc), None for alpha.
        """
        self._sheet = pygame.image.load(path)
        if color_key is not None:
            self._sheet.set_colorkey(color_key)
        self._sheet = self._sheet.convert_alpha()
        self._cell_w = cell_width
        self._cell_h = cell_height
        self._scale = scale
        self._scaled_w = int(cell_width * scale) if cell_width else 0
        self._scaled_h = int(cell_height * scale) if cell_height else 0
        self._cols = self._sheet.get_width() // cell_width if cell_width else 0
        self._rows = self._sheet.get_height() // cell_height if cell_height else 0

    def get(self, col: int, row: int = 0) -> pygame.Surface:
        """Return the sprite at (col, row) as a scaled Surface.

        Returns:
            A new scaled Surface (independent copy, safe to blit).
        """
        rect = pygame.Rect(col * self._cell_w, row * self._cell_h,
                           self._cell_w, self._cell_h)
        sprite = self._sheet.subsurface(rect)
        if self._scale != 1.0:
            sprite = pygame.transform.scale(sprite, (self._scaled_w, self._scaled_h))
        return sprite

    def get_rect(self, x: int, y: int, w: int, h: int,
                 scale: float | None = None) -> pygame.Surface:
        """Return the sprite at an explicit pixel rect.

        Use this when sprites on the sheet have differing sizes: each
        sprite is defined by its own (x, y, w, h) instead of a uniform
        grid index.

        Args:
            x, y: Top-left of the sprite in source pixels.
            w, h: Width and height of the sprite in source pixels.
            scale: Optional per-sprite scale (defaults to the sheet scale).

        Returns:
            A scaled Surface (independent copy, safe to blit).
        """
        rect = pygame.Rect(x, y, w, h)
        sprite = self._sheet.subsurface(rect)
        s = self._scale if scale is None else scale
        if s != 1.0:
            sprite = pygame.transform.scale(sprite, (int(w * s), int(h * s)))
        return sprite

    def get_row(self, row: int) -> list[pygame.Surface]:
        """Return all sprites in a row (useful for animation frames)."""
        return [self.get(col, row) for col in range(self._cols)]

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def rows(self) -> int:
        return self._rows