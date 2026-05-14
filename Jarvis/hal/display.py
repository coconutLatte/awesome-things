from abc import ABC, abstractmethod


class DisplayHAL(ABC):
    """显示设备抽象接口"""

    @abstractmethod
    def show_text(self, text: str) -> None:
        """显示文本"""
        ...

    @abstractmethod
    def show_animation(self, anim_path: str) -> None:
        """播放动画"""
        ...

    @abstractmethod
    def clear(self) -> None:
        """清屏"""
        ...

    @abstractmethod
    def set_brightness(self, level: int) -> None:
        """设置亮度 (0-100)"""
        ...
