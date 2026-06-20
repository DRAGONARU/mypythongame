from src.core.ecs.system import System
from src.core.components import InputState


class InputSystem(System):
    """Input system for mouse and keyboard"""
    def __init__(self) -> None:
        self.mouse_pos: tuple[int, int] = (0, 0)
        self.mouse_pressed: tuple[bool, bool, bool] = (False, False, False)
        self.keys_pressed: tuple[bool, ...] = ()
        self._input_entity = None

    def update(self, world) -> None:
        self.mouse_pos = self._get_mouse_pos()
        self.mouse_pressed = self._get_mouse_pressed()
        self.keys_pressed = self._get_keys_pressed()
        if self._input_entity is None or not world._is_alive(self._input_entity):
            self._input_entity = world.create_entity()
        state = InputState(mouse_x=self.mouse_pos[0], mouse_y=self.mouse_pos[1], mouse_pressed=self.mouse_pressed, keys_pressed=self.keys_pressed)
        world.add_component(self._input_entity, state)

    def _get_mouse_pos(self) -> tuple[int, int]:
        from pygame import mouse
        return mouse.get_pos()
    
    def _get_mouse_pressed(self) -> tuple[bool, bool, bool]:
        from pygame import mouse
        return mouse.get_pressed()

    def _get_keys_pressed(self) -> tuple[bool, ...]:
        from pygame import key
        return key.get_pressed()