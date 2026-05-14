from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    role: str  # "user" 或 "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


class ContextManager:
    """管理对话上下文历史"""

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.messages: list[Message] = []
        self._system_prompt: str = ""

    def set_system_prompt(self, prompt: str):
        self._system_prompt = prompt

    def add_user_message(self, content: str):
        self.messages.append(Message(role="user", content=content))
        self._trim()

    def add_assistant_message(self, content: str):
        self.messages.append(Message(role="assistant", content=content))
        self._trim()

    def get_messages(self) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def get_system_prompt(self) -> str:
        return self._system_prompt

    def clear(self):
        self.messages.clear()

    def _trim(self):
        if len(self.messages) > self.max_turns * 2:
            self.messages = self.messages[-(self.max_turns * 2):]
