from src.core.ecs.world import World
from src.systems import MovementSystem, InputSystem, LifetimeSystem, CollisionSystem, CombatSystem, KnifeSystem, KnifeBounceSystem, EnemySystem, PlayerMovementSystem, SeparationSystem, RewindSystem
from src.core.game_loop import GameLoop
from src.rendering.render import Renderer
from src.core.event_log import EventLog
from src.core.snapshots import SnapshotBuffer
from src.core.components import InputState, Player, TimeMana
from config.config_params import SCREEN_SIZE, REWIND_CAPACITY_TICKS, SNAPSHOT_CAPACITY
import pygame


class Game:
    """Game class"""
    def __init__(self, screen_size: tuple[int, int] = SCREEN_SIZE):
        self.world = World()
        self.input_system = InputSystem()
        self.systems = [
            self.input_system,
            PlayerMovementSystem(),
            KnifeSystem(),
            EnemySystem(),
            MovementSystem(),
            SeparationSystem(),
            CollisionSystem(),
            CombatSystem(),
            KnifeBounceSystem(),
            LifetimeSystem(),
        ]
        self._renderer = Renderer(screen_size)
        self.loop = GameLoop(tick_fn=self._tick, render_fn=self._render)
        self.rewind_system = RewindSystem()
        self.event_log = EventLog(capacity_ticks=REWIND_CAPACITY_TICKS)
        self.snapshot_buffer = SnapshotBuffer(capacity=SNAPSHOT_CAPACITY)
        self.world.event_log = self.event_log

    def _tick(self, dt: float) -> None:
        if self._rewind():
            self._check_quit()
            return
        self.world.tick += 1
        self.event_log.begin_tick(self.world.tick)
        self.event_log.capture_fields(self.world)
        for system in self.systems:
            system.update(self.world)
        self.world.events.clear()
        self.snapshot_buffer.capture(self.world)
        self._check_quit()

    def _check_quit(self) -> None:
        """Stop the loop if ESC or Q is pressed."""
        input_state = self._find_input_state(self.world)
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

    def _rewind(self) -> bool:
        """Run rewind if player holds R and has TimeMana, else stop.

        InputSystem is always invoked first so rewind can detect key
        release. Returns True if a rewind tick was performed (normal
        pipeline skipped), False otherwise.
        """
        self.input_system.update(self.world)
        input_state = self._find_input_state(self.world)
        if input_state is None:
            return False

        time_mana = self._find_player_time_mana(self.world)
        wants_rewind = (
            time_mana is not None
            and time_mana.value > 0
            and self._is_pressed(input_state, pygame.K_r)
        )

        if wants_rewind:
            self.rewind_system.start()
        elif self.rewind_system.active:
            self.rewind_system.stop()

        if self.rewind_system.active:
            self.rewind_system.update(self.world)
            return True
        return False

    @staticmethod
    def _is_pressed(input_state: InputState, key_code: int) -> bool:
        keys = input_state.keys_pressed
        return key_code < len(keys) and keys[key_code]

    def _find_player_time_mana(self, world) -> TimeMana | None:
        for entity, pl, t_mana in world.query(Player, TimeMana):
            return t_mana
        return None

    def _find_input_state(self, world) -> InputState | None:
        for entity, state in world.query(InputState):
            return state
        return None
