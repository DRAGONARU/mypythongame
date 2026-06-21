"""Centralised tunable parameters for the game.

All gameplay/system constants live here so they can be tweaked in
one place during debugging and balancing. Source files import these
values instead of hardcoding their own.
"""


# --- Tick simulation ---

TICK_RATE: int = 120
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
PLAYER_TIME_MANA: int = 500
PLAYER_XP_TO_NEXT: int = 100
PLAYER_HP_REGEN: int = 2
PLAYER_MANA_REGEN: int = 2
PLAYER_TIME_MANA_REGEN: int = 50
COOLDOWN_TICKS = 10

# --- Enemy ---

ENEMY_SPEED: float = 100.0 / TICK_RATE
ENEMY_RADIUS: float = 10.0
ENEMY_HP: int = 50
ENEMY_CONTACT_DAMAGE: int = 10
ENEMY_HIT_COOLDOWN: int = 30
SPAWN_RING_RADIUS: float = 200.0

# --- Wave spawner ---

WAVE_SPAWN_COUNT: int = 5
WAVE_SPAWN_COOLDOWN: int = 120
WAVE_MAX_ENEMIES: int = 100


# --- Knife ---

KNIFE_SPEED: float = 300.0 / TICK_RATE
KNIFE_DAMAGE: int = 25
KNIFE_LIFETIME: int = 1024
KNIFE_RADIUS: float = 4.0
KNIFE_DELAYED_TICKS: int = 512
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

# --- HUD ---
HUD_BAR_WIDTH: int = 200
HUD_BAR_HEIGHT: int = 16
HUD_BAR_GAP: int = 6
HUD_MARGIN_X: int = 12
HUD_MARGIN_Y: int = 12
HUD_HP_COLOR: tuple[int, int, int] = (200, 40, 40)
HUD_MANA_COLOR: tuple[int, int, int] = (60, 120, 230)
HUD_TIMEMANA_COLOR: tuple[int, int, int] = (160, 90, 230)
HUD_BG_COLOR: tuple[int, int, int] = (40, 40, 50)
HUD_BORDER_COLOR: tuple[int, int, int] = (200, 200, 200)

# --- Background ---
USE_BG_TILE: bool = True
BG_TILE_PATH: str = "assets/bg_tile.png"

# --- Audio ---
USE_MUSIC: bool = True
MUSIC_PATH: str = "assets/music.mp3"
MUSIC_VOLUME: float = 0.5

# --- Time ---

NORMAL = "normal"
SLOW = "slow"
TIME_STOP = "stop"
REWIND = "rewind"

SLOW_SCALE: float = 0.3
TIME_STOP_DRAIN: int = 2
SLOW_DRAIN: int = 1

# --- Sprite sheet ---
USE_SPRITES: bool = True
SPRITE_COLOR_KEY: tuple[int, int, int] | None = None
SPRITE_SHEETS: dict[str, tuple[str, tuple[int, int, int] | None]] = {
    "main": ("assets/sheet.png", SPRITE_COLOR_KEY),
    "enemy": ("assets/enemy_sprites.png", SPRITE_COLOR_KEY),
}

# Each sprite: (sheet_name, x, y, w, h) in pixels on that sheet.
SPRITE_PLAYER: tuple[str, int, int, int, int] = ("main", 0, 0, 32, 50)
SPRITE_KNIFE: tuple[str, int, int, int, int] = ("main", 0, 150, 30, 10)
SPRITE_ENEMY: tuple[str, int, int, int, int] = ("enemy", 0, 352, 30, 30)

USE_BG_TILE: bool = True
BG_TILE_PATH: str = "assets/2160.png"