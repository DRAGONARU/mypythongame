import pygame
from src.core.ecs.world import World
from src.core.components import Position, Collider, Player, Enemy, Knife, Health

class Renderer:
    """Pygame renderer drawing entities as colored circles.

    Player: blue, Enemy: red, Knife: white. Health bar drawn above
    enemies. Not part of the logic system pipeline — called from
    Game._render with interpolation alpha.
    """

    BG_COLOR: tuple[int, int, int] = (20, 20, 30)
    PLAYER_COLOR: tuple[int, int, int] = (80, 150, 255)
    ENEMY_COLOR: tuple[int, int, int] = (220, 60, 60)
    KNIFE_COLOR: tuple[int, int, int] = (240, 240, 240)
    HEALTH_BAR_BG: tuple[int, int, int] = (60, 0, 0)
    HEALTH_BAR_FG: tuple[int, int, int] = (0, 200, 0)

    def __init__(self, screen_size: tuple[int, int] = (800, 600), title: str = "Luna Dial Survivors"):
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption(title)
        self.screen_size = screen_size

    def render(self, world: World, alpha: float) -> None:
        """Draw all visible entities to the screen.

        Args:
            world: World to read entity data from.
            alpha: Interpolation factor [0, 1) between logic ticks.
                Ignored for MVP (positions drawn as-is).
        """
        self.screen.fill(self.BG_COLOR)
        self._draw_enemies(world)
        self._draw_player(world)
        self._draw_knives(world)
        pygame.display.flip()

    def _draw_player(self, world: World) -> None:
        """Draw the player as a blue circle."""
        for entity, player, pos, col in world.query(Player, Position, Collider):
            pygame.draw.circle(self.screen, self.PLAYER_COLOR,
                            (int(pos.x), int(pos.y)), int(col.radius))

    def _draw_enemies(self, world: World) -> None:
        """Draw enemies as red circles with health bars."""
        for entity, enemy, pos, col, health in world.query(Enemy, Position, Collider, Health):
            DRAW_WITH_BAR = False
            pygame.draw.circle(self.screen, self.ENEMY_COLOR,
                            (int(pos.x), int(pos.y)), int(col.radius))
            if DRAW_WITH_BAR:
                bar_w = int(col.radius * 2)
                bar_h = 4
                bx = int(pos.x - col.radius)
                by = int(pos.y - col.radius - 8)
                pygame.draw.rect(self.screen, self.HEALTH_BAR_BG, (bx, by, bar_w, bar_h))
                ratio = max(0.0, health.value / health.max_value)
                pygame.draw.rect(self.screen, self.HEALTH_BAR_FG,
                                (bx, by, int(bar_w * ratio), bar_h))

    def _draw_knives(self, world: World) -> None:
        """Draw knives as small white circles."""
        for entity, knife, pos, col in world.query(Knife, Position, Collider):
            pygame.draw.circle(self.screen, self.KNIFE_COLOR,
                            (int(pos.x), int(pos.y)), max(2, int(col.radius)))