import math
import pygame
from src.core.ecs.world import World
from src.core.components import Position, Collider, Velocity, Player, Enemy, Knife, Health, Mana, TimeMana
from config.config_params import (
    SCREEN_SIZE, WINDOW_TITLE,
    BG_COLOR, PLAYER_COLOR, ENEMY_COLOR, KNIFE_COLOR,
    HEALTH_BAR_BG, HEALTH_BAR_FG,
    HUD_BAR_WIDTH, HUD_BAR_HEIGHT, HUD_BAR_GAP,
    HUD_MARGIN_X, HUD_MARGIN_Y,
    HUD_HP_COLOR, HUD_MANA_COLOR, HUD_TIMEMANA_COLOR,
    HUD_BG_COLOR, HUD_BORDER_COLOR,
    USE_BG_TILE, BG_TILE_PATH,
)
from src.rendering.sprite_sheet import SpriteSheet
from config.config_params import (
    USE_SPRITES, SPRITE_SHEETS,
    SPRITE_PLAYER, SPRITE_ENEMY, SPRITE_KNIFE,
)


class Renderer:
    """Pygame renderer drawing entities as sprites or colored circles.

    Sprites are loaded from one or more sprite sheets. Each sprite is
    defined by an explicit pixel rect (sheet, x, y, w, h) so that
    different-sized sprites on the same sheet are supported. Falls
    back to procedural circles when USE_SPRITES is False or a sprite
    is missing.
    """

    BG_COLOR: tuple[int, int, int] = BG_COLOR
    PLAYER_COLOR: tuple[int, int, int] = PLAYER_COLOR
    ENEMY_COLOR: tuple[int, int, int] = ENEMY_COLOR
    KNIFE_COLOR: tuple[int, int, int] = KNIFE_COLOR
    HEALTH_BAR_BG: tuple[int, int, int] = HEALTH_BAR_BG
    HEALTH_BAR_FG: tuple[int, int, int] = HEALTH_BAR_FG

    def __init__(self, screen_size: tuple[int, int] = SCREEN_SIZE, title: str = WINDOW_TITLE):
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption(title)
        self.screen_size = screen_size
        self._sprites = self._load_sprites()
        self._bg = self._make_background()

    def _make_background(self) -> pygame.Surface:
        """Build a screen-sized tiled background once."""
        bg = pygame.Surface(self.screen_size)
        if not USE_BG_TILE:
            bg.fill(self.BG_COLOR)
            return bg
        try:
            tile = pygame.image.load(BG_TILE_PATH).convert()
        except (FileNotFoundError, pygame.error):
            bg.fill(self.BG_COLOR)
            return bg
        tw, th = tile.get_size()
        for y in range(0, self.screen_size[1], th):
            for x in range(0, self.screen_size[0], tw):
                bg.blit(tile, (x, y))
        return bg

    def _load_sprites(self) -> dict[str, pygame.Surface]:
        """Load sprites from one or more sheets.

        Returns an empty dict in procedural mode (USE_SPRITES=False).
        Missing files fall back to procedural drawing per sprite.
        """
        if not USE_SPRITES:
            return {}
        sheets: dict[str, SpriteSheet] = {}
        sprites: dict[str, pygame.Surface] = {}
        for name, (path, color_key) in SPRITE_SHEETS.items():
            try:
                sheets[name] = SpriteSheet(path, 0, 0, color_key=color_key)
            except (FileNotFoundError, pygame.error):
                continue
        for sprite_name, (sheet_name, x, y, w, h) in (
            ("player", SPRITE_PLAYER),
            ("enemy", SPRITE_ENEMY),
            ("knife", SPRITE_KNIFE),
        ):
            sheet = sheets.get(sheet_name)
            if sheet is None:
                continue
            try:
                sprites[sprite_name] = sheet.get_rect(x, y, w, h)
            except ValueError:
                continue
        return sprites

    def render(self, world: World, alpha: float) -> None:
        """Draw all visible entities to the screen.

        Args:
            world: World to read entity data from.
            alpha: Interpolation factor [0, 1) between logic ticks.
                Ignored for MVP (positions drawn as-is).
        """
        self.screen.blit(self._bg, (0, 0))
        self._draw_enemies(world)
        self._draw_player(world)
        self._draw_knives(world)
        self._draw_hud(world)
        pygame.display.flip()

    def _draw_player(self, world: World) -> None:
        """Draw the player as a sprite (or blue circle fallback)."""
        for entity, player, pos, col in world.query(Player, Position, Collider):
            sprite = self._sprites.get("player")
            if sprite is not None:
                rect = sprite.get_rect(center=(int(pos.x), int(pos.y)))
                self.screen.blit(sprite, rect)
            else:
                pygame.draw.circle(self.screen, self.PLAYER_COLOR,
                                   (int(pos.x), int(pos.y)), int(col.radius))

    def _draw_enemies(self, world: World) -> None:
        """Draw enemies as sprites (or red circles) with health bars."""
        sprite = self._sprites.get("enemy")
        for entity, enemy, pos, col, health in world.query(Enemy, Position, Collider, Health):
            if sprite is not None:
                rect = sprite.get_rect(center=(int(pos.x), int(pos.y)))
                self.screen.blit(sprite, rect)
            else:
                pygame.draw.circle(self.screen, self.ENEMY_COLOR,
                                   (int(pos.x), int(pos.y)), int(col.radius))
            self._draw_health_bar(pos, col, health)

    def _draw_knives(self, world: World) -> None:
        """Draw knives as rotated sprites (or white circles fallback)."""
        sprite = self._sprites.get("knife")
        for entity, knife, pos, col, vel in world.query(Knife, Position, Collider, Velocity):
            if sprite is not None:
                angle = -math.degrees(math.atan2(vel.y, vel.x))
                rotated = pygame.transform.rotate(sprite, angle)
                rect = rotated.get_rect(center=(int(pos.x), int(pos.y)))
                self.screen.blit(rotated, rect)
            else:
                pygame.draw.circle(self.screen, self.KNIFE_COLOR,
                                   (int(pos.x), int(pos.y)), max(2, int(col.radius)))

    def _draw_health_bar(self, pos, col, health) -> None:
        """Draw a small health bar above an entity."""
        bar_w = int(col.radius * 2)
        bar_h = 4
        bx = int(pos.x - col.radius)
        by = int(pos.y - col.radius - 8)
        pygame.draw.rect(self.screen, self.HEALTH_BAR_BG, (bx, by, bar_w, bar_h))
        ratio = max(0.0, health.value / health.max_value)
        pygame.draw.rect(self.screen, self.HEALTH_BAR_FG,
                         (bx, by, int(bar_w * ratio), bar_h))

    def _draw_hud(self, world: World) -> None:
        """Draw the player's HP/Mana/TimeMana bars in the top-left corner."""
        hp = mana = tm = None
        for entity, player, health, mana, time_mana in world.query(
            Player, Health, Mana, TimeMana
        ):
            hp = health
            mana = mana
            tm = time_mana
            break
        if hp is None:
            return

        x = HUD_MARGIN_X
        y = HUD_MARGIN_Y
        self._draw_bar(x, y, hp.value, hp.max_value, HUD_HP_COLOR)
        y += HUD_BAR_HEIGHT + HUD_BAR_GAP
        self._draw_bar(x, y, mana.value, mana.max_value, HUD_MANA_COLOR)
        y += HUD_BAR_HEIGHT + HUD_BAR_GAP
        self._draw_bar(x, y, tm.value, tm.max_value, HUD_TIMEMANA_COLOR)

    def _draw_bar(self, x: int, y: int, value, max_value, color) -> None:
        """Draw one horizontal bar: background, fill, border."""
        pygame.draw.rect(self.screen, HUD_BG_COLOR,
                         (x, y, HUD_BAR_WIDTH, HUD_BAR_HEIGHT))
        ratio = max(0.0, min(1.0, value / max_value)) if max_value > 0 else 0.0
        fill_w = int(HUD_BAR_WIDTH * ratio)
        if fill_w > 0:
            pygame.draw.rect(self.screen, color, (x, y, fill_w, HUD_BAR_HEIGHT))
        pygame.draw.rect(self.screen, HUD_BORDER_COLOR,
                         (x, y, HUD_BAR_WIDTH, HUD_BAR_HEIGHT), 1)