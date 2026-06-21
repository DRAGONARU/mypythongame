from src.core.ecs.system import System
from src.core.components import Position, Velocity, Player, InputState, TimeAffected
from config.config_params import PLAYER_SPEED
import pygame


class PlayerMovementSystem(System):
    """Moves the player based on keyboard input (WASD)."""

    PLAYER_SPEED: float = PLAYER_SPEED

    def update(self, world) -> None:
        input_state = self._get_input_state(world)
        if input_state is None:
            return

        keys = input_state.keys_pressed
        dx = 0.0
        dy = 0.0
        if self._is_pressed(keys, pygame.K_a):
            dx -= 1.0
        if self._is_pressed(keys, pygame.K_d):
            dx += 1.0
        if self._is_pressed(keys, pygame.K_w):
            dy -= 1.0
        if self._is_pressed(keys, pygame.K_s):
            dy += 1.0

        for entity, player, vel in world.query(Player, Velocity):
            if dx != 0.0 and dy != 0.0:
                inv = 0.7071067811865475
                vel.x = dx * self.PLAYER_SPEED * inv
                vel.y = dy * self.PLAYER_SPEED * inv
            else:
                vel.x = dx * self.PLAYER_SPEED
                vel.y = dy * self.PLAYER_SPEED

    @staticmethod
    def _is_pressed(keys: tuple[bool, ...], key_code: int) -> bool:
        """Safely check if a key is pressed, handling oversized key codes."""
        return key_code < len(keys) and keys[key_code]

    def _get_input_state(self, world) -> InputState | None:
        """Return the single InputState in the world, or None."""
        for entity, state in world.query(InputState):
            return state
        return None
