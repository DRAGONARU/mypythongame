from src.systems.input_system import InputSystem
from src.core.ecs.world import World
import pytest


@pytest.fixture
def system():
    return InputSystem()


@pytest.fixture
def world():
    return World()

@pytest.fixture
def mock_all_inputs(system, monkeypatch):
    """Mock all three input methods with default values."""
    monkeypatch.setattr(system, '_get_mouse_pos', lambda: (0, 0))
    monkeypatch.setattr(system, '_get_mouse_pressed', lambda: (False, False, False))
    monkeypatch.setattr(system, '_get_keys_pressed', lambda: ())


def test_input_initial_state(system):
    """Input system starts with default values."""
    assert system.mouse_pos == (0, 0)
    assert system.mouse_pressed == (False, False, False)
    assert system.keys_pressed == ()


def test_input_updates_mouse_pos(system, world, mock_all_inputs, monkeypatch):
    """Mouse position is updated."""
    monkeypatch.setattr(system, '_get_mouse_pos', lambda: (100, 200))
    
    system.update(world)
    
    assert system.mouse_pos == (100, 200)


def test_input_updates_mouse_pressed(system, world, mock_all_inputs, monkeypatch):
    """Mouse buttons state is updated."""
    monkeypatch.setattr(system, '_get_mouse_pressed', lambda: (True, False, False))
    
    system.update(world)
    
    assert system.mouse_pressed == (True, False, False)


def test_input_updates_keys_pressed(system, world, mock_all_inputs, monkeypatch):
    """Keyboard state is updated."""
    monkeypatch.setattr(system, '_get_keys_pressed', lambda: (False, True, False))
    
    system.update(world)
    
    assert system.keys_pressed == (False, True, False)


def test_input_does_not_modify_world(system, world, mock_all_inputs):
    """Input system doesn't modify world state."""
    e = world.create_entity()
    
    system.update(world)
    
    assert world._is_alive(e)