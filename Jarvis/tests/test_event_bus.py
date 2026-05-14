import pytest
from unittest.mock import MagicMock, patch
from core.event_bus import EventBus


def test_event_bus_signals():
    """测试事件总线信号存在"""
    bus = EventBus()
    assert hasattr(bus, "user_message")
    assert hasattr(bus, "ai_response_chunk")
    assert hasattr(bus, "ai_response_done")
    assert hasattr(bus, "state_changed")
    assert hasattr(bus, "error_occurred")


def test_event_bus_emit(qtbot):
    """测试事件发射"""
    bus = EventBus()

    received = []
    bus.state_changed.connect(lambda s: received.append(s))

    bus.state_changed.emit("thinking")
    assert received == ["thinking"]
