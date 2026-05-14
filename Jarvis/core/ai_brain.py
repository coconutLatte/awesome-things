import anthropic
from loguru import logger
from core.event_bus import event_bus


class AIBrain:
    """Claude API 封装，负责 AI 对话"""

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com", model: str = "claude-sonnet-4-20250514", max_tokens: int = 1024):
        self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_tokens = max_tokens
        logger.info(f"AI 配置: base_url={base_url}, model={model}")

    def think(self, system_prompt: str, messages: list[dict]) -> str:
        """同步调用 AI，返回完整回复"""
        event_bus.state_changed.emit("thinking")

        try:
            full_response = []
            with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    full_response.append(text)
                    event_bus.ai_response_chunk.emit(text)

            result = "".join(full_response)
            event_bus.state_changed.emit("talking")
            event_bus.ai_response_done.emit(result)
            return result

        except Exception as e:
            err_detail = str(e)
            if "Connection" in err_detail or "connect" in err_detail.lower():
                logger.error(f"AI 连接失败，请检查 base_url 和网络: {self.client.base_url}")
                logger.error(f"原始错误: {e}")
            else:
                logger.error(f"AI 调用失败: {e}")
            event_bus.error_occurred.emit(f"AI 调用失败: {e}")
            event_bus.state_changed.emit("idle")
            raise
