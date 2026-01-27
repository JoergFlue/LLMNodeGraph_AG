
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
        # record is a logging.LogRecord object
        if hasattr(record, 'getMessage'):
            msg = record.getMessage()
        elif hasattr(record, 'msg'):
            msg = record.msg
        else:
            msg = str(record)
            
        name = record.name if hasattr(record, 'name') else "ROOT"
        level_name = record.levelname if hasattr(record, 'levelname') else "INFO"
        
        # Context
        context_str = ""
        if hasattr(record, 'node_id') and record.node_id:
            context_str += f"{record.node_id} "
        if hasattr(record, 'request_id') and record.request_id:
             # If node_id is formatted like "[Node1] ", request_id might need brackets too
             context_str += f"[Req:{record.request_id}] "

        # Color Coding
        color = Colors.LOG_DEFAULT
        if "QT" in name: color = Colors.LOG_QT
        elif "LLM" in name: color = Colors.LOG_LLM
        elif "CORE" in name: color = Colors.LOG_CORE
        elif "http" in name: color = Colors.LOG_LLM # HTTP logs often related to LLM

        if level_name == "ERROR": color = Colors.LOG_ERROR
        elif level_name == "WARNING": color = Colors.LOG_WARNING
        
        # Format
        self.text_edit.setTextColor(QColor(color))
        # [Logger] [Context] Message
        self.text_edit.append(f"[{name}] {context_str}{msg}")
