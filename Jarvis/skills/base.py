from abc import ABC, abstractmethod
from loguru import logger


class Skill(ABC):
    """技能基类，所有技能需继承此类"""

    name: str = "unnamed"
    description: str = ""

    @abstractmethod
    def match(self, message: str) -> bool:
        """判断消息是否匹配此技能"""
        ...

    @abstractmethod
    def execute(self, message: str) -> str:
        """执行技能，返回回复文本"""
        ...


class SkillManager:
    """技能管理器"""

    def __init__(self):
        self.skills: list[Skill] = []

    def register(self, skill: Skill):
        self.skills.append(skill)
        logger.info(f"注册技能: {skill.name}")

    def register_builtin_skills(self, intent_router):
        """注册内置技能"""
        from skills.builtin.greeting import GreetingSkill

        self.register(GreetingSkill())

        # 将技能注册到意图路由
        for skill in self.skills:
            intent_router.register(skill.match, skill.execute)
