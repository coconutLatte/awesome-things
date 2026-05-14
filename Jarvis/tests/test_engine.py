import pytest
from core.context import ContextManager
from core.intent import IntentRouter
from skills.base import SkillManager
from skills.builtin.greeting import GreetingSkill


def test_engine_init(mock_config):
    """测试引擎初始化（不启动 AI）"""
    # 只测试组件组装，不测试 AI 调用
    context = ContextManager(max_turns=20)
    intent_router = IntentRouter()
    skill_manager = SkillManager()

    skill_manager.register_builtin_skills(intent_router)

    assert len(skill_manager.skills) >= 1
    assert context.get_messages() == []


def test_greeting_route(mock_config):
    """测试问候走技能路由，不调用 AI"""
    intent_router = IntentRouter()
    skill_manager = SkillManager()
    skill_manager.register_builtin_skills(intent_router)

    result = intent_router.route("你好")
    assert result is not None
    assert isinstance(result, str)


def test_non_greeting_no_route(mock_config):
    """测试非问候消息不匹配技能"""
    intent_router = IntentRouter()
    skill_manager = SkillManager()
    skill_manager.register_builtin_skills(intent_router)

    result = intent_router.route("帮我写一段 Python 代码")
    assert result is None
