from src.core.ecs.world import World
from src.systems import MovementSystem, InputSystem, LifetimeSystem, CollisionSystem, CombatSystem, KnifeSystem, KnifeBounceSystem, EnemySystem, PlayerMovementSystem, SeparationSystem, RewindSystem, TimeSystem, PlayerGainSystem, WaveSpawner, SpellCardSystem, ProgressionSystem, BossSystem
from src.core.game_loop import GameLoop
from src.rendering.render import Renderer
from src.core.event_log import EventLog
from src.core.snapshots import SnapshotBuffer
from src.core.components import InputState, Player, TimeMana, Health, Enemy
from config.config_params import SCREEN_SIZE, REWIND_CAPACITY_TICKS, SNAPSHOT_CAPACITY, USE_MUSIC, MUSIC_PATH, MUSIC_VOLUME
import pygame


class Game:
    """Game class"""
    def __init__(self, screen_size: tuple[int, int] = SCREEN_SIZE):
        self.world = World()
        self.input_system = InputSystem()
        self.time_system = TimeSystem()
        self.wave_spawner = WaveSpawner(screen_size)
        self.boss_system = BossSystem(self.wave_spawner, self.time_system, screen_size)
        self.victory: bool = False
        self.systems = [
            self.input_system,
            PlayerMovementSystem(),
            KnifeSystem(),
            SpellCardSystem(),
            ProgressionSystem(),
            EnemySystem(),
            self.boss_system,
            MovementSystem(),
            SeparationSystem(),
            CollisionSystem(),
            CombatSystem(),
            KnifeBounceSystem(),
            LifetimeSystem(),
            PlayerGainSystem(self.time_system),
            self.wave_spawner,
        ]
        self._renderer = Renderer(screen_size)
        self.loop = GameLoop(tick_fn=self._tick, render_fn=self._render)
        self.rewind_system = RewindSystem()
        self.event_log = EventLog(capacity_ticks=REWIND_CAPACITY_TICKS)
        self.snapshot_buffer = SnapshotBuffer(capacity=SNAPSHOT_CAPACITY)
        self.world.event_log = self.event_log
        self._start_music()

    def _start_music(self) -> None:
        """Start looping background music if enabled and available."""
        if not USE_MUSIC:
            return
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(MUSIC_PATH)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(loops=-1)
        except (pygame.error, FileNotFoundError):
            pass

    def _tick(self, dt: float) -> None:
        if self._rewind():
            self._check_quit()
            return
        self.world.tick += 1
        self.event_log.begin_tick(self.world.tick)
        self.event_log.capture_fields(self.world)
        self.time_system.update(self.world)
        for system in self.systems:
            system.update(self.world)
        self.world.events.clear()
        self.snapshot_buffer.capture(self.world)
        self._check_quit()
        self._check_player_death()
        self._check_victory()

    def _check_player_death(self) -> None:
        """Stop the loop if the player's Health reaches zero."""
        for entity, player, health in self.world.query(Player, Health):
            if health.value <= 0:
                self.loop.stop()
            break

    def _check_victory(self) -> None:
        """Stop the loop once all waves, the boss included, are cleared."""
        if not self.wave_spawner.all_spawned:
            return
        if not self.boss_system.boss_spawned:
            return
        for entity, enemy in self.world.query(Enemy):
            return
        self.victory = True
        self.loop.stop()

    def _check_quit(self) -> None:
        """Stop the loop if ESC or Q is pressed."""
        input_state = self._find_input_state(self.world)
        if input_state is None:
            return
        keys = input_state.keys_pressed
        if keys and (keys[pygame.K_ESCAPE] or keys[pygame.K_q]):
            self.loop.stop()

    def _render(self, alpha: float) -> None:
        wave_progress = self._wave_progress()
        self._renderer.render(self.world, alpha, wave_progress)

    def _wave_progress(self) -> float:
        """Return the fraction of the wave cleared [0, 1]."""
        max_enemies = self.wave_spawner._max_enemies
        if max_enemies <= 0:
            return 0.0
        alive = 0
        for entity, enemy in self.world.query(Enemy):
            alive += 1
        killed = self.wave_spawner.total_spawned - alive
        return max(0.0, killed / max_enemies)

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
            rewound = self.rewind_system.update(self.world)
            return rewound
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
