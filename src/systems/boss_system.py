import math
import pygame
from src.core.ecs.system import System
from src.core.components import (
    Boss, Enemy, Player, Position, Velocity, Collider, Health,
    TimeAffected, CollisionFilter, Projectile, Lifetime,
    LAYER_ENEMY, LAYER_PLAYER, LAYER_PROJECTILE, LAYER_KNIFE,
)
from config.config_params import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    BOSS_HP, BOSS_RADIUS, BOSS_SPEED,
    BOSS_PROJECTILE_SPEED, BOSS_PROJECTILE_DAMAGE, BOSS_PROJECTILE_RADIUS,
    BOSS_PROJECTILE_LIFETIME, BOSS_FIRE_COOLDOWN, BOSS_SPREAD_DEGREES,
    BOSS_MUSIC_PATH, USE_MUSIC, AMOUNT_OF_BOSSES,
)


class BossSystem(System):
    """Spawns the boss as the final encounter and handles its ranged attacks.

    The boss appears once all wave enemies have been spawned and cleared.
    It is a stationary turret that fires a 3-round spread (centre shot
    aimed at the player, flanking shots at +/- 20 degrees) on a cooldown.

    Music switches to a boss track when the boss spawns. Firing is
    suppressed during Time Stop so the boss cannot flood the arena with
    frozen projectiles.
    """

    def __init__(self, wave_spawner, time_system, screen_size: tuple[int, int] = (SCREEN_WIDTH, SCREEN_HEIGHT)):
        self._wave_spawner = wave_spawner
        self._time_system = time_system
        self._screen_size = screen_size
        self.boss_spawned: bool = False

    def update(self, world) -> None:
        if not self.boss_spawned:
            self._try_spawn_boss(world)
            return
        self._move_boss(world)
        self._fire(world)

    def _move_boss(self, world) -> None:
        """Move the boss slowly toward the player."""
        if self._time_system.current_scale <= 0.0:
            return
        player_pos = self._find_player_pos(world)
        if player_pos is None:
            return
        for entity, boss, pos, vel in world.query(Boss, Position, Velocity):
            dx = player_pos.x - pos.x
            dy = player_pos.y - pos.y
            dist = (dx * dx + dy * dy) ** 0.5 or 1.0
            vel.x = (dx / dist) * BOSS_SPEED
            vel.y = (dy / dist) * BOSS_SPEED

    def _try_spawn_boss(self, world) -> None:
        """Spawn the boss once all waves are spawned and no enemies remain."""
        if not self._wave_spawner.all_spawned:
            return
        for entity, enemy in world.query(Enemy):
            return
        for boss in range(AMOUNT_OF_BOSSES):
            self._spawn_boss(world)

    def _spawn_boss(self, world) -> None:
        """Create the boss entity at the screen centre and switch music."""
        boss = world.create_entity()
        cx = self._screen_size[0] / 2
        cy = self._screen_size[1] / 2
        world.add_component(boss, Position(x=cx, y=cy))
        world.add_component(boss, Velocity(x=0.0, y=0.0))
        world.add_component(boss, Collider(radius=BOSS_RADIUS))
        world.add_component(boss, Health(value=BOSS_HP, max_value=BOSS_HP))
        world.add_component(boss, Enemy())
        world.add_component(boss, Boss())
        world.add_component(boss, TimeAffected(scale=1.0))
        world.add_component(boss, CollisionFilter(layer=LAYER_ENEMY, mask=LAYER_PLAYER | LAYER_KNIFE))
        self.boss_spawned = True
        self._change_music()

    def _change_music(self) -> None:
        """Switch to the boss music track if music is enabled."""
        if not USE_MUSIC:
            return
        try:
            pygame.mixer.music.load(BOSS_MUSIC_PATH)
            pygame.mixer.music.play(loops=-1)
        except (pygame.error, FileNotFoundError):
            pass

    def _fire(self, world) -> None:
        """Each boss fires a 3-round spread at the player on its own cooldown."""
        if self._time_system.current_scale <= 0.0:
            return
        player_pos = self._find_player_pos(world)
        if player_pos is None:
            return
        for entity, boss, pos in world.query(Boss, Position):
            if boss.fire_cooldown > 0:
                boss.fire_cooldown -= 1
                continue
            base_angle = math.atan2(player_pos.y - pos.y, player_pos.x - pos.x)
            spread = math.radians(BOSS_SPREAD_DEGREES)
            for delta in (-spread, 0.0, spread):
                angle = base_angle + delta
                vx = math.cos(angle) * BOSS_PROJECTILE_SPEED
                vy = math.sin(angle) * BOSS_PROJECTILE_SPEED
                self._spawn_projectile(world, pos.x, pos.y, vx, vy)
            boss.fire_cooldown = BOSS_FIRE_COOLDOWN

    def _spawn_projectile(self, world, x: float, y: float, vx: float, vy: float) -> None:
        """Create a single boss projectile."""
        p = world.create_entity()
        world.add_component(p, Position(x=x, y=y))
        world.add_component(p, Velocity(x=vx, y=vy))
        world.add_component(p, Collider(radius=BOSS_PROJECTILE_RADIUS))
        world.add_component(p, Projectile(damage=BOSS_PROJECTILE_DAMAGE))
        world.add_component(p, Lifetime(remaining_ticks=BOSS_PROJECTILE_LIFETIME))
        world.add_component(p, TimeAffected(scale=1.0))
        world.add_component(p, CollisionFilter(layer=LAYER_PROJECTILE, mask=LAYER_PLAYER))

    @staticmethod
    def _find_player_pos(world) -> Position | None:
        for entity, player, pos in world.query(Player, Position):
            return pos
        return None
