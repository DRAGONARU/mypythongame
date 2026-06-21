"""Centralised tunable parameters for the game.

All gameplay/system constants live here so they can be tweaked in
one place during debugging and balancing. Source files import these
values instead of hardcoding their own.
"""


# --- Tick simulation ---

TICK_RATE: int = 60
FIXED_DT: float = 1.0 / TICK_RATE
MAX_TICKS_PER_FRAME: int = 5


# --- Rewind / Time history ---

REWIND_CAPACITY_TICKS: int = 240
SNAPSHOT_CAPACITY: int = 240
REWIND_DRAIN_PER_TICK: int = 3
REWIND_MAX_TICKS: int = 240


# --- Player ---

PLAYER_SPEED: float = 250.0 / TICK_RATE
PLAYER_RADIUS: float = 12.0
PLAYER_HP: int = 100
PLAYER_MANA: int = 100
PLAYER_TIME_MANA: int = 100
PLAYER_XP_TO_NEXT: int = 100


# --- Enemy ---

ENEMY_SPEED: float = 100.0 / TICK_RATE
ENEMY_RADIUS: float = 10.0
ENEMY_HP: int = 50
SPAWN_RING_RADIUS: float = 200.0
ARENA_ENEMY_COUNT: int = 120


# --- Knife ---

KNIFE_SPEED: float = 300.0 / TICK_RATE
KNIFE_DAMAGE: int = 25
KNIFE_LIFETIME: int = 240
KNIFE_RADIUS: float = 4.0
KNIFE_DELAYED_TICKS: int = 60
KNIFE_REFLECTIVE_BOUNCES: int = 3
KNIFE_SPAWN_COOLDOWN: int = 6


# --- Spatial hashing ---

COLLISION_CELL_SIZE: float = 20.0
SEPARATION_CELL_SIZE: float = 20.0


# --- Rendering / Window ---

SCREEN_WIDTH: int = 800
SCREEN_HEIGHT: int = 600
SCREEN_SIZE: tuple[int, int] = (SCREEN_WIDTH, SCREEN_HEIGHT)
WINDOW_TITLE: str = "Luna Dial Survivors"

BG_COLOR: tuple[int, int, int] = (20, 20, 30)
PLAYER_COLOR: tuple[int, int, int] = (80, 150, 255)
ENEMY_COLOR: tuple[int, int, int] = (220, 60, 60)
KNIFE_COLOR: tuple[int, int, int] = (240, 240, 240)
HEALTH_BAR_BG: tuple[int, int, int] = (60, 0, 0)
HEALTH_BAR_FG: tuple[int, int, int] = (0, 200, 0)

# --- Time ---

NORMAL = "normal"
SLOW = "slow"
TIME_STOP = "stop"
REWIND = "rewind"

SLOW_SCALE: float = 0.3
TIME_STOP_DRAIN: int = 2
SLOW_DRAIN: int = 1