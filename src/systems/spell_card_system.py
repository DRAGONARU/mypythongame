import math
import pygame
from src.core.ecs.system import System
from src.core.components import (
    SpellLoadout, KnifeLoadout, InputState, Position, Velocity, Collider,
    Knife, Owner, Lifetime, TimeAffected, CollisionFilter, Player, Mana,
    LAYER_KNIFE, LAYER_ENEMY,
)
from config.config_params import (
    KNIFE_SPEED, KNIFE_DAMAGE, KNIFE_LIFETIME, KNIFE_RADIUS,
    SPELL_KNIVES_COST, SPELL_TELEPORT_COST, SPELL_COOLDOWN,
)


class SpellCardSystem(System):
    """Casts spell cards on right-click, cycling cards with Z.

    Two spell cards are supported:
      * ``knives`` — spawns a ring of knives radiating from the player.
      * ``teleport`` — instantly moves the player to the cursor.

    Casting costs Mana (per-card cost) and triggers a shared cooldown.
    Selection cycles through ``SpellLoadout.available`` with the Z key.
    """

    KNIFE_SPEED = KNIFE_SPEED
    KNIFE_DAMAGE = KNIFE_DAMAGE
    KNIFE_LIFETIME = KNIFE_LIFETIME
    KNIFE_RADIUS = KNIFE_RADIUS

    def __init__(self):
        self._knives_cost: int = SPELL_KNIVES_COST
        self._teleport_cost: int = SPELL_TELEPORT_COST
        self._cooldown: int = SPELL_COOLDOWN

    def update(self, world) -> None:
        input_state = self._get_input_state(world)
        if input_state is None:
            return
        self._handle_selection(world, input_state)
        self._handle_cast(world, input_state)

    def _get_input_state(self, world) -> InputState | None:
        """Return the single InputState in the world, or None."""
        for entity, state in world.query(InputState):
            return state
        return None

    def _handle_selection(self, world, input_state: InputState) -> None:
        """Cycle the current spell card when Z is pressed."""
        for entity, loadout in world.query(SpellLoadout):
            keys = input_state.keys_pressed
            if len(keys) > pygame.K_z and keys[pygame.K_z]:
                idx = loadout.available.index(loadout.current)
                loadout.current = loadout.available[(idx + 1) % len(loadout.available)]

    def _handle_cast(self, world, input_state: InputState) -> None:
        """Cast the current spell on right-click if mana and cooldown allow."""
        for entity, loadout, mana, pos in world.query(SpellLoadout, Mana, Position):
            if loadout.cooldown > 0:
                loadout.cooldown -= 1
                continue
            if not input_state.mouse_pressed[2]:
                continue
            cost = self._cost_for(loadout.current)
            if mana.value < cost:
                continue
            mana.value -= cost
            if loadout.current == "knives":
                self._cast_knives(world, entity, pos, loadout)
            elif loadout.current == "teleport":
                self._cast_teleport(pos, input_state)
            loadout.cooldown = self._cooldown

    def _cost_for(self, spell: str) -> int:
        """Return the Mana cost for the given spell card."""
        if spell == "knives":
            return self._knives_cost
        if spell == "teleport":
            return self._teleport_cost
        return 0

    def _cast_knives(self, world, owner, owner_pos: Position, loadout: SpellLoadout) -> None:
        """Spawn a ring of knives radiating outward from the player."""
        count = loadout.knives_count
        for i in range(count):
            angle = 2 * math.pi * i / count
            vx = math.cos(angle) * self.KNIFE_SPEED
            vy = math.sin(angle) * self.KNIFE_SPEED
            knife = world.create_entity()
            world.add_component(knife, Position(x=owner_pos.x, y=owner_pos.y))
            world.add_component(knife, Velocity(x=vx, y=vy))
            world.add_component(knife, Collider(radius=self.KNIFE_RADIUS))
            world.add_component(knife, Knife(knife_type="normal",
                                             damage=self.KNIFE_DAMAGE,
                                             speed=self.KNIFE_SPEED))
            world.add_component(knife, Lifetime(remaining_ticks=self.KNIFE_LIFETIME))
            world.add_component(knife, Owner(entity=owner))
            world.add_component(knife, TimeAffected(scale=1.0))
            world.add_component(knife, CollisionFilter(layer=LAYER_KNIFE, mask=LAYER_ENEMY))

    def _cast_teleport(self, pos: Position, input_state: InputState) -> None:
        """Move the player to the cursor position."""
        pos.x = float(input_state.mouse_x)
        pos.y = float(input_state.mouse_y)
