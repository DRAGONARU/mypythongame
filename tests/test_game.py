from src.core.game import Game
from src.core.ecs.entity import Entity
from src.core.components import Position, Velocity, TimeAffected, Collider, Knife, Health, Lifetime
from src.core.events import CollisionEvent
import pytest


@pytest.fixture
def game(monkeypatch):
    """Create a Game with mocked pygame input methods."""
    g = Game()
    for system in g.systems:
        if hasattr(system, '_get_mouse_pos'):
            monkeypatch.setattr(system, '_get_mouse_pos', lambda: (0, 0))
            monkeypatch.setattr(system, '_get_mouse_pressed', lambda: (False, False, False))
            monkeypatch.setattr(system, '_get_keys_pressed', lambda: ())
    return g


def test_game_initializes_world(game):
    """Game creates a World on init."""
    assert game.world is not None
    assert game.world.tick == 0
    assert game.world.events == []


def test_game_initializes_systems(game):
    """Game creates all systems on init."""
    assert len(game.systems) == 9


def test_game_initializes_loop(game):
    """Game creates a GameLoop on init."""
    assert game.loop is not None


def test_game_tick_increments_tick(game):
    """_tick increments world.tick."""
    game._tick(0.008)
    assert game.world.tick == 1
    game._tick(0.008)
    assert game.world.tick == 2


def test_game_tick_clears_events(game):
    """_tick clears events after running systems."""
    e1 = game.world.create_entity()
    e2 = game.world.create_entity()
    game.world.events.append(CollisionEvent(e1, e2, game.world.tick))
    game._tick(0.008)
    assert game.world.events == []


def test_game_tick_empty_world(game):
    """_tick runs on empty world without error."""
    game._tick(0.008)


def test_game_tick_with_moving_entity(game):
    """Full tick moves an entity through the system pipeline."""
    e = game.world.create_entity()
    game.world.add_component(e, Position(x=0.0, y=0.0))
    game.world.add_component(e, Velocity(x=2.0, y=3.0))
    game.world.add_component(e, TimeAffected(scale=1.0))

    game._tick(0.008)

    pos = game.world.get_component(e, Position)
    assert pos.x == 2.0
    assert pos.y == 3.0


def test_game_tick_lifetime_destroys_entity(game):
    """Full tick destroys entity when lifetime expires."""
    e = game.world.create_entity()
    game.world.add_component(e, Lifetime(remaining_ticks=1))

    game._tick(0.008)

    assert not game.world._is_alive(e)


def test_game_tick_collision_and_combat_pipeline(game):
    """Full tick: collision generates event, combat applies damage."""
    knife = game.world.create_entity()
    game.world.add_component(knife, Position(x=0.0, y=0.0))
    game.world.add_component(knife, Collider(radius=10.0))
    game.world.add_component(knife, Knife(knife_type="normal", damage=25, speed=5.0))

    enemy = game.world.create_entity()
    game.world.add_component(enemy, Position(x=5.0, y=0.0))
    game.world.add_component(enemy, Collider(radius=10.0))
    game.world.add_component(enemy, Health(value=100, max_value=100))

    game._tick(0.008)

    assert game.world.get_component(enemy, Health).value == 75
    assert not game.world._is_alive(knife)


def test_game_render_accepts_alpha(game):
    """_render accepts alpha parameter without error."""
    game._render(0.5)


def test_game_stop_sets_running_false(game):
    """stop() signals the loop to exit."""
    game.stop()
    assert game.loop._running is False
