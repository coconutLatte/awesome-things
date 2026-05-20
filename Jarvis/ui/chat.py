from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication, QTextEdit, QLineEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QPoint, QTimer, Signal
from PySide6.QtGui import QFont, QColor, QPainter, QPainterPath, QPixmap, QTextCursor
from loguru import logger
from core.event_bus import event_bus


class ChatBubble(QWidget):
    """聊天气泡窗口"""

    message_sent = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(320)

        self._jarvis_block = -1       # Jarvis 消息块编号
        self._streaming_started = False
        self._is_thinking = False
        self._thinking_dots = 0

        self._setup_ui()
        self._setup_timer()
        self._connect_events()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.status_label = QLabel("● 就绪")
        self.status_label.setStyleSheet("color: #81C784; font-size: 11px; padding: 2px 4px;")
        layout.addWidget(self.status_label)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 30, 30, 230);
                color: #E0E0E0;
                border: 1px solid rgba(100, 100, 100, 150);
                border-radius: 10px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        self.chat_display.setMinimumHeight(200)
        self.chat_display.setMaximumHeight(400)
        layout.addWidget(self.chat_display)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入消息...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(40, 40, 40, 230);
                color: #E0E0E0;
                border: 1px solid rgba(100, 100, 100, 150);
                border-radius: 15px; padding: 8px 15px; font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid rgba(0, 150, 255, 200); }
        """)
        self.input_field.returnPressed.connect(self._on_send)
        input_layout.addWidget(self.input_field)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(50, 32)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 120, 215, 200);
                color: white; border: none; border-radius: 15px; font-size: 13px;
            }
            QPushButton:hover { background-color: rgba(0, 140, 235, 230); }
            QPushButton:pressed { background-color: rgba(0, 100, 195, 200); }
        """)
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)

    def _setup_timer(self):
        self._thinking_timer = QTimer(self)
        self._thinking_timer.timeout.connect(self._animate_thinking)

    def _connect_events(self):
        event_bus.state_changed.connect(self._on_state_changed)
        event_bus.ai_response_chunk.connect(self._on_stream_chunk)
        event_bus.ai_response_done.connect(self._on_stream_done)

    def _on_state_changed(self, state: str):
        if state == "thinking":
            self._start_thinking()
        elif state == "talking":
            self._stop_thinking()

    def _start_thinking(self):
        self._is_thinking = True
        self._thinking_dots = 0
        self._streaming_started = False
        self._thinking_timer.start(400)
        self.status_label.setText("● 思考中...")
        self.status_label.setStyleSheet("color: #FFC107; font-size: 11px; padding: 2px 4px;")
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        # 创建一个 Jarvis 块，先显示思考中
        self._add_jarvis_block("思考中")

    def _stop_thinking(self):
        self._is_thinking = False
        self._thinking_timer.stop()
        self.status_label.setText("● 回复中...")
        self.status_label.setStyleSheet("color: #2196F3; font-size: 11px; padding: 2px 4px;")

    def _add_jarvis_block(self, text: str):
        """在文档末尾追加一个 Jarvis 块，记录块编号"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertBlock()
        cursor.insertHtml(
            f'<span style="color:#81C784;font-weight:bold;">Jarvis:</span> '
            f'<span style="color:#999;">{text}</span>'
        )
        self._jarvis_block = self.chat_display.document().blockCount() - 1

    def _replace_jarvis_text(self, new_text: str, is_streaming: bool = False):
        """替换 Jarvis 块的文本内容"""
        if self._jarvis_block < 0:
            return
        block = self.chat_display.document().findBlockByNumber(self._jarvis_block)
        if not block.isValid():
            return
        cursor = QTextCursor(block)
        # 选中块内文本（不含块分隔符）
        cursor.setPosition(block.position())
        cursor.setPosition(block.position() + block.length() - 1, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        # 插入新内容
        color = "#E0E0E0" if is_streaming else "#999"
        cursor.insertHtml(
            f'<span style="color:#81C784;font-weight:bold;">Jarvis:</span> '
            f'<span style="color:{color};">{new_text}</span>'
        )

    def _append_to_jarvis_block(self, text: str):
        """追加文本到 Jarvis 块末尾"""
        if self._jarvis_block < 0:
            return
        block = self.chat_display.document().findBlockByNumber(self._jarvis_block)
        if not block.isValid():
            return
        cursor = QTextCursor(block)
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)

    def _animate_thinking(self):
        if self._streaming_started:
            return
        self._thinking_dots = (self._thinking_dots + 1) % 4
        dots = "." * self._thinking_dots
        self._replace_jarvis_text(f"思考中{dots}")

    def _on_stream_chunk(self, text: str):
        """流式输出"""
        if self._is_thinking:
            self._thinking_timer.stop()

        if not self._streaming_started:
            self._streaming_started = True
            # 首个 chunk：替换思考文本为回复
            self._replace_jarvis_text(text, is_streaming=True)
        else:
            # 后续 chunk：追加
            self._append_to_jarvis_block(text)
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def _on_stream_done(self, text: str):
        """流式输出完成 - 不再添加新块"""
        if not self._streaming_started and text:
            # 无流式输出（技能直返），替换思考文本
            self._replace_jarvis_text(text, is_streaming=True)
        # 重置状态（不添加新块，回复已在流式中显示）
        self._streaming_started = False
        self._jarvis_block = -1
        self.status_label.setText("● 就绪")
        self.status_label.setStyleSheet("color: #81C784; font-size: 11px; padding: 2px 4px;")
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()
        QTimer.singleShot(2000, lambda: event_bus.state_changed.emit("idle"))

    def _on_send(self):
        text = self.input_field.text().strip()
        if text:
            self.add_message("你", text)
            self.input_field.clear()
            self.message_sent.emit(text)

    def add_message(self, sender: str, text: str):
        color = "#4FC3F7" if sender == "你" else "#81C784"
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertBlock()
        cursor.insertHtml(
            f'<span style="color:{color};font-weight:bold;">{sender}:</span> {text}'
        )
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        painter.fillPath(path, QColor(30, 30, 30, 230))
        painter.drawPath(path)

    def focusOutEvent(self, event):
        pass
