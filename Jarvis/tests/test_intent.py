import pytest
from core.intent import IntentRouter
from skills.base import Skill, SkillManager
from skills.builtin.greeting import GreetingSkill


def test_greeting_skill_match():
    """测试问候技能匹配"""
    skill = GreetingSkill()
    assert skill.match("你好") is True
    assert skill.match("hello") is True
    assert skill.match("嗨") is True
    assert skill.match("今天天气怎么样") is False


def test_greeting_skill_execute():
    """测试问候技能执行"""
    skill = GreetingSkill()
    response = skill.execute("你好")
    assert isinstance(response, str)
    assert len(response) > 0


def test_intent_router():
    """测试意图路由"""
    router = IntentRouter()

    def matcher(msg):
        return "天气" in msg

    def handler(msg):
        return "今天晴天"

    router.register(matcher, handler)

    assert router.route("今天天气怎么样") == "今天晴天"
    assert router.route("你好") is None  # 无匹配


def test_skill_manager_register():
    """测试技能注册"""
    manager = SkillManager()
    skill = GreetingSkill()
    manager.register(skill)
    assert len(manager.skills) == 1
    assert manager.skills[0].name == "greeting"
