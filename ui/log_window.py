
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QFont

class LogWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Logs")
        self.resize(600, 400)
        self.setWindowFlags(Qt.Window) # Floating window
        
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background-color: #111; color: #eee; font-family: Consolas, monospace;")
        layout.addWidget(self.text_edit)
        
    def append_log(self, record):
        # record is a logging.LogRecord object or dict-like
        msg = record.msg if hasattr(record, 'msg') else str(record)
        name = record.name if hasattr(record, 'name') else "ROOT"
        level_name = record.levelname if hasattr(record, 'levelname') else "INFO"
        
        # Color Coding
        color = "#cccccc" # Default
        if "QT" in name: color = "#4caf50" # Green
        elif "LLM" in name: color = "#2196f3" # Blue
        elif "CORE" in name: color = "#ff9800" # Orange
        
        if level_name == "ERROR": color = "#f44336" # Red
        elif level_name == "WARNING": color = "#ffeb3b" # Yellow
        
        # Format
        self.text_edit.setTextColor(QColor(color))
        self.text_edit.append(f"[{name}] {msg}")
