from core.event_bus import event_bus


class IntentRouter:
    """意图识别与路由，将用户输入分发到对应处理逻辑"""

    def __init__(self):
        self._handlers: list[tuple[callable, callable]] = []

    def register(self, matcher: callable, handler: callable):
        """注册意图处理器
        matcher: (str) -> bool，判断是否匹配
        handler: (str) -> str，处理并返回回复
        """
        self._handlers.append((matcher, handler))

    def route(self, message: str) -> str | None:
        """尝试路由消息，返回 None 表示无匹配，应交给 AI 处理"""
        for matcher, handler in self._handlers:
            try:
                if matcher(message):
                    result = handler(message)
                    event_bus.skill_triggered.emit(matcher.__name__, {"message": message})
                    return result
            except Exception as e:
                continue
        return None
