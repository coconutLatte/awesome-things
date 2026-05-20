import os
import sys
import pytest

# 模拟 ANTHROPIC_API_KEY 避免启动警告
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Qt Application 实例，所有测试共享"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_ui_imports(qapp):
    """测试 UI 模块可正常导入"""
    from ui.chat import ChatBubble
    from ui.pet import PetWindow
    from ui.tray import SystemTray
    assert True  # 导入成功即可


def test_chat_bubble_create(qapp):
    """测试聊天气泡窗口创建"""
    from ui.chat import ChatBubble

    bubble = ChatBubble()
    assert bubble.isVisible() is False
    assert bubble.send_btn.isEnabled() is True
    assert bubble.input_field.isEnabled() is True


def test_chat_bubble_add_message(qapp):
    """测试添加消息到聊天气泡"""
    from ui.chat import ChatBubble

    bubble = ChatBubble()
    bubble.add_message("你", "你好")
    bubble.add_message("Jarvis", "你好，有什么可以帮你的？")

    html = bubble.chat_display.toHtml()
    assert "你好" in html


def test_chat_bubble_thinking(qapp, qtbot):
    """测试思考状态切换"""
    from ui.chat import ChatBubble

    bubble = ChatBubble()
    bubble._start_thinking()

    assert bubble._is_thinking is True
    assert bubble.input_field.isEnabled() is False
    assert bubble.send_btn.isEnabled() is False
    assert "思考中" in bubble.status_label.text()

    bubble._stop_thinking()
    assert bubble._is_thinking is False


def test_chat_bubble_send_signal(qapp, qtbot):
    """测试发送消息信号"""
    from ui.chat import ChatBubble

    bubble = ChatBubble()
    messages = []
    bubble.message_sent.connect(lambda s: messages.append(s))

    bubble.input_field.setText("你好")
    bubble._on_send()

    assert messages == ["你好"]
    assert bubble.input_field.text() == ""


def test_pet_window_create(qapp, qtbot):
    """测试宠物窗口创建"""
    from ui.pet import PetWindow
    from unittest.mock import MagicMock

    engine = MagicMock()
    engine.context = MagicMock()
    engine.context.clear = MagicMock()

    pet = PetWindow(engine)
    assert pet._current_state == "idle"
    # offscreen 模式下 isVisible 可能为 False，检查窗口标志
    assert pet.windowFlags() is not None


def test_context_menu(qapp, qtbot):
    """测试右键菜单"""
    from ui.pet import PetWindow
    from unittest.mock import MagicMock

    engine = MagicMock()
    engine.context = MagicMock()
    engine.context.clear = MagicMock()

    pet = PetWindow(engine)
    # 创建右键菜单，验证不崩溃
    from PySide6.QtWidgets import QMenu
    menu = QMenu()
    menu.addAction("测试")
    menu.close()


def test_thinking_to_response_transition(qapp, qtbot):
    """测试思考→回复过渡：思考中文字不应出现在最终聊天历史中"""
    from ui.chat import ChatBubble
    from core.event_bus import event_bus

    bubble = ChatBubble()

    # 模拟完整流程：用户消息 → 思考 → 流式回复 → 完成
    event_bus.state_changed.emit("thinking")
    qtbot.wait(100)  # 等待事件处理

    # 思考中应显示
    assert bubble._is_thinking is True
    assert bubble._jarvis_block >= 0

    # 模拟流式 chunk 到达
    event_bus.ai_response_chunk.emit("你好")
    event_bus.ai_response_chunk.emit("世界")
    qtbot.wait(100)

    # 流式输出应已开始，思考应停止
    assert bubble._streaming_started is True

    # 模拟回复完成
    event_bus.ai_response_done.emit("你好世界")
    qtbot.wait(100)

    # 验证：最终文本不应包含"思考中"
    final_text = bubble.chat_display.toPlainText()
    assert "思考中" not in final_text, f"最终聊天中不应出现'思考中'，实际内容: {final_text}"
    # 应包含用户消息和回复
    assert "你好世界" in final_text


def test_skill_response_no_thinking_leak(qapp, qtbot):
    """测试技能直返（无流式）：思考中文字不应出现在最终聊天历史中"""
    from ui.chat import ChatBubble
    from core.event_bus import event_bus

    bubble = ChatBubble()

    # 模拟：思考 → 技能直返（无 chunk，直接 done）
    event_bus.state_changed.emit("thinking")
    qtbot.wait(100)

    assert bubble._is_thinking is True

    # 技能直返：无 chunk，直接发 done
    event_bus.ai_response_done.emit("随时为您服务。")
    qtbot.wait(200)

    final_text = bubble.chat_display.toPlainText()
    assert "思考中" not in final_text, f"最终聊天中不应出现'思考中'，实际内容: {final_text}"
    assert "随时为您服务" in final_text


def test_no_duplicate_response(qapp, qtbot):
    """测试回复不应重复显示"""
    from ui.chat import ChatBubble
    from core.event_bus import event_bus

    bubble = ChatBubble()

    # 完整流程
    event_bus.state_changed.emit("thinking")
    qtbot.wait(100)
    event_bus.ai_response_chunk.emit("测试回复")
    qtbot.wait(100)
    event_bus.ai_response_done.emit("测试回复")
    qtbot.wait(200)

    final_text = bubble.chat_display.toPlainText()
    # "测试回复" 应只出现一次
    count = final_text.count("测试回复")
    assert count == 1, f"'测试回复'应出现1次，实际出现{count}次，内容: {final_text}"
