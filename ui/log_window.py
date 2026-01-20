
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QFont
from .theme import Colors, Styles

class LogWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Logs")
        self.resize(600, 400)
        self.setWindowFlags(Qt.Window) # Floating window
        
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(Styles.LOG_WINDOW)
        layout.addWidget(self.text_edit)
        
    def append_log(self, record):
        # record is a logging.LogRecord object or dict-like
        msg = record.msg if hasattr(record, 'msg') else str(record)
        name = record.name if hasattr(record, 'name') else "ROOT"
        level_name = record.levelname if hasattr(record, 'levelname') else "INFO"
        
        # Color Coding
        color = Colors.LOG_DEFAULT
        if "QT" in name: color = Colors.LOG_QT
        elif "LLM" in name: color = Colors.LOG_LLM
        elif "CORE" in name: color = Colors.LOG_CORE
        
        if level_name == "ERROR": color = Colors.LOG_ERROR
        elif level_name == "WARNING": color = Colors.LOG_WARNING
        
        # Format
        self.text_edit.setTextColor(QColor(color))
        self.text_edit.append(f"[{name}] {msg}")
