from src.core.ecs.system import System
from src.core.components import Position, Velocity, Enemy, Health, Player

class EnemySystem(System):
    """Handles enemy AI: movement towards the player."""

    ENEMY_SPEED = 100.0 / 120.0

    def update(self, world) -> None:
        self._move_enemies(world)
        self._check_death(world)

    def _move_enemies(self, world) -> None:
        """Moves enemies towards player."""

        player_pos = None
        for player_entity, player, p_pos in world.query(Player, Position):
            player_pos = p_pos
            break

        if player_pos is None:
            return

        for enemy_entity, enemy, pos in world.query(Enemy, Position):
            dx = player_pos.x - pos.x
            dy = player_pos.y - pos.y
            dist = (dx * dx + dy * dy) ** 0.5 or 1.0
            vx = (dx / dist) * self.ENEMY_SPEED
            vy = (dy / dist) * self.ENEMY_SPEED
            vel = world.get_component(enemy_entity, Velocity)
            if vel is None:
                world.add_component(enemy_entity, Velocity(x=vx, y=vy))
            else:
                vel.x = vx
                vel.y = vy

    def _check_death(self, world) -> None:
        """Checks if the enemy has died."""
        dead = []
        for entity, enemy, health in world.query(Enemy, Health):
            if health.value <= 0:
                dead.append(entity)
        for entity in dead:
            world.destroy_entity(entity)