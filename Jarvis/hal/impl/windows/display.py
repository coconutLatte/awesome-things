from hal.display import DisplayHAL


class WindowsDisplay(DisplayHAL):
    """Windows 平台显示实现 - 通过 Qt Widget 显示"""

    def __init__(self):
        self._widget = None

    def set_widget(self, widget):
        """绑定 Qt Widget"""
        self._widget = widget

    def show_text(self, text: str) -> None:
        if self._widget and hasattr(self._widget, "show_message"):
            self._widget.show_message(text)

    def show_animation(self, anim_path: str) -> None:
        if self._widget and hasattr(self._widget, "play_animation"):
            self._widget.play_animation(anim_path)

    def clear(self) -> None:
        if self._widget and hasattr(self._widget, "clear_message"):
            self._widget.clear_message()

    def set_brightness(self, level: int) -> None:
        if self._widget:
            self._widget.setWindowOpacity(level / 100.0)
