from src.systems.rewind_system import RewindSystem
from src.core.event_log import EventLog
from src.core.ecs.world import World
from src.core.components import Position, Health, TimeMana, Player
import pytest


@pytest.fixture
def log():
    return EventLog(capacity_ticks=20)


@pytest.fixture
def system():
    return RewindSystem()


@pytest.fixture
def world():
    return World()


def _bind(world, log):
    world.event_log = log
    return world


def _add_player(world, x=0.0, y=0.0, mana=100):
    e = world.create_entity()
    world.add_component(e, Position(x=x, y=y))
    world.add_component(e, Health(value=100, max_value=100))
    world.add_component(e, TimeMana(value=mana, max_value=100))
    world.add_component(e, Player())
    return e


def _simulate_tick(world, log, tick):
    """Run a normal tick: begin, capture, mutate tick counter."""
    world.tick = tick
    log.begin_tick(tick)
    log.capture_fields(world)


# --- start/stop ---


def test_start_sets_active(system):
    system.start()
    assert system.active is True
    assert system.ticks_rewound == 0


def test_stop_clears_state(system):
    system.start()
    system.ticks_rewound = 5
    system.stop()
    assert system.active is False
    assert system.ticks_rewound == 0


def test_update_inactive_noop(system, world):
    _add_player(world)
    system.update(world)


# --- rewind mechanics ---


class TestRewind:
    def test_undo_decrements_tick(self, system, log, world):
        _bind(world, log)
        e = _add_player(world, x=100.0, y=0.0)
        _simulate_tick(world, log, 1)
        world.get_component(e, Position).x = 500.0

        system.start()
        system.update(world)

        assert world.tick == 0
        assert world.get_component(e, Position).x == 100.0

    def test_drains_time_mana(self, system, log, world):
        _bind(world, log)
        e = _add_player(world, mana=100)
        _simulate_tick(world, log, 1)

        system.start()
        system.update(world)

        assert world.get_component(e, TimeMana).value == 100 - system.DRAIN_PER_TICK

    def test_increments_ticks_rewound(self, system, log, world):
        _bind(world, log)
        _add_player(world)
        _simulate_tick(world, log, 1)

        system.start()
        system.update(world)
        assert system.ticks_rewound == 1

        _simulate_tick(world, log, 2)
        system.update(world)
        assert system.ticks_rewound == 2

    def test_multiple_undoes(self, system, log, world):
        _bind(world, log)
        e = _add_player(world, x=0.0, y=0.0)

        for t in range(1, 4):
            _simulate_tick(world, log, t)
            world.get_component(e, Position).x += 10.0

        assert world.get_component(e, Position).x == 30.0
        assert world.tick == 3

        system.start()
        for _ in range(3):
            system.update(world)

        assert world.tick == 0
        assert world.get_component(e, Position).x == 0.0


# --- stop conditions ---


class TestStopConditions:
    def test_stop_on_low_mana(self, system, log, world):
        _bind(world, log)
        _add_player(world, mana=system.DRAIN_PER_TICK - 1)
        _simulate_tick(world, log, 1)

        system.start()
        system.update(world)

        assert system.active is False

    def test_stop_on_max_ticks(self, system, log, world):
        system = RewindSystem()
        system.MAX_REWIND_TICKS = 2
        _bind(world, log)
        _add_player(world)
        for t in range(1, 4):
            _simulate_tick(world, log, t)

        system.start()
        system.update(world)
        system.update(world)
        system.update(world)

        assert system.active is False
        assert system.ticks_rewound == 0

    def test_stop_on_empty_log(self, system, log, world):
        _bind(world, log)
        _add_player(world)

        system.start()
        system.update(world)

        assert system.active is False

    def test_stop_on_undo_failure(self, system, log, world):
        _bind(world, log)
        _add_player(world)
        _simulate_tick(world, log, 1)

        system.start()
        system.update(world)
        assert system.ticks_rewound == 1

        system.update(world)
        assert system.active is False

    def test_stop_when_no_player(self, system, log, world):
        _bind(world, log)
        _simulate_tick(world, log, 1)

        system.start()
        system.update(world)

        assert system.active is False

    def test_mana_not_drained_below_zero(self, system, log, world):
        _bind(world, log)
        e = _add_player(world, mana=system.DRAIN_PER_TICK)
        _simulate_tick(world, log, 1)

        system.start()
        system.update(world)
        assert system.active is True
        assert world.get_component(e, TimeMana).value == 0

        _simulate_tick(world, log, 2)
        system.update(world)
        assert system.active is False


# --- no event_log ---


def test_no_event_log_stops(system, world):
    _add_player(world)
    system.start()
    system.update(world)
    assert system.active is False
