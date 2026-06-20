from src.core.ecs.system import System
from src.core.components import Knife, Health, Owner, Reflective

class CombatSystem(System):
    """System for combat"""
    def update(self, world) -> None:
        for event in world.events:
            self._process(world, event.a, event.b)
            self._process(world, event.b, event.a)

    def _process(self, world, attacker, defender):
        if not world._is_alive(attacker) or not world._is_alive(defender):
            return
        knife = world.get_component(attacker, Knife)
        health = world.get_component(defender, Health)
        owner = world.get_component(attacker, Owner)
        if owner and owner.entity == defender:
            return
        if knife and health:
            health.value -= knife.damage
            if world.get_component(attacker, Reflective) is None:
                world.destroy_entity(attacker)