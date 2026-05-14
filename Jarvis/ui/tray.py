from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QFont, QColor
from loguru import logger


def _create_icon() -> QIcon:
    """生成一个简单的 Jarvis 图标"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 120, 215))
    painter = QPainter(pixmap)
    painter.setPen(QColor(255, 255, 255))
    painter.setFont(QFont("Arial", 32, QFont.Bold))
    painter.drawText(pixmap.rect(), 0x0084, "J")  # AlignCenter
    painter.end()
    return QIcon(pixmap)


class SystemTray:
    """系统托盘"""

    def __init__(self, pet_window):
        self.pet_window = pet_window
        self._setup_tray()

    def _setup_tray(self):
        self.tray = QSystemTrayIcon()

        # 使用默认图标
        self.tray.setIcon(_create_icon())
        self.tray.setToolTip("Jarvis AI 助手")

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px;
            }
            QMenu::item:selected {
                background-color: #404040;
            }
        """)

        show_action = menu.addAction("显示 Jarvis")
        show_action.triggered.connect(self._show_pet)

        chat_action = menu.addAction("打开对话")
        chat_action.triggered.connect(self._show_chat)

        menu.addSeparator()

        quit_action = menu.addAction("退出")
        quit_action.triggered.connect(QApplication.quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

    def _show_pet(self):
        self.pet_window.show()
        self.pet_window.activateWindow()

    def _show_chat(self):
        self.pet_window._toggle_chat()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_pet()
