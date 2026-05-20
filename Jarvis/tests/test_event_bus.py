import pytest
from core.event_bus import EventBus


def test_event_bus_signals():
    """测试事件总线信号存在"""
    bus = EventBus()
    assert hasattr(bus, "user_message")
    assert hasattr(bus, "ai_response_chunk")
    assert hasattr(bus, "ai_response_done")
    assert hasattr(bus, "state_changed")
    assert hasattr(bus, "skill_triggered")
    assert hasattr(bus, "error_occurred")


def test_state_signal_emit(qtbot):
    """测试状态信号发射"""
    bus = EventBus()

    states = []
    bus.state_changed.connect(lambda s: states.append(s))

    with qtbot.waitSignal(bus.state_changed, timeout=1000):
        bus.state_changed.emit("thinking")

    assert states == ["thinking"]


def test_user_message_signal(qtbot):
    """测试用户消息信号"""
    bus = EventBus()

    messages = []
    bus.user_message.connect(lambda s: messages.append(s))

    with qtbot.waitSignal(bus.user_message, timeout=1000):
        bus.user_message.emit("你好")

    assert messages == ["你好"]


def test_ai_response_chunk_signal(qtbot):
    """测试流式响应信号"""
    bus = EventBus()

    chunks = []
    bus.ai_response_chunk.connect(lambda s: chunks.append(s))

    bus.ai_response_chunk.emit("你好")
    bus.ai_response_chunk.emit("世界")

    assert chunks == ["你好", "世界"]


def test_ai_response_done_signal(qtbot):
    """测试响应完成信号"""
    bus = EventBus()

    done = []
    bus.ai_response_done.connect(lambda s: done.append(s))

    with qtbot.waitSignal(bus.ai_response_done, timeout=1000):
        bus.ai_response_done.emit("完整回复")

    assert done == ["完整回复"]


def test_error_signal(qtbot):
    """测试错误信号"""
    bus = EventBus()

    errors = []
    bus.error_occurred.connect(lambda s: errors.append(s))

    with qtbot.waitSignal(bus.error_occurred, timeout=1000):
        bus.error_occurred.emit("连接失败")

    assert errors == ["连接失败"]


def test_skill_triggered_signal(qtbot):
    """测试技能触发信号（多参数）"""
    bus = EventBus()

    triggered = []
    bus.skill_triggered.connect(lambda name, params: triggered.append((name, params)))

    bus.skill_triggered.emit("greeting", {"message": "你好"})

    assert len(triggered) == 1
    assert triggered[0] == ("greeting", {"message": "你好"})


def test_multiple_listeners(qtbot):
    """测试多个监听器"""
    bus = EventBus()

    a, b = [], []
    bus.state_changed.connect(lambda s: a.append(s))
    bus.state_changed.connect(lambda s: b.append(s))

    bus.state_changed.emit("idle")

    assert a == ["idle"]
    assert b == ["idle"]
