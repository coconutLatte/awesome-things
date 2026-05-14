import pytest
from core.context import ContextManager, Message


def test_add_messages():
    """测试添加消息"""
    ctx = ContextManager(max_turns=10)
    ctx.add_user_message("你好")
    ctx.add_assistant_message("你好，有什么可以帮你的？")

    messages = ctx.get_messages()
    assert len(messages) == 2
    assert messages[0] == {"role": "user", "content": "你好"}
    assert messages[1] == {"role": "assistant", "content": "你好，有什么可以帮你的？"}


def test_context_trim():
    """测试上下文裁剪"""
    ctx = ContextManager(max_turns=2)

    # 添加超过限制的消息
    for i in range(5):
        ctx.add_user_message(f"消息 {i}")
        ctx.add_assistant_message(f"回复 {i}")

    messages = ctx.get_messages()
    # max_turns=2 意味着最多保留 4 条消息（2 轮对话）
    assert len(messages) == 4
    assert messages[0]["content"] == "消息 3"


def test_system_prompt():
    """测试系统提示词"""
    ctx = ContextManager()
    ctx.set_system_prompt("你是 Jarvis")
    assert ctx.get_system_prompt() == "你是 Jarvis"


def test_clear_context():
    """测试清空上下文"""
    ctx = ContextManager()
    ctx.add_user_message("测试")
    ctx.clear()
    assert len(ctx.get_messages()) == 0
