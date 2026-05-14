import subprocess
from hal.audio import AudioHAL


class WindowsAudio(AudioHAL):
    """Windows 平台音频实现"""

    def __init__(self):
        self._volume = 80

    def play_audio(self, audio_path: str) -> None:
        # Windows 可以用 winsound 或 pygame
        try:
            import winsound
            winsound.PlaySound(audio_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except ImportError:
            pass

    def speak(self, text: str) -> None:
        # 使用 Windows SAPI
        try:
            ps_cmd = f'Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Speak("{text}")'
            subprocess.Popen(["powershell", "-Command", ps_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

    def set_volume(self, level: int) -> None:
        self._volume = max(0, min(100, level))

    def stop(self) -> None:
        import winsound
        winsound.PlaySound(None, winsound.SND_PURGE)
