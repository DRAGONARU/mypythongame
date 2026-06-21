from src.core.ecs.system import System
from src.core.components import Player, Health, Mana, TimeMana
from config.config_params import PLAYER_HP_REGEN, PLAYER_MANA_REGEN, PLAYER_TIME_MANA_REGEN, COOLDOWN_TICKS


class PlayerGainSystem(System):
    """Handles passive regeneration of the player's health, mana and time mana.

    Regen cadence follows the global time flow: during Time Stop no regen
    occurs, during Slow regen fires less often. The player's own
    TimeAffected is pinned to 1.0 by TimeSystem (so movement stays normal
    during time effects), so the global scale is read from TimeSystem.

    The regen amount is left integer; instead the interval between regen
    ticks is scaled as ``COOLDOWN_TICKS / scale`` so small fractional
    scales do not zero out the per-tick gain.
    """

    def __init__(self, time_system):
        self._time_system = time_system
        self.cooldown_ticks: int = 0
        self.cooldown: int = COOLDOWN_TICKS

    def update(self, world) -> None:
        scale = self._time_system.current_scale
        if scale <= 0.0:
            return
        if self.cooldown_ticks > 0:
            self.cooldown_ticks -= 1
            return
        for entity, player, health, mana, time_mana in world.query(Player, Health, Mana, TimeMana):
            self._gain_health(health)
            self._gain_mana(mana)
            self._gain_time_mana(time_mana)
        self.cooldown_ticks = max(1, round(self.cooldown / scale))

    def _gain_health(self, health):
        """Restore health up to its maximum."""
        if health.value >= health.max_value:
            return
        health.value += PLAYER_HP_REGEN
        if health.value > health.max_value:
            health.value = health.max_value

    def _gain_mana(self, mana):
        """Restore mana up to its maximum."""
        if mana.value >= mana.max_value:
            return
        mana.value += PLAYER_MANA_REGEN
        if mana.value > mana.max_value:
            mana.value = mana.max_value

    def _gain_time_mana(self, time_mana):
        """Restore time mana up to its maximum."""
        if time_mana.value >= time_mana.max_value:
            return
        time_mana.value += PLAYER_TIME_MANA_REGEN
        if time_mana.value > time_mana.max_value:
            time_mana.value = time_mana.max_value
