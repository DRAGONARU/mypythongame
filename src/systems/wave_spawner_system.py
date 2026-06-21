import random
from src.core.ecs.system import System
from src.core.components import (
    Position, Velocity, Collider, Health, Enemy, TimeAffected, CollisionFilter,
    LAYER_ENEMY, LAYER_PLAYER, LAYER_KNIFE,
)
from config.config_params import (
    SCREEN_WIDTH, SCREEN_HEIGHT, ENEMY_RADIUS, ENEMY_HP,
    WAVE_SPAWN_COUNT, WAVE_SPAWN_COOLDOWN, WAVE_MAX_ENEMIES,
)


class WaveSpawner(System):
    """Spawns enemies at the screen edges in timed pulses.

    Every ``WAVE_SPAWN_COOLDOWN`` ticks a pulse of ``WAVE_SPAWN_COUNT``
    enemies is created at random positions along the screen border, up to
    a total of ``WAVE_MAX_ENEMIES`` for the whole run. Once every enemy
    has been spawned and none remain alive the run is considered won.
    """

    def __init__(self, screen_size: tuple[int, int] = (SCREEN_WIDTH, SCREEN_HEIGHT)):
        self._width, self._height = screen_size
        self._spawn_count: int = WAVE_SPAWN_COUNT
        self._cooldown: int = WAVE_SPAWN_COOLDOWN
        self._max_enemies: int = WAVE_MAX_ENEMIES
        self._cooldown_ticks: int = 0
        self.total_spawned: int = 0

    @property
    def all_spawned(self) -> bool:
        """True once the configured maximum has been spawned."""
        return self.total_spawned >= self._max_enemies

    def update(self, world) -> None:
        if self.all_spawned:
            return
        if self._cooldown_ticks > 0:
            self._cooldown_ticks -= 1
            return
        self._spawn_pulse(world)
        self._cooldown_ticks = self._cooldown

    def _spawn_pulse(self, world) -> None:
        """Spawn one pulse of enemies, capped by the remaining budget."""
        remaining = self._max_enemies - self.total_spawned
        count = min(self._spawn_count, remaining)
        for _ in range(count):
            x, y = self._random_edge_position()
            self._spawn_enemy(world, x, y)
            self.total_spawned += 1

    def _random_edge_position(self) -> tuple[float, float]:
        """Pick a random point on the screen border."""
        side = random.randint(0, 3)
        if side == 0:
            return random.uniform(0, self._width), 0.0
        if side == 1:
            return float(self._width), random.uniform(0, self._height)
        if side == 2:
            return random.uniform(0, self._width), float(self._height)
        return 0.0, random.uniform(0, self._height)

    def _spawn_enemy(self, world, x: float, y: float) -> None:
        """Create a single enemy entity at the given position."""
        enemy = world.create_entity()
        world.add_component(enemy, Position(x=x, y=y))
        world.add_component(enemy, Velocity(x=0.0, y=0.0))
        world.add_component(enemy, Collider(radius=ENEMY_RADIUS))
        world.add_component(enemy, Health(value=ENEMY_HP, max_value=ENEMY_HP))
        world.add_component(enemy, Enemy())
        world.add_component(enemy, CollisionFilter(layer=LAYER_ENEMY, mask=LAYER_PLAYER | LAYER_KNIFE))
        world.add_component(enemy, TimeAffected(scale=1.0))
