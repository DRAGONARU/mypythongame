from src.core.ecs.system import System
from src.core.components import Knife, Position, Owner, InputState, Delayed, Velocity, Collider, KnifeLoadout, Player, Lifetime, TimeAffected, CollisionFilter, Reflective, Enemy
from src.core.components import LAYER_KNIFE, LAYER_ENEMY
import pygame

class KnifeSystem(System):
    """Handles knife spawning, delayed activation, and reflective bouncing."""

    KNIFE_SPEED = 300.0
    KNIFE_DAMAGE = 25
    KNIFE_LIFETIME = 240
    KNIFE_RADIUS = 4.0
    DELAYED_TICKS = 60
    REFLECTIVE_BOUNCES = 3
    SPAWN_COOLDOWN = 6 

    def update(self, world) -> None:
        self._handle_selection(world)
        self._handle_spawning(world)
        self._activate_delayed(world)
        self._bounce_reflective(world)

    def _handle_selection(self, world) -> None:
        """Handles knife selection and available knife types."""
        for entity, loadout, input_state in world.query(KnifeLoadout, InputState):
            keys = input_state.keys_pressed
            if len(keys) > pygame.K_1 and keys[pygame.K_1] and "normal" in loadout.available:
                loadout.current = "normal"
            elif len(keys) > pygame.K_2 and keys[pygame.K_2] and "delayed" in loadout.available:
                loadout.current = "delayed"
            elif len(keys) > pygame.K_3 and keys[pygame.K_3] and "reflective" in loadout.available:
                loadout.current = "reflective"
        
    def _handle_spawning(self, world) -> None:
        """Handles knife spawning and knife cooldown."""
        for entity, loadout, pos, input_state in world.query(KnifeLoadout, Position, InputState):
            if loadout.cooldown > 0:
                loadout.cooldown -= 1
                continue
            if input_state.mouse_pressed[0]:
                self._spawn_knife(world, entity, pos, loadout.current, input_state)
                loadout.cooldown = self.SPAWN_COOLDOWN

    def _spawn_knife(self, world, owner, owner_pos, knife_type, input_state) -> None:
        """Spawns a knife at the player's position."""
        knife = world.create_entity()

        dx = input_state.mouse_x - owner_pos.x
        dy = input_state.mouse_y - owner_pos.y
        length = (dx*dx + dy*dy) ** 0.5 or 1.0
        vx = (dx / length) * self.KNIFE_SPEED
        vy = (dy / length) * self.KNIFE_SPEED

        world.add_component(knife, Position(x=owner_pos.x, y=owner_pos.y))
        world.add_component(knife, Velocity(x=vx, y=vy))
        world.add_component(knife, Collider(radius=self.KNIFE_RADIUS))
        world.add_component(knife, Knife(knife_type=knife_type,
                                        damage=self.KNIFE_DAMAGE,
                                        speed=self.KNIFE_SPEED))
        world.add_component(knife, Lifetime(remaining_ticks=self.KNIFE_LIFETIME))
        world.add_component(knife, Owner(entity=owner))
        world.add_component(knife, TimeAffected(scale=1.0))
        world.add_component(knife, CollisionFilter(layer=LAYER_KNIFE, mask=LAYER_ENEMY))

        if knife_type == "delayed":
            time_aff = world.get_component(knife, TimeAffected)
            time_aff.scale = 0.0
            world.add_component(knife, Delayed(activate_ticks=self.DELAYED_TICKS))
        elif knife_type == "reflective":
            world.add_component(knife, Reflective(bounces_remaining=self.REFLECTIVE_BOUNCES))

    def _activate_delayed(self, world) -> None:
        """Handles delayed knife activation."""
        for entity, delayed, time_aff in world.query(Delayed, TimeAffected):
            delayed.activate_ticks -= 1
            if delayed.activate_ticks <= 0:
                time_aff.scale = 1.0
                world.remove_component(entity, Delayed)
    
    def _bounce_reflective(self, world) -> None:
        """Handles reflective knife bouncing off enemies."""
        for event in world.events:
            self._try_bounce(world, event.a, event.b)
            self._try_bounce(world, event.b, event.a)

    def _try_bounce(self, world, knife_entity, other_entity):
        if not world._is_alive(knife_entity) or not world._is_alive(other_entity):
            return
        reflective = world.get_component(knife_entity, Reflective)
        if reflective is None:
            return
        if world.get_component(other_entity, Enemy) is None:
            return

        knife_pos = world.get_component(knife_entity, Position)
        knife_vel = world.get_component(knife_entity, Velocity)
        knife_col = world.get_component(knife_entity, Collider)
        other_pos = world.get_component(other_entity, Position)
        other_col = world.get_component(other_entity, Collider)
        if knife_pos is None or knife_vel is None:
            return

        nx = knife_pos.x - other_pos.x
        ny = knife_pos.y - other_pos.y
        dist = (nx * nx + ny * ny) ** 0.5 or 1.0
        nx /= dist
        ny /= dist

        dot = knife_vel.x * nx + knife_vel.y * ny
        knife_vel.x = knife_vel.x - 2 * dot * nx
        knife_vel.y = knife_vel.y - 2 * dot * ny

        overlap = (knife_col.radius + other_col.radius) - dist
        if overlap > 0:
            knife_pos.x += nx * overlap
            knife_pos.y += ny * overlap

        reflective.bounces_remaining -= 1
        if reflective.bounces_remaining <= 0:
            world.remove_component(knife_entity, Reflective)