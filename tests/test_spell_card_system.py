from src.systems.spell_card_system import SpellCardSystem
from src.core.components import (
    SpellLoadout, Mana, Position, Player, Knife, InputState,
)
from src.core.ecs.world import World
from config.config_params import (
    SPELL_KNIVES_COUNT, SPELL_KNIVES_COST, SPELL_TELEPORT_COST, SPELL_COOLDOWN,
)
import pygame
import pytest


@pytest.fixture
def system():
    return SpellCardSystem()


@pytest.fixture
def world():
    return World()


def _add_player(world, mana_value=100):
    e = world.create_entity()
    world.add_component(e, Player())
    world.add_component(e, Position(x=400.0, y=300.0))
    world.add_component(e, Mana(value=mana_value, max_value=100))
    world.add_component(e, SpellLoadout(current="knives", available=("knives", "teleport"), cooldown=0, knives_count=SPELL_KNIVES_COUNT))
    return e


def _add_input(world, right=False, z=False):
    keys = [False] * 512
    if z:
        keys[pygame.K_z] = True
    state = InputState(
        mouse_x=100.0,
        mouse_y=200.0,
        mouse_pressed=(False, False, right),
        keys_pressed=tuple(keys),
    )
    e = world.create_entity()
    world.add_component(e, state)
    return state


# --- selection ---


def test_z_cycles_spell(system, world):
    """Pressing Z cycles through available spell cards."""
    _add_player(world)
    state = _add_input(world, z=True)
    system.update(world)
    for entity, loadout in world.query(SpellLoadout):
        assert loadout.current == "teleport"


def test_z_cycles_back_to_start(system, world):
    """Cycling past the last spell wraps to the first."""
    player = _add_player(world)
    loadout = world.get_component(player, SpellLoadout)
    loadout.current = "teleport"
    _add_input(world, z=True)
    system.update(world)
    for entity, loadout in world.query(SpellLoadout):
        assert loadout.current == "knives"


def test_no_z_keeps_current(system, world):
    """Without Z the current spell is unchanged."""
    _add_player(world)
    _add_input(world)
    system.update(world)
    for entity, loadout in world.query(SpellLoadout):
        assert loadout.current == "knives"


# --- knives spell ---


def test_knives_spell_spawns_ring(system, world):
    """Right-click with the knives spell spawns a ring of knives."""
    _add_player(world)
    _add_input(world, right=True)
    system.update(world)
    knives = list(world.query(Knife))
    assert len(knives) == SPELL_KNIVES_COUNT


def test_knives_spell_drains_mana(system, world):
    """Casting knives deducts the configured mana cost."""
    player = _add_player(world)
    _add_input(world, right=True)
    system.update(world)
    mana = world.get_component(player, Mana)
    assert mana.value == 100 - SPELL_KNIVES_COST


def test_knives_spell_sets_cooldown(system, world):
    """Casting sets the shared spell cooldown."""
    player = _add_player(world)
    _add_input(world, right=True)
    system.update(world)
    loadout = world.get_component(player, SpellLoadout)
    assert loadout.cooldown == SPELL_COOLDOWN


def test_cooldown_blocks_cast(system, world):
    """While on cooldown the spell does not fire."""
    player = _add_player(world)
    loadout = world.get_component(player, SpellLoadout)
    loadout.cooldown = 3
    _add_input(world, right=True)
    system.update(world)
    knives = list(world.query(Knife))
    assert len(knives) == 0


def test_insufficient_mana_blocks_cast(system, world):
    """Not enough mana prevents casting."""
    _add_player(world, mana_value=SPELL_KNIVES_COST - 1)
    _add_input(world, right=True)
    system.update(world)
    knives = list(world.query(Knife))
    assert len(knives) == 0


# --- teleport spell ---


def test_teleport_moves_player_to_cursor(system, world):
    """The teleport spell moves the player to the cursor position."""
    player = _add_player(world)
    loadout = world.get_component(player, SpellLoadout)
    loadout.current = "teleport"
    _add_input(world, right=True)
    system.update(world)
    pos = world.get_component(player, Position)
    assert pos.x == 100.0
    assert pos.y == 200.0


def test_teleport_drains_mana(system, world):
    """Teleport deducts its configured mana cost."""
    player = _add_player(world)
    loadout = world.get_component(player, SpellLoadout)
    loadout.current = "teleport"
    _add_input(world, right=True)
    system.update(world)
    mana = world.get_component(player, Mana)
    assert mana.value == 100 - SPELL_TELEPORT_COST


def test_teleport_does_not_spawn_knives(system, world):
    """Teleport casts no knives."""
    player = _add_player(world)
    loadout = world.get_component(player, SpellLoadout)
    loadout.current = "teleport"
    _add_input(world, right=True)
    system.update(world)
    knives = list(world.query(Knife))
    assert len(knives) == 0


# --- no input ---


def test_no_right_click_no_cast(system, world):
    """Without right-click nothing happens."""
    _add_player(world)
    _add_input(world, right=False)
    system.update(world)
    knives = list(world.query(Knife))
    assert len(knives) == 0


def test_no_input_state_no_crash(system, world):
    """Missing InputState does not raise."""
    _add_player(world)
    system.update(world)


def test_no_spell_loadout_no_crash(system, world):
    """Missing SpellLoadout does not raise."""
    _add_input(world, right=True)
    system.update(world)
