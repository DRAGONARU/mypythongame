import pygame
from src.core.game import Game
from src.world_setup import ArenaSetup
from config.config_params import SCREEN_SIZE

def main() -> None:
    """Entry point: initialise pygame, create game, populate arena, run."""
    pygame.init()
    game = Game(screen_size=SCREEN_SIZE)
    ArenaSetup.setup(game.world, enemy_count=0)
    game.run()
    pygame.quit()

if __name__ == "__main__":
    main()