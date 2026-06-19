from src.core.ecs.world import World
from src.systems import MovementSystem, InputSystem, LifetimeSystem, CollisionSystem, CombatSystem
from src.core.game_loop import GameLoop

class Game:
    """Game class"""
    def __init__(self):
        self.world = World()
        self.systems = [
            InputSystem(),
            MovementSystem(),
            CollisionSystem(),
            CombatSystem(),
            LifetimeSystem(),
        ]
        self.loop = GameLoop(tick_fn = self._tick, render_fn = self._render)

    def _tick(self, dt: float) -> None:
        self.world.tick += 1
        for system in self.systems:
            system.update(self.world)
        self.world.events.clear()

    def _render(self, dt: float) -> None:
        pass

    def run(self) -> None:
        self.loop.start()

    def stop(self) -> None:
        self.loop.stop()