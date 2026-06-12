from abc import ABC, abstractmethod
from .world import World


class System(ABC):
    """Base abstract class for ECS systems."""

    @abstractmethod
    def update(self, world: World) -> None:
        """Update the system state based on the current world state."""
        pass