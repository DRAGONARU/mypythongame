import pygame
from src.core.game import Game
from src.world_setup import ArenaSetup
from config.config_params import SCREEN_SIZE, ARENA_ENEMY_COUNT

def main() -> None:
    """Entry point: initialise pygame, create game, populate arena, run."""
    pygame.init()
    game = Game(screen_size=SCREEN_SIZE)
    ArenaSetup.setup(game.world, enemy_count=ARENA_ENEMY_COUNT)
    game.run()
    pygame.quit()

if __name__ == "__main__":
    main()