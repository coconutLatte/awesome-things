from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication, QMenu, QSystemTrayIcon
from PySide6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPainter, QPainterPath, QPixmap, QIcon, QAction, QCursor
from loguru import logger
from ui.chat import ChatBubble
from core.event_bus import event_bus


class PetWindow(QWidget):
    """桌面宠物主窗口 - 无边框、透明、可拖拽"""

    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self._drag_pos = None
        self._current_state = "idle"

        self._setup_window()
        self._setup_ui()
        self._setup_chat()
        self._connect_events()
        self._position_at_bottom_right()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(120, 120)

    def _setup_ui(self):
        self.avatar_label = QLabel(self)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setFixedSize(120, 120)

        # 默认用文字作为头像
        self.avatar_label.setText("🤖")
        self.avatar_label.setFont(QFont("Segoe UI Emoji", 48))
        self.avatar_label.setStyleSheet("background: transparent;")

        # 状态指示器
        self.state_label = QLabel("●", self)
        self.state_label.setFixedSize(20, 20)
        self.state_label.move(95, 95)
        self._update_state_color("idle")

    def _setup_chat(self):
        self.chat_bubble = ChatBubble()
        self.chat_bubble.message_sent.connect(self._on_message_sent)

    def _connect_events(self):
        event_bus.state_changed.connect(self._on_state_changed)

    def _position_at_bottom_right(self):
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 50
        y = screen.height() - self.height() - 100
        self.move(x, y)

    def _update_state_color(self, state: str):
        colors = {
            "idle": "#4CAF50",
            "thinking": "#FFC107",
            "talking": "#2196F3",
        }
        color = colors.get(state, "#4CAF50")
        self.state_label.setStyleSheet(f"color: {color}; background: transparent; font-size: 14px;")

    def _on_state_changed(self, state: str):
        self._current_state = state
        self._update_state_color(state)

        if state == "idle":
            self.avatar_label.setText("🤖")
        elif state == "thinking":
            self.avatar_label.setText("🤔")
        elif state == "talking":
            self.avatar_label.setText("💬")

    def _on_message_sent(self, text: str):
        event_bus.user_message.emit(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 如果没有明显拖拽，则切换聊天窗口
            if self._drag_pos:
                delta = event.globalPosition().toPoint() - (self.pos() + self._drag_pos)
                if abs(delta.x()) < 5 and abs(delta.y()) < 5:
                    self._toggle_chat()
            self._drag_pos = None
            event.accept()

    def _toggle_chat(self):
        if self.chat_bubble.isVisible():
            self.chat_bubble.hide()
        else:
            # 定位到宠物上方
            pet_pos = self.pos()
            chat_x = pet_pos.x() + self.width() // 2 - self.chat_bubble.width() // 2
            chat_y = pet_pos.y() - self.chat_bubble.height() - 10
            self.chat_bubble.move(max(0, chat_x), max(0, chat_y))
            self.chat_bubble.show()
            self.chat_bubble.input_field.setFocus()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item:selected {
                background-color: #404040;
            }
        """)

        chat_action = menu.addAction("💬 对话")
        clear_action = menu.addAction("🗑️ 清空对话")
        menu.addSeparator()
        quit_action = menu.addAction("❌ 退出")

        action = menu.exec(event.globalPos())

        if action == chat_action:
            self._toggle_chat()
        elif action == clear_action:
            self.engine.context.clear()
            self.chat_bubble.chat_display.clear()
        elif action == quit_action:
            QApplication.quit()

    def show_message(self, text: str):
        self.chat_bubble.add_message("Jarvis", text)
        if not self.chat_bubble.isVisible():
            self._toggle_chat()

    def play_animation(self, anim_path: str):
        pass  # TODO: 支持 GIF 动画

    def clear_message(self):
        self.chat_bubble.chat_display.clear()
