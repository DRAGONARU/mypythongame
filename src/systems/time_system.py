from src.core.ecs.system import System
from src.core.components import TimeAffected, TimeMana, Player, Delayed
from src.core.components import InputState
import pygame
from config.config_params import PLAYER_TIME_MANA, NORMAL, SLOW, TIME_STOP, REWIND, SLOW_SCALE, TIME_STOP_DRAIN, SLOW_DRAIN


class TimeSystem(System):
    """Handles Time things"""

    def __init__(self):
        self.current_mode: str = NORMAL

    @property
    def current_scale(self) -> float:
        """Global time scale derived from the current mode.

        Returns 1.0 for NORMAL, SLOW_SCALE for SLOW, 0.0 for TIME_STOP.
        The player's own TimeAffected is pinned to 1.0 by _apply_multiplier
        so movement stays normal during time effects; this property exposes
        the world-wide scale other systems (e.g. regen) should respect.
        """
        if self.current_mode == SLOW:
            return SLOW_SCALE
        if self.current_mode == TIME_STOP:
            return 0.0
        return 1.0

    def update(self, world) -> None:
        input_state = self._get_input_state(world)
        if input_state is None:
            self._apply_scales(world, NORMAL)
            return
        
        player_entity = None
        time_mana = None
        for entity, player, t_mana in world.query(Player, TimeMana):
            player_entity = entity
            time_mana = t_mana
            break
        if player_entity is None or time_mana is None:
            self._apply_scales(world, NORMAL)
            return
        
        wants_stop = self._is_pressed(input_state, pygame.K_SPACE)
        wants_slow = self._is_pressed(input_state, pygame.K_e)

        if wants_stop  and time_mana.value >= TIME_STOP_DRAIN:
            current_mode = TIME_STOP
        elif wants_slow and time_mana.value >= SLOW_DRAIN:
            current_mode = SLOW
        else:
            current_mode = NORMAL

        self._apply_scales(world, current_mode)

        if current_mode == TIME_STOP:
            time_mana.value -= TIME_STOP_DRAIN
        elif current_mode == SLOW:
            time_mana.value -= SLOW_DRAIN

    def _get_input_state(self, world) -> InputState | None:
        """Return the single InputState in the world, or None."""
        for entity, state in world.query(InputState):
            return state
        return None

    @staticmethod
    def _is_pressed(input_state: InputState, key_code: int) -> bool:
        """Safely check if a key is pressed, handling oversized key codes."""
        keys = input_state.keys_pressed
        return key_code < len(keys) and keys[key_code]
    
    def _apply_scales(self, world, mode: str) -> None:
        """Apply TimeScales to the world"""
        self.current_mode = mode
        if mode == NORMAL:
            self._apply_multiplier(world, 1.0)
        elif mode == SLOW:
            self._apply_multiplier(world, SLOW_SCALE)
        elif mode == TIME_STOP:
            self._apply_multiplier(world, 0.0)

    def _apply_multiplier(self, world, scale: float) -> None:
        """Apply a TimeScale to the world.

        Delayed knives are skipped — their scale is managed by
        KnifeSystem._activate_delayed (frozen at 0.0 until activation),
        overriding global time mode so they stay put until ready.
        """
        for entity, time_aff in world.query(TimeAffected):
            is_player = world.get_component(entity, Player) is not None
            if is_player:
                time_aff.scale = 1.0
            elif world.get_component(entity, Delayed) is not None:
                time_aff.scale = 0.0
            else:
                time_aff.scale = scale
