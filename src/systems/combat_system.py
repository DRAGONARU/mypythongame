from src.core.ecs.system import System
from src.core.components import Knife, Health, Owner, Reflective, Enemy, Player, DamageCooldown, Projectile
from config.config_params import ENEMY_CONTACT_DAMAGE, ENEMY_HIT_COOLDOWN


class CombatSystem(System):
    """System for combat: knife damage and enemy contact damage.

    Knife hits apply Knife.damage to the defender's Health and
    destroy non-reflective knives. Enemy-player contact applies
    ENEMY_CONTACT_DAMAGE to the player, guarded by a DamageCooldown
    so overlapping enemies don't deal 120 hits per second.
    """

    def update(self, world) -> None:
        self._tick_cooldowns(world)
        for event in world.events:
            self._process(world, event.a, event.b)
            self._process(world, event.b, event.a)

    def _tick_cooldowns(self, world) -> None:
        """Decrement DamageCooldown timers and remove expired ones."""
        expired = []
        for entity, cd in world.query(DamageCooldown):
            cd.remaining_ticks -= 1
            if cd.remaining_ticks <= 0:
                expired.append(entity)
        for entity in expired:
            world.remove_component(entity, DamageCooldown)

    def _process(self, world, attacker, defender):
        if not world._is_alive(attacker) or not world._is_alive(defender):
            return
        owner = world.get_component(attacker, Owner)
        if owner and owner.entity == defender:
            return
        health = world.get_component(defender, Health)
        if health is None:
            return

        knife = world.get_component(attacker, Knife)
        if knife is not None:
            health.value -= knife.damage
            if world.get_component(attacker, Reflective) is None:
                world.destroy_entity(attacker)
            return

        projectile = world.get_component(attacker, Projectile)
        if projectile is not None:
            if world.get_component(defender, Player) is not None:
                cd = world.get_component(defender, DamageCooldown)
                if cd is not None:
                    return
                health.value -= projectile.damage
                world.add_component(defender, DamageCooldown(remaining_ticks=ENEMY_HIT_COOLDOWN))
                world.destroy_entity(attacker)
            return

        enemy = world.get_component(attacker, Enemy)
        player = world.get_component(defender, Player)
        if enemy is not None and player is not None:
            cd = world.get_component(defender, DamageCooldown)
            if cd is not None:
                return
            health.value -= ENEMY_CONTACT_DAMAGE
            world.add_component(defender, DamageCooldown(remaining_ticks=ENEMY_HIT_COOLDOWN))
