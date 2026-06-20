from src.core.ecs.world import World
from src.systems import MovementSystem, InputSystem, LifetimeSystem, CollisionSystem, CombatSystem, KnifeSystem, KnifeBounceSystem, EnemySystem, PlayerMovementSystem
from src.core.game_loop import GameLoop
from src.rendering.render import Renderer
import pygame
from src.core.components import InputState


class Game:
    """Game class"""
    def __init__(self, screen_size: tuple[int, int] = (800, 600)):
        self.world = World()
        self.systems = [
            InputSystem(),
            PlayerMovementSystem(),
            KnifeSystem(),
            EnemySystem(),
            MovementSystem(),
            CollisionSystem(),
            CombatSystem(),
            KnifeBounceSystem(),
            LifetimeSystem(),
        ]
        self._renderer = Renderer(screen_size, title="Luna Dial Survivors")
        self.loop = GameLoop(tick_fn = self._tick, render_fn = self._render)

    def _tick(self, dt: float) -> None:
        self.world.tick += 1
        for system in self.systems:
            system.update(self.world)
        self.world.events.clear()
        self._check_quit()

    def _check_quit(self) -> None:
        """Stop the loop if ESC or Q is pressed."""
        input_state = None
        for entity, state in self.world.query(InputState):
            input_state = state
            break
        if input_state is None:
            return
        keys = input_state.keys_pressed
        if keys and (keys[pygame.K_ESCAPE] or keys[pygame.K_q]):
            self.loop.stop()

    def _render(self, alpha: float) -> None:
        self._renderer.render(self.world, alpha)

    def run(self) -> None:
        self.loop.start()

    def stop(self) -> None:
        self.loop.stop()