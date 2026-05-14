import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from utils.logger import setup_logger
import utils.config as config


def run_cli():
    """命令行模式 - 无需 GUI，方便调试"""
    from core.engine import Engine
    from core.event_bus import event_bus

    engine = Engine()

    print("\n🤖 Jarvis CLI 模式")
    print("输入消息开始对话，输入 'quit' 退出\n")

    # 简单的命令行交互
    def on_response(text):
        print(f"\nJarvis: {text}\n")

    event_bus.ai_response_done.connect(on_response)

    while True:
        try:
            user_input = input("你: ").strip()
            if user_input.lower() in ('quit', 'exit', 'q'):
                break
            if user_input:
                event_bus.user_message.emit(user_input)
                # 等待 AI 回复
                import time
                while engine.context.messages and engine.context.messages[-1].role == "user":
                    time.sleep(0.1)
        except KeyboardInterrupt:
            break
        except EOFError:
            break

    print("\n再见！")


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
