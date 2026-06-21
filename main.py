import pygame
from src.core.game import Game
from src.world_setup import ArenaSetup

def main() -> None:
    """Entry point: initialise pygame, create game, populate arena, run."""
    pygame.init()
    game = Game(screen_size=(800, 600))
    ArenaSetup.setup(game.world, enemy_count=1000)
    game.run()
    pygame.quit()

if __name__ == "__main__":
    main()