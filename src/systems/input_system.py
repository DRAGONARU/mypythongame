from src.core.ecs.system import System
from pygame import key, mouse


class InputSystem(System):
    """Input system for mouse and keyboard"""
    def __init__(self) -> None:
        self.mouse_pos: tuple[int, int] = (0, 0)
        self.mouse_pressed: tuple[bool, bool, bool] = (False, False, False)
        self.keys_pressed: tuple[bool, ...] = ()

    def update(self, world) -> None:
        self.mouse_pos = self._get_mouse_pos()
        self.mouse_pressed = self._get_mouse_pressed()
        self.keys_pressed = self._get_keys_pressed()

    def _get_mouse_pos(self) -> tuple[int, int]:
        from pygame import mouse
        return mouse._get_mouse_pos()
    
    def _get_mouse_pressed(self) -> tuple[bool, bool, bool]:
        from pygame import mouse
        return mouse.get_pressed()

    def _get_keys_pressed(self) -> tuple[bool, ...]:
        from pygame import key
        return key.get_pressed()