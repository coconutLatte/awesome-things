from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    """全局事件总线，用于模块间解耦通信"""

    # 用户发送消息
    user_message = Signal(str)
    # AI 回复（流式，可能触发多次）
    ai_response_chunk = Signal(str)
    # AI 回复完成
    ai_response_done = Signal(str)
    # 状态变化: idle / thinking / talking
    state_changed = Signal(str)
    # 技能触发
    skill_triggered = Signal(str, dict)
    # 错误通知
    error_occurred = Signal(str)


# 全局单例
event_bus = EventBus()
