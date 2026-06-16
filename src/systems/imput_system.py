from src.core.ecs.system import System
from pygame import key, mouse


class InputSystem(System):
    """Input system for mouse and keyboard"""
    def __init__(self, mouse_pos: tuple[int, int], mouse_pressed: tuple[bool, bool, bool], keys_pressed: tuple[bool, ...]):
        self.mouse_pos = mouse_pos
        self.mouse_pressed = mouse_pressed
        self.keys_pressed = keys_pressed

    def update(self, world) -> None:
        self.mouse_pos = mouse.get_pos()
        self.mouse_pressed = mouse.get_pressed()
        self.keys_pressed = key.get_pressed()