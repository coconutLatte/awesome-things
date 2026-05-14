from abc import ABC, abstractmethod
from typing import Callable


class InputHAL(ABC):
    """输入设备抽象接口"""

    @abstractmethod
    def on_text_input(self, callback: Callable[[str], None]) -> None:
        """注册文字输入回调"""
        ...

    @abstractmethod
    def on_touch(self, callback: Callable[[int, int], None]) -> None:
        """注册触摸/点击回调"""
        ...

    @abstractmethod
    def start(self) -> None:
        """启动输入监听"""
        ...

    @abstractmethod
    def stop(self) -> None:
        """停止输入监听"""
        ...
