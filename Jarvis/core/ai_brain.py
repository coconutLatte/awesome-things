import anthropic
from loguru import logger
from core.event_bus import event_bus


class AIBrain:
    """Claude API 封装，负责 AI 对话"""

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com", model: str = "claude-sonnet-4-20250514", max_tokens: int = 131072):
        self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_tokens = max_tokens
        logger.info(f"AI 配置: base_url={base_url}, model={model}, max_tokens={max_tokens}")

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
                thinking={"type": "disabled"},
            ) as stream:
                for text in stream.text_stream:
                    full_response.append(text)
                    event_bus.ai_response_chunk.emit(text)

            result = "".join(full_response)
            if not result:
                result = "(模型未返回文本内容)"

            event_bus.state_changed.emit("talking")
            event_bus.ai_response_done.emit(result)
            return result

        except Exception as e:
            err_type = type(e).__name__

            # anthropic SDK 的 HTTP 错误
            status = getattr(e, "status_code", None)
            body = getattr(e, "body", None) or getattr(e, "response", None)

            if status:
                logger.error(f"AI HTTP 错误 [{status}]: {e}")
                if body:
                    logger.error(f"响应体: {body}")
            else:
                logger.error(f"AI 调用失败 ({err_type}): {e}")

            logger.debug(f"请求参数: model={self.model}, base_url={self.client.base_url}, max_tokens={self.max_tokens}")

            event_bus.error_occurred.emit(f"AI 错误 [{status or err_type}]: {e}")
            event_bus.state_changed.emit("idle")
            raise
