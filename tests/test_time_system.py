from src.systems.time_system import TimeSystem
from config.config_params import NORMAL, SLOW, TIME_STOP, SLOW_SCALE, TIME_STOP_DRAIN, SLOW_DRAIN
from src.core.components import Position, TimeAffected, TimeMana, Player, Enemy, InputState
from src.core.ecs.world import World
import pygame
import pytest


@pytest.fixture
def system():
    return TimeSystem()


@pytest.fixture
def world():
    return World()


def _make_keys(*pressed):
    """Build a keys_pressed tuple with given pygame key constants set True.

    Only keys with code < 512 can be represented (matching the real
    pygame.key.get_pressed() tuple size). Modifier keys like K_LSHIFT
    exceed this bound, so slow mode is tested via a regular key (K_e).
    """
    keys = [False] * 512
    for k in pressed:
        if k < len(keys):
            keys[k] = True
    return tuple(keys)


def _add_input_state(world, keys=None):
    if keys is None:
        keys = _make_keys()
    e = world.create_entity()
    world.add_component(e, InputState(
        mouse_x=0.0, mouse_y=0.0,
        mouse_pressed=(False, False, False), keys_pressed=keys,
    ))
    return e


def _add_player(world, mana=100):
    e = world.create_entity()
    world.add_component(e, Position(x=0.0, y=0.0))
    world.add_component(e, TimeAffected(scale=1.0))
    world.add_component(e, TimeMana(value=mana, max_value=100))
    world.add_component(e, Player())
    return e


def _add_enemy(world, x=100.0, y=0.0):
    e = world.create_entity()
    world.add_component(e, Position(x=x, y=y))
    world.add_component(e, TimeAffected(scale=1.0))
    world.add_component(e, Enemy())
    return e


# --- normal mode ---


class TestNormalMode:
    def test_no_keys_all_normal(self, system, world):
        _add_input_state(world)
        p = _add_player(world)
        e = _add_enemy(world)

        system.update(world)

        assert system.current_mode == NORMAL
        assert world.get_component(p, TimeAffected).scale == 1.0
        assert world.get_component(e, TimeAffected).scale == 1.0

    def test_normal_no_mana_drain(self, system, world):
        _add_input_state(world)
        p = _add_player(world, mana=100)

        system.update(world)

        assert world.get_component(p, TimeMana).value == 100

    def test_keys_pressed_no_mana_stays_normal(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_SPACE))
        p = _add_player(world, mana=0)
        e = _add_enemy(world)

        system.update(world)

        assert system.current_mode == NORMAL
        assert world.get_component(e, TimeAffected).scale == 1.0


# --- slow mode ---


class TestSlowMode:
    def test_lshift_activates_slow(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_e))
        p = _add_player(world, mana=100)
        e = _add_enemy(world)

        system.update(world)

        assert system.current_mode == SLOW
        assert world.get_component(e, TimeAffected).scale == pytest.approx(SLOW_SCALE)

    def test_player_always_full_speed_in_slow(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_e))
        p = _add_player(world, mana=100)

        system.update(world)

        assert world.get_component(p, TimeAffected).scale == 1.0

    def test_slow_drains_mana(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_e))
        p = _add_player(world, mana=100)

        system.update(world)

        assert world.get_component(p, TimeMana).value == 100 - SLOW_DRAIN

    def test_slow_not_enough_mana_falls_back_normal(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_e))
        p = _add_player(world, mana=SLOW_DRAIN - 1)
        e = _add_enemy(world)

        system.update(world)

        assert system.current_mode == NORMAL
        assert world.get_component(e, TimeAffected).scale == 1.0
        assert world.get_component(p, TimeMana).value == SLOW_DRAIN - 1


# --- time stop mode ---


class TestTimeStopMode:
    def test_space_activates_time_stop(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_SPACE))
        p = _add_player(world, mana=100)
        e = _add_enemy(world)

        system.update(world)

        assert system.current_mode == TIME_STOP
        assert world.get_component(e, TimeAffected).scale == 0.0

    def test_player_full_speed_in_time_stop(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_SPACE))
        p = _add_player(world, mana=100)

        system.update(world)

        assert world.get_component(p, TimeAffected).scale == 1.0

    def test_time_stop_drains_mana(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_SPACE))
        p = _add_player(world, mana=100)

        system.update(world)

        assert world.get_component(p, TimeMana).value == 100 - TIME_STOP_DRAIN

    def test_time_stop_not_enough_mana_falls_back_normal(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_SPACE))
        p = _add_player(world, mana=TIME_STOP_DRAIN - 1)
        e = _add_enemy(world)

        system.update(world)

        assert system.current_mode == NORMAL
        assert world.get_component(e, TimeAffected).scale == 1.0


# --- priority ---


class TestPriority:
    def test_space_and_lshift_prefers_time_stop(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_SPACE, pygame.K_e))
        p = _add_player(world, mana=100)
        e = _add_enemy(world)

        system.update(world)

        assert system.current_mode == TIME_STOP
        assert world.get_component(e, TimeAffected).scale == 0.0

    def test_stop_insufficient_mana_falls_to_slow(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_SPACE, pygame.K_e))
        p = _add_player(world, mana=SLOW_DRAIN)
        e = _add_enemy(world)

        system.update(world)

        assert system.current_mode == SLOW
        assert world.get_component(e, TimeAffected).scale == pytest.approx(SLOW_SCALE)


# --- edge cases ---


class TestEdgeCases:
    def test_no_input_state_normal(self, system, world):
        p = _add_player(world)
        e = _add_enemy(world)

        system.update(world)

        assert system.current_mode == NORMAL
        assert world.get_component(e, TimeAffected).scale == 1.0

    def test_no_player_normal(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_SPACE))
        e = _add_enemy(world)

        system.update(world)

        assert system.current_mode == NORMAL
        assert world.get_component(e, TimeAffected).scale == 1.0

    def test_empty_world(self, system, world):
        system.update(world)
        assert system.current_mode == NORMAL

    def test_enemy_without_time_affected_untouched(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_SPACE))
        _add_player(world, mana=100)
        e = world.create_entity()
        world.add_component(e, Position(x=50.0, y=0.0))
        world.add_component(e, Enemy())

        system.update(world)

        assert world.get_component(e, TimeAffected) is None

    def test_mana_not_drained_below_zero_slow(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_e))
        p = _add_player(world, mana=SLOW_DRAIN)

        system.update(world)

        assert world.get_component(p, TimeMana).value == 0

    def test_multiple_enemies_all_slowed(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_SPACE))
        _add_player(world, mana=100)
        enemies = [_add_enemy(world, x=float(i * 50)) for i in range(5)]

        system.update(world)

        for e in enemies:
            assert world.get_component(e, TimeAffected).scale == 0.0

    def test_release_keys_restores_normal(self, system, world):
        _add_input_state(world, keys=_make_keys(pygame.K_SPACE))
        p = _add_player(world, mana=100)
        e = _add_enemy(world)

        system.update(world)
        assert world.get_component(e, TimeAffected).scale == 0.0

        state = world.get_component(world.query(InputState).__iter__().__next__()[0], InputState)
        state.keys_pressed = _make_keys()
        system.update(world)

        assert system.current_mode == NORMAL
        assert world.get_component(e, TimeAffected).scale == 1.0
