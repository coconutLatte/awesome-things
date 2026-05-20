import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from utils.logger import setup_logger
import utils.config as config


def run_cli():
    """CLI 模拟模式 - 模拟聊天窗口的完整流程，方便调试"""
    import time
    import threading
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from core.engine import Engine
    from core.event_bus import event_bus

    # QApplication 必须存在，否则跨线程信号无法投递
    app = QApplication(sys.argv)

    engine = Engine()

    state = {"jarvis_text": "", "is_streaming": False, "is_thinking": False, "dots": 0}
    anim_stop = threading.Event()

    def animate_thinking():
        while not anim_stop.is_set():
            if state["is_thinking"] and not state["is_streaming"]:
                state["dots"] = (state["dots"] + 1) % 4
                dots = "." * state["dots"]
                print(f"\r\033[KJarvis: 思考中{dots}", end="", flush=True)
            anim_stop.wait(0.4)

    def on_state_changed(s):
        if s == "thinking":
            state["is_thinking"] = True
            state["is_streaming"] = False
            state["jarvis_text"] = ""
        elif s == "talking":
            state["is_thinking"] = False
        elif s == "idle":
            state["is_thinking"] = False
            state["is_streaming"] = False

    def on_chunk(text):
        if not state["is_streaming"]:
            state["is_streaming"] = True
            print(f"\r\033[KJarvis: {text}", end="", flush=True)
            state["jarvis_text"] = text
        else:
            print(text, end="", flush=True)
            state["jarvis_text"] += text

    def on_done(text):
        if state["is_streaming"]:
            print()  # 流式已显示，只换行
        else:
            print(f"Jarvis: {text}")  # 技能直返，打印
        state["is_streaming"] = False
        state["is_thinking"] = False

    def on_error(msg):
        print(f"\r\033[K⚠️ {msg}")
        state["is_thinking"] = False
        state["is_streaming"] = False

    event_bus.state_changed.connect(on_state_changed)
    event_bus.ai_response_chunk.connect(on_chunk)
    event_bus.ai_response_done.connect(on_done)
    event_bus.error_occurred.connect(on_error)

    anim_thread = threading.Thread(target=animate_thinking, daemon=True)
    anim_thread.start()

    print("\n🤖 Jarvis CLI 模拟模式（模拟聊天窗口流程）")
    print("输入消息开始对话，输入 'quit' 退出\n")

    # 用 QTimer 轮询 stdin，避免阻塞 Qt 事件循环
    import select

    def poll_input():
        # AI 处理中不读取新输入
        if state["is_thinking"] or state["is_streaming"]:
            return
        if not select.select([sys.stdin], [], [], 0)[0]:
            return
        line = sys.stdin.readline().strip()
        if not line:
            return
        if line.lower() in ('quit', 'exit', 'q'):
            anim_stop.set()
            app.quit()
            return
        state["is_thinking"] = True
        print(f"你: {line}")
        event_bus.user_message.emit(line)

    timer = QTimer()
    timer.timeout.connect(poll_input)
    timer.start(100)

    app.exec()
    anim_stop.set()
    print("再见！")


def run_gui():
    """GUI 模式 - 桌面宠物"""
    from PySide6.QtWidgets import QApplication
    from core.engine import Engine
    from ui.pet import PetWindow
    from ui.tray import SystemTray

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    engine = Engine()
    pet = PetWindow(engine)
    pet.show()
    tray = SystemTray(pet)

    logger.info("Jarvis 已启动 ✨")
    logger.info("点击宠物打开对话，右键菜单查看更多选项")

    sys.exit(app.exec())


def main():
    # 初始化日志
    setup_logger()
    logger.info("Jarvis 启动中...")

    # 首次运行配置向导
    config.setup_wizard()

    # 加载配置
    cfg = config.load_config()
    logger.info(f"平台: {cfg.get('platform', 'windows')}")

    # 检查 API Key
    api_key = config.get("ai.api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("⚠️  未配置 API Key")
        logger.warning("   请编辑 ~/.jarvis.json 或设置环境变量 ANTHROPIC_API_KEY")

    # 根据参数选择模式
    if "--cli" in sys.argv:
        run_cli()
    else:
        run_gui()


if __name__ == "__main__":
    main()
