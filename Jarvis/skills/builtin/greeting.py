import random
from skills.base import Skill


class GreetingSkill(Skill):
    """问候技能"""

    name = "greeting"
    description = "处理简单的问候语"

    _keywords = ["你好", "hi", "hello", "嗨", "早上好", "下午好", "晚上好", "早安", "晚安"]
    _responses = [
        "你好，有什么可以帮你的？",
        "随时为您服务。",
        "我在，说吧。",
        "有什么需要，尽管说。",
    ]

    def match(self, message: str) -> bool:
        text = message.strip().lower()
        return any(kw in text for kw in self._keywords)

    def execute(self, message: str) -> str:
        return random.choice(self._responses)
