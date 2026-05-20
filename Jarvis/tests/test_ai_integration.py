import os
import json
import sys
import pytest
from pathlib import Path


def _load_test_config():
    """加载测试用配置，优先级：本地文件 > 用户配置 > 环境变量"""
    # 1. 项目本地 .jarvis.test.json
    local = Path(__file__).parent.parent / ".jarvis.test.json"
    if local.exists():
        with open(local) as f:
            return json.load(f).get("ai", {})

    # 2. 用户配置 ~/.jarvis.json
    user = Path.home() / ".jarvis.json"
    if user.exists():
        with open(user) as f:
            return json.load(f).get("ai", {})

    # 3. 环境变量
    return {
        "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
        "base_url": os.environ.get("ANTHROPIC_API_BASE_URL", "https://api.anthropic.com"),
        "model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
    }


def get_ai_config():
    cfg = _load_test_config()
    api_key = cfg.get("api_key", "")
    if not api_key:
        pytest.skip("未配置 API Key，跳过真实 AI 调用测试")
    return cfg


def test_ai_connection():
    """测试 AI 连通性"""
    cfg = get_ai_config()

    from anthropic import Anthropic

    client = Anthropic(api_key=cfg["api_key"], base_url=cfg.get("base_url", "https://api.anthropic.com"))

    response = client.messages.create(
        model=cfg.get("model", "claude-sonnet-4-20250514"),
        max_tokens=500,
        messages=[{"role": "user", "content": "回复 OK"}],
        thinking={"type": "disabled"},
    )

    # 提取文本内容（兼容 thinking block）
    text = ""
    for block in response.content:
        if hasattr(block, "text"):
            text += block.text
    assert len(text) > 0


def test_ai_streaming():
    """测试 AI 流式响应"""
    cfg = get_ai_config()

    from anthropic import Anthropic

    client = Anthropic(api_key=cfg["api_key"], base_url=cfg.get("base_url", "https://api.anthropic.com"))

    chunks = []
    with client.messages.stream(
        model=cfg.get("model", "claude-sonnet-4-20250514"),
        max_tokens=500,
        messages=[{"role": "user", "content": "说 你好世界"}],
        thinking={"type": "disabled"},
    ) as stream:
        for text in stream.text_stream:
            chunks.append(text)

    result = "".join(chunks)
    assert len(result) > 0


def test_ai_brain_integration():
    """测试 AIBrain 集成"""
    cfg = get_ai_config()

    from core.ai_brain import AIBrain

    brain = AIBrain(
        api_key=cfg["api_key"],
        base_url=cfg.get("base_url", "https://api.anthropic.com"),
        model=cfg.get("model", "claude-sonnet-4-20250514"),
        max_tokens=500,
    )

    response = brain.think(
        system_prompt="你是测试助手，回复要简短。",
        messages=[{"role": "user", "content": "你好"}],
    )

    assert isinstance(response, str)
    assert len(response) > 0


def test_ai_brain_streaming():
    """测试 AIBrain 流式输出（兼容 thinking 模型）"""
    cfg = get_ai_config()

    from core.ai_brain import AIBrain
    from core.event_bus import event_bus

    brain = AIBrain(
        api_key=cfg["api_key"],
        base_url=cfg.get("base_url", "https://api.anthropic.com"),
        model=cfg.get("model", "claude-sonnet-4-20250514"),
        max_tokens=50,
    )

    chunks = []
    event_bus.ai_response_chunk.connect(lambda t: chunks.append(t))

    response = brain.think(
        system_prompt="你是测试助手。",
        messages=[{"role": "user", "content": "说 测试"}],
    )

    # 兼容 thinking 模型（text_stream 可能为空）
    assert isinstance(response, str)
    assert len(response) > 0
    assert response != "(模型未返回文本内容)"
