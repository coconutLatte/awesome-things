import os
import threading
from loguru import logger
from core.event_bus import event_bus
from core.ai_brain import AIBrain
from core.context import ContextManager
from core.intent import IntentRouter
from skills.base import SkillManager
import utils.config as config


class Engine:
    """核心引擎，协调 AI、上下文、意图路由和技能系统"""

    def __init__(self):
        self.context = ContextManager(max_turns=20)
        self.intent_router = IntentRouter()
        self.skill_manager = SkillManager()

        # 初始化 AI - 优先从配置读取，其次环境变量
        api_key = config.get("ai.api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
        base_url = config.get("ai.base_url", "https://api.anthropic.com")

        if not api_key:
            logger.warning("未配置 API Key，请在 ~/.jarvis.json 或环境变量 ANTHROPIC_API_KEY 中设置")

        self.ai = AIBrain(
            api_key=api_key,
            base_url=base_url,
            model=config.get("ai.model", "claude-sonnet-4-20250514"),
            max_tokens=config.get("ai.max_tokens", 1024),
        )

        # 设置系统提示词
        system_prompt = config.get("ai.system_prompt", "你是 Jarvis，一个智能个人助手。")
        self.context.set_system_prompt(system_prompt)

        # 注册内置技能
        self.skill_manager.register_builtin_skills(self.intent_router)

        # 连接事件
        event_bus.user_message.connect(self._on_user_message)

        logger.info("Engine 初始化完成")

    def _on_user_message(self, message: str):
        """处理用户消息"""
        self.context.add_user_message(message)

        # 先尝试技能路由
        skill_response = self.intent_router.route(message)
        if skill_response:
            self.context.add_assistant_message(skill_response)
            event_bus.ai_response_done.emit(skill_response)
            event_bus.state_changed.emit("talking")
            return

        # 交给 AI 处理（子线程，不阻塞 UI）
        threading.Thread(target=self._ai_call, daemon=True).start()

    def _ai_call(self):
        """在子线程中调用 AI"""
        try:
            response = self.ai.think(
                system_prompt=self.context.get_system_prompt(),
                messages=self.context.get_messages(),
            )
            self.context.add_assistant_message(response)
            event_bus.ai_response_done.emit(response)
        except Exception as e:
            error_msg = "抱歉，我遇到了一些问题，请稍后再试。"
            self.context.add_assistant_message(error_msg)
            event_bus.ai_response_done.emit(error_msg)
