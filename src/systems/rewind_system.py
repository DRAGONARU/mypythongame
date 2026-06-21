from src.core.ecs.system import System
from src.core.components import Player, TimeMana
from config.config_params import REWIND_DRAIN_PER_TICK, REWIND_MAX_TICKS


class RewindSystem(System):
    """Performs reverse-replay rewind using EventLog.

    When active (player holds rewind key + TimeMana > 0), undoes
    one tick per update by calling event_log.undo_latest_tick and
    decrementing world.tick. Game skips normal systems while
    rewinding.

    Attributes:
        active: Whether rewind is currently in progress.
        ticks_rewound: Total ticks undone in current rewind session.
    """

    DRAIN_PER_TICK: int = REWIND_DRAIN_PER_TICK
    MAX_REWIND_TICKS: int = REWIND_MAX_TICKS

    def __init__(self):
        self.active: bool = False
        self.ticks_rewound: int = 0

    def update(self, world) -> bool:
        """Undo one tick if possible. Returns True if a tick was undone."""
        if not self.active:
            return False

        player_entity = None
        for entity, pl, t_mana in world.query(Player, TimeMana):
            player_entity = entity
            break

        if player_entity is None:
            self.stop()
            return False

        time_mana = world.get_component(player_entity, TimeMana)
        if time_mana is None:
            self.stop()
            return False

        if time_mana.value < self.DRAIN_PER_TICK:
            self.stop()
            return False

        if self.ticks_rewound >= self.MAX_REWIND_TICKS:
            self.stop()
            return False

        if world.event_log is None or world.event_log.latest_tick() is None:
            self.stop()
            return False

        success = world.event_log.undo_latest_tick(world)
        if not success:
            self.stop()
            return False

        time_mana = world.get_component(player_entity, TimeMana)
        time_mana.value -= self.DRAIN_PER_TICK
        self.ticks_rewound += 1
        return True

    def start(self) -> None:
        self.active = True
        self.ticks_rewound = 0

    def stop(self) -> None:
        self.active = False
        self.ticks_rewound = 0
