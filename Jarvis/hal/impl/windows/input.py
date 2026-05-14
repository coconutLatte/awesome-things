from typing import Callable
from hal.input import InputHAL


class WindowsInput(InputHAL):
    """Windows 平台输入实现 - 通过 Qt 事件处理"""

    def __init__(self):
        self._text_callback = None
        self._touch_callback = None

    def on_text_input(self, callback: Callable[[str], None]) -> None:
        self._text_callback = callback

    def on_touch(self, callback: Callable[[int, int], None]) -> None:
        self._touch_callback = callback

    def start(self) -> None:
        pass  # Qt 事件循环自动处理

    def stop(self) -> None:
        pass

    def handle_text(self, text: str):
        if self._text_callback:
            self._text_callback(text)

    def handle_touch(self, x: int, y: int):
        if self._touch_callback:
            self._touch_callback(x, y)
