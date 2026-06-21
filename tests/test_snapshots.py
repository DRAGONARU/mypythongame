from src.core.snapshots import WorldSnapshot, SnapshotBuffer
from src.core.ecs.world import World
from src.core.components import Position, Velocity, Health, TimeAffected, Player, Enemy
import pytest


@pytest.fixture
def world():
    return World()


def _spawn_player(world, x=0.0, y=0.0, hp=100):
    e = world.create_entity()
    world.add_component(e, Position(x=x, y=y))
    world.add_component(e, Velocity(x=0.0, y=0.0))
    world.add_component(e, Health(value=hp, max_value=hp))
    world.add_component(e, TimeAffected(scale=1.0))
    world.add_component(e, Player())
    return e


def _spawn_enemy(world, x, y, hp=50):
    e = world.create_entity()
    world.add_component(e, Position(x=x, y=y))
    world.add_component(e, Velocity(x=1.0, y=0.0))
    world.add_component(e, Health(value=hp, max_value=hp))
    world.add_component(e, TimeAffected(scale=1.0))
    world.add_component(e, Enemy())
    return e


# --- WorldSnapshot.capture ---


class TestWorldSnapshotCapture:
    def test_capture_records_tick(self, world):
        world.tick = 42
        _spawn_player(world)
        snap = WorldSnapshot.capture(world)
        assert snap.tick == 42

    def test_capture_copies_components(self, world):
        """Captured components are independent copies, not live references."""
        e = _spawn_player(world, x=10.0, y=20.0)
        snap = WorldSnapshot.capture(world)

        pos = world.get_component(e, Position)
        pos.x = 999.0
        pos.y = 888.0

        captured = snap.components[Position][0][1]
        assert captured.x == 10.0
        assert captured.y == 20.0

    def test_capture_multiple_component_types(self, world):
        _spawn_player(world)
        _spawn_enemy(world, 50.0, 0.0)
        snap = WorldSnapshot.capture(world)
        assert Position in snap.components
        assert Velocity in snap.components
        assert Health in snap.components
        assert TimeAffected in snap.components
        assert len(snap.components[Position]) == 2

    def test_capture_bookkeeping(self, world):
        _spawn_player(world)
        _spawn_enemy(world, 10.0, 0.0)
        snap = WorldSnapshot.capture(world)
        assert snap.alive == 2
        assert snap.next_id == 2
        assert len(snap.generations) == 2
        assert len(snap.free_ids) == 0

    def test_capture_empty_world(self, world):
        snap = WorldSnapshot.capture(world)
        assert snap.tick == 0
        assert snap.components == {}
        assert snap.alive == 0


# --- WorldSnapshot.restore ---


class TestWorldSnapshotRestore:
    def test_restore_reverts_position(self, world):
        e = _spawn_player(world, x=100.0, y=200.0)
        world.tick = 5
        snap = WorldSnapshot.capture(world)

        pos = world.get_component(e, Position)
        pos.x = 500.0
        pos.y = 600.0
        world.tick = 99

        snap.restore(world)
        assert world.get_component(e, Position).x == 100.0
        assert world.get_component(e, Position).y == 200.0
        assert world.tick == 5

    def test_restore_reverts_health(self, world):
        e = _spawn_player(world, hp=100)
        snap = WorldSnapshot.capture(world)

        world.get_component(e, Health).value = 30
        snap.restore(world)
        assert world.get_component(e, Health).value == 100

    def test_restore_recreates_destroyed_entity(self, world):
        e = _spawn_enemy(world, 50.0, 0.0)
        snap = WorldSnapshot.capture(world)

        world.destroy_entity(e)
        assert not world._is_alive(e)

        snap.restore(world)
        assert world._is_alive(e)
        assert world.get_component(e, Position).x == 50.0

    def test_restore_removes_entity_created_after_capture(self, world):
        _spawn_player(world)
        snap = WorldSnapshot.capture(world)

        new_enemy = _spawn_enemy(world, 100.0, 0.0)
        assert world._alive == 2

        snap.restore(world)
        assert world._alive == 1
        assert not world._is_alive(new_enemy)

    def test_restore_preserves_entity_handles(self, world):
        """Entity handle from before capture still valid after restore."""
        e = _spawn_player(world)
        snap = WorldSnapshot.capture(world)
        world.destroy_entity(e)
        snap.restore(world)
        assert world._is_alive(e)
        assert world.get_component(e, Position) is not None

    def test_restore_isolation(self, world):
        """Restoring does not mutate the snapshot's stored copies."""
        e = _spawn_player(world, x=100.0, y=0.0)
        snap = WorldSnapshot.capture(world)

        snap.restore(world)
        world.get_component(e, Position).x = 555.0

        snap.restore(world)
        assert world.get_component(e, Position).x == 100.0

    def test_restore_multiple_times(self, world):
        """Same snapshot can restore repeatedly without corruption."""
        e = _spawn_player(world, x=10.0, y=0.0, hp=100)
        snap = WorldSnapshot.capture(world)

        for _ in range(5):
            world.get_component(e, Position).x = 777.0
            world.get_component(e, Health).value = 1
            snap.restore(world)
            assert world.get_component(e, Position).x == 10.0
            assert world.get_component(e, Health).value == 100

    def test_restore_bookkeeping(self, world):
        e1 = _spawn_player(world)
        e2 = _spawn_enemy(world, 10.0, 0.0)
        world.destroy_entity(e2)
        snap = WorldSnapshot.capture(world)

        e3 = world.create_entity()
        snap.restore(world)

        assert world._alive == 1
        assert world._is_alive(e1)
        assert world._next_id == snap.next_id

    def test_restore_full_world_state(self, world):
        """Full integration: capture, mutate, restore, verify all fields."""
        p = _spawn_player(world, x=100.0, y=100.0, hp=100)
        e1 = _spawn_enemy(world, 200.0, 0.0, hp=50)
        e2 = _spawn_enemy(world, 0.0, 200.0, hp=50)
        world.tick = 10
        snap = WorldSnapshot.capture(world)

        world.get_component(p, Position).x = 0.0
        world.get_component(p, Health).value = 10
        world.get_component(e1, Position).x = 999.0
        world.get_component(e2, Health).value = 1
        world.tick = 999
        world.destroy_entity(e1)
        new = world.create_entity()

        snap.restore(world)

        assert world.tick == 10
        assert world.get_component(p, Position).x == 100.0
        assert world.get_component(p, Position).y == 100.0
        assert world.get_component(p, Health).value == 100
        assert world._is_alive(e1)
        assert world.get_component(e1, Position).x == 200.0
        assert world.get_component(e2, Health).value == 50
        assert not world._is_alive(new)
        assert world._alive == 3


# --- SnapshotBuffer ---


class TestSnapshotBuffer:
    def test_empty_buffer_latest_tick(self):
        buf = SnapshotBuffer(capacity=10)
        assert buf.latest_tick() is None
        assert buf.oldest_tick() is None
        assert buf.can_rewind(1) is False

    def test_capture_and_latest_tick(self, world):
        buf = SnapshotBuffer(capacity=10)
        _spawn_player(world)
        world.tick = 5
        buf.capture(world)
        assert buf.latest_tick() == 5
        assert buf.oldest_tick() == 5

    def test_restore_to_captured_tick(self, world):
        buf = SnapshotBuffer(capacity=10)
        e = _spawn_player(world, x=100.0, y=0.0)
        world.tick = 5
        buf.capture(world)

        world.get_component(e, Position).x = 999.0
        world.tick = 99

        assert buf.restore(world, 5) is True
        assert world.get_component(e, Position).x == 100.0
        assert world.tick == 5

    def test_restore_nonexistent_tick(self, world):
        buf = SnapshotBuffer(capacity=10)
        _spawn_player(world)
        world.tick = 5
        buf.capture(world)
        assert buf.restore(world, 0) is False
        assert buf.restore(world, 99) is False

    def test_restore_empty_buffer(self, world):
        buf = SnapshotBuffer(capacity=10)
        assert buf.restore(world, 0) is False

    def test_multiple_captures_sequential(self, world):
        buf = SnapshotBuffer(capacity=10)
        e = _spawn_player(world, x=0.0, y=0.0)

        for t in range(5):
            world.tick = t
            world.get_component(e, Position).x = float(t * 100)
            buf.capture(world)

        assert buf.latest_tick() == 4
        assert buf.oldest_tick() == 0

        assert buf.restore(world, 2) is True
        assert world.get_component(e, Position).x == 200.0
        assert world.tick == 2

    def test_buffer_overwrites_oldest(self, world):
        """When capacity exceeded, oldest snapshots are lost."""
        buf = SnapshotBuffer(capacity=3)
        e = _spawn_player(world, x=0.0, y=0.0)

        for t in range(5):
            world.tick = t
            world.get_component(e, Position).x = float(t)
            buf.capture(world)

        assert buf.latest_tick() == 4
        assert buf.oldest_tick() == 2
        assert buf.can_rewind(3) is False
        assert buf.can_rewind(2) is True

        assert buf.restore(world, 4) is True
        assert world.get_component(e, Position).x == 4.0

        assert buf.restore(world, 2) is True
        assert world.get_component(e, Position).x == 2.0

        assert buf.restore(world, 1) is False

    def test_can_rewind_within_range(self, world):
        buf = SnapshotBuffer(capacity=240)
        e = _spawn_player(world)
        for t in range(100):
            world.tick = t
            buf.capture(world)

        assert buf.can_rewind(99) is True
        assert buf.can_rewind(100) is False

    def test_restore_preserves_world_after_rewind(self, world):
        """After restore, normal capture can continue with new timeline."""
        buf = SnapshotBuffer(capacity=10)
        e = _spawn_player(world, x=0.0, y=0.0)

        world.tick = 0
        buf.capture(world)
        world.tick = 1
        world.get_component(e, Position).x = 100.0
        buf.capture(world)

        buf.restore(world, 0)
        assert world.get_component(e, Position).x == 0.0
        assert world.tick == 0

        world.tick = 1
        world.get_component(e, Position).x = 50.0
        buf.capture(world)
        assert buf.restore(world, 1) is True
        assert world.get_component(e, Position).x == 50.0

    def test_capacity_one(self, world):
        """Buffer with capacity 1 keeps only the latest snapshot."""
        buf = SnapshotBuffer(capacity=1)
        e = _spawn_player(world, x=0.0, y=0.0)

        world.tick = 0
        buf.capture(world)
        world.tick = 1
        world.get_component(e, Position).x = 100.0
        buf.capture(world)

        assert buf.latest_tick() == 1
        assert buf.oldest_tick() == 1
        assert buf.restore(world, 0) is False
        assert buf.restore(world, 1) is True
        assert world.get_component(e, Position).x == 100.0
