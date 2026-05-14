from abc import ABC, abstractmethod


class AudioHAL(ABC):
    """音频设备抽象接口"""

    @abstractmethod
    def play_audio(self, audio_path: str) -> None:
        """播放音频文件"""
        ...

    @abstractmethod
    def speak(self, text: str) -> None:
        """文字转语音并播放"""
        ...

    @abstractmethod
    def set_volume(self, level: int) -> None:
        """设置音量 (0-100)"""
        ...

    @abstractmethod
    def stop(self) -> None:
        """停止播放"""
        ...
