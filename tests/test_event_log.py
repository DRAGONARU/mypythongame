from src.core.event_log import EventLog, UndoEvent
from src.core.ecs.world import World
from src.core.components import Position, Velocity, Health, Player, Enemy, KnifeLoadout
import pytest


@pytest.fixture
def log():
    return EventLog(capacity_ticks=10)


@pytest.fixture
def world():
    return World()


def _bind(world, log):
    world.event_log = log
    return world


# --- begin_tick / latest_tick / clear ---


class TestTickLifecycle:
    def test_begin_tick_creates_bucket(self, log):
        log.begin_tick(1)
        assert log.latest_tick() == 1

    def test_empty_log_latest_tick(self, log):
        assert log.latest_tick() is None

    def test_multiple_ticks_ordered(self, log):
        for t in range(5):
            log.begin_tick(t)
        assert log.latest_tick() == 4

    def test_clear(self, log):
        for t in range(3):
            log.begin_tick(t)
        log.clear()
        assert log.latest_tick() is None
        assert log._events == {}

    def test_capacity_evicts_oldest(self, log):
        log = EventLog(capacity_ticks=3)
        for t in range(5):
            log.begin_tick(t)
        assert log.latest_tick() == 4
        assert 0 not in log._events
        assert 1 not in log._events
        assert 2 in log._events
        assert len(log._tick_order) == 3


# --- capture_fields ---


class TestCaptureFields:
    def test_captures_pre_tick_state(self, log, world):
        _bind(world, log)
        e = world.create_entity()
        world.add_component(e, Position(x=10.0, y=20.0))
        world.add_component(e, Health(value=100, max_value=100))

        log.begin_tick(1)
        log.capture_fields(world)

        bucket = log._events[1]
        types = {ev.component_type for ev in bucket}
        assert Position in types
        assert Health in types
        assert all(ev.kind == "field" for ev in bucket)

    def test_field_copies_are_independent(self, log, world):
        """Captured copies don't change when world mutates."""
        _bind(world, log)
        e = world.create_entity()
        world.add_component(e, Position(x=10.0, y=0.0))

        log.begin_tick(1)
        log.capture_fields(world)

        captured = None
        for ev in log._events[1]:
            if ev.component_type == Position:
                captured = ev.old_value
                break
        assert captured.x == 10.0

        world.get_component(e, Position).x = 999.0
        assert captured.x == 10.0

    def test_capture_empty_world(self, log, world):
        log.begin_tick(1)
        log.capture_fields(world)
        assert log._events[1] == []


# --- record lifecycle via World hooks ---


class TestWorldHooks:
    def test_create_entity_records_created(self, log, world):
        _bind(world, log)
        log.begin_tick(1)
        e = world.create_entity()
        events = log._events[1]
        assert len(events) == 1
        assert events[0].kind == "created"
        assert events[0].entity_id == e.id

    def test_add_component_records_added(self, log, world):
        _bind(world, log)
        log.begin_tick(1)
        e = world.create_entity()
        world.add_component(e, Position(x=0.0, y=0.0))
        kinds = [ev.kind for ev in log._events[1]]
        assert "added" in kinds

    def test_overwrite_not_recorded_as_added(self, log, world):
        _bind(world, log)
        log.begin_tick(1)
        e = world.create_entity()
        world.add_component(e, Position(x=0.0, y=0.0))
        world.add_component(e, Position(x=10.0, y=0.0))
        added = [ev for ev in log._events[1] if ev.kind == "added" and ev.component_type == Position]
        assert len(added) == 1

    def test_destroy_entity_records_destroyed(self, log, world):
        _bind(world, log)
        log.begin_tick(1)
        e = world.create_entity()
        world.add_component(e, Position(x=5.0, y=0.0))
        world.destroy_entity(e)
        destroyed = [ev for ev in log._events[1] if ev.kind == "destroyed"]
        assert len(destroyed) == 1
        assert Position in destroyed[0].old_value
        assert destroyed[0].old_value[Position].x == 5.0

    def test_remove_component_records_removed(self, log, world):
        _bind(world, log)
        log.begin_tick(1)
        e = world.create_entity()
        world.add_component(e, Position(x=7.0, y=0.0))
        world.remove_component(e, Position)
        removed = [ev for ev in log._events[1] if ev.kind == "removed"]
        assert len(removed) == 1
        assert removed[0].component_type == Position
        assert removed[0].old_value.x == 7.0

    def test_no_log_when_event_log_none(self, world):
        e = world.create_entity()
        world.add_component(e, Position(x=0.0, y=0.0))
        assert world.event_log is None


# --- undo_latest_tick: field mutations ---


class TestUndoFields:
    def test_undo_reverts_position(self, log, world):
        _bind(world, log)
        e = world.create_entity()
        world.add_component(e, Position(x=100.0, y=0.0))
        world.tick = 5

        log.begin_tick(6)
        log.capture_fields(world)
        world.get_component(e, Position).x = 500.0

        assert log.undo_latest_tick(world) is True
        assert world.get_component(e, Position).x == 100.0
        assert world.tick == 5

    def test_undo_reverts_health(self, log, world):
        _bind(world, log)
        e = world.create_entity()
        world.add_component(e, Health(value=100, max_value=100))
        world.tick = 0

        log.begin_tick(1)
        log.capture_fields(world)
        world.get_component(e, Health).value = 25

        log.undo_latest_tick(world)
        assert world.get_component(e, Health).value == 100

    def test_undo_multiple_fields(self, log, world):
        _bind(world, log)
        e = world.create_entity()
        world.add_component(e, Position(x=10.0, y=20.0))
        world.add_component(e, Velocity(x=1.0, y=2.0))
        world.tick = 0

        log.begin_tick(1)
        log.capture_fields(world)
        world.get_component(e, Position).x = 99.0
        world.get_component(e, Position).y = 88.0
        world.get_component(e, Velocity).x = -5.0

        log.undo_latest_tick(world)
        assert world.get_component(e, Position).x == 10.0
        assert world.get_component(e, Position).y == 20.0
        assert world.get_component(e, Velocity).x == 1.0
        assert world.get_component(e, Velocity).y == 2.0


# --- undo_latest_tick: lifecycle ---


class TestUndoLifecycle:
    def test_undo_created_entity(self, log, world):
        _bind(world, log)
        world.tick = 0
        log.begin_tick(1)
        log.capture_fields(world)
        e = world.create_entity()
        world.add_component(e, Position(x=50.0, y=0.0))

        log.undo_latest_tick(world)
        assert not world._is_alive(e)
        assert world._alive == 0

    def test_undo_destroyed_entity(self, log, world):
        _bind(world, log)
        e = world.create_entity()
        world.add_component(e, Position(x=50.0, y=0.0))
        world.add_component(e, Health(value=100, max_value=100))
        world.tick = 0

        log.begin_tick(1)
        log.capture_fields(world)
        world.destroy_entity(e)

        log.undo_latest_tick(world)
        assert world._is_alive(e)
        assert world.get_component(e, Position).x == 50.0
        assert world.get_component(e, Health).value == 100

    def test_undo_added_component(self, log, world):
        _bind(world, log)
        e = world.create_entity()
        world.add_component(e, Position(x=0.0, y=0.0))
        world.tick = 0

        log.begin_tick(1)
        log.capture_fields(world)
        world.add_component(e, Velocity(x=5.0, y=0.0))

        log.undo_latest_tick(world)
        assert world.get_component(e, Velocity) is None
        assert world.get_component(e, Position) is not None

    def test_undo_removed_component(self, log, world):
        _bind(world, log)
        e = world.create_entity()
        world.add_component(e, Position(x=7.0, y=0.0))
        world.tick = 0

        log.begin_tick(1)
        log.capture_fields(world)
        world.remove_component(e, Position)

        log.undo_latest_tick(world)
        pos = world.get_component(e, Position)
        assert pos is not None
        assert pos.x == 7.0

    def test_undo_destroyed_preserves_generation(self, log, world):
        """Recreated entity keeps original generation, not a new one."""
        _bind(world, log)
        e = world.create_entity()
        world.add_component(e, Position(x=0.0, y=0.0))
        world.tick = 0

        log.begin_tick(1)
        log.capture_fields(world)
        world.destroy_entity(e)
        assert world._generations[e.id] == 1

        log.undo_latest_tick(world)
        assert world._generations[e.id] == 0
        assert world._is_alive(e)


# --- undo: combined scenarios ---


class TestUndoCombined:
    def test_undo_spawn_and_damage(self, log, world):
        """Spawn knife + damage enemy in one tick: full reverse."""
        _bind(world, log)
        enemy = world.create_entity()
        world.add_component(enemy, Health(value=50, max_value=50))
        world.tick = 0

        log.begin_tick(1)
        log.capture_fields(world)

        knife = world.create_entity()
        world.add_component(knife, Position(x=0.0, y=0.0))
        world.get_component(enemy, Health).value = 25
        world.destroy_entity(knife)

        log.undo_latest_tick(world)
        assert not world._is_alive(knife)
        assert world.get_component(enemy, Health).value == 50

    def test_multiple_undo_ticks(self, log, world):
        _bind(world, log)
        e = world.create_entity()
        world.add_component(e, Position(x=0.0, y=0.0))

        for t in range(1, 4):
            log.begin_tick(t)
            log.capture_fields(world)
            world.get_component(e, Position).x += 10.0
            world.tick = t

        assert world.get_component(e, Position).x == 30.0
        assert world.tick == 3

        log.undo_latest_tick(world)
        assert world.get_component(e, Position).x == 20.0
        assert world.tick == 2

        log.undo_latest_tick(world)
        assert world.get_component(e, Position).x == 10.0
        assert world.tick == 1

        log.undo_latest_tick(world)
        assert world.get_component(e, Position).x == 0.0
        assert world.tick == 0

    def test_undo_isolation(self, log, world):
        """Undoing doesn't corrupt stored event copies for re-undo."""
        _bind(world, log)
        e = world.create_entity()
        world.add_component(e, Position(x=10.0, y=0.0))
        world.tick = 0

        log.begin_tick(1)
        log.capture_fields(world)
        world.get_component(e, Position).x = 500.0

        log.undo_latest_tick(world)
        assert world.get_component(e, Position).x == 10.0

        log.begin_tick(1)
        log.capture_fields(world)
        world.get_component(e, Position).x = 999.0
        log.undo_latest_tick(world)
        assert world.get_component(e, Position).x == 10.0


# --- edge cases ---


class TestEdgeCases:
    def test_undo_empty_log(self, log, world):
        assert log.undo_latest_tick(world) is False

    def test_undo_during_undo_returns_false(self, log, world):
        _bind(world, log)
        world.tick = 0
        log.begin_tick(1)
        log.capture_fields(world)
        log._undoing = True
        assert log.undo_latest_tick(world) is False
        log._undoing = False

    def test_no_recording_after_capacity_evict(self, world):
        log = EventLog(capacity_ticks=2)
        _bind(world, log)
        for t in range(1, 4):
            log.begin_tick(t)
            log.capture_fields(world)
            e = world.create_entity()

        assert log.latest_tick() == 3
        assert 1 not in log._events
        assert 2 in log._events
