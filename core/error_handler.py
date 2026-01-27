
import sys
import traceback
import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTextEdit, 
                               QPushButton, QHBoxLayout, QStyle, QApplication)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

class ErrorDialog(QDialog):
    def __init__(self, title, message, details=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Content Row: Icon + Message
        content_layout = QHBoxLayout()
        
        # Icon
        icon_label = QLabel()
        icon = self.style().standardIcon(QStyle.SP_MessageBoxCritical)
        icon_label.setPixmap(icon.pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        content_layout.addWidget(icon_label)
        
        # Message
        self.lbl_msg = QLabel(message)
        self.lbl_msg.setWordWrap(True)
        self.lbl_msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
        # Give it a reasonable minimum width but let it expand vertically
        self.lbl_msg.setMinimumWidth(300)
        self.lbl_msg.setMaximumWidth(600)
        content_layout.addWidget(self.lbl_msg, 1) # stretch factor 1
        
        main_layout.addLayout(content_layout)
        
        # Details Area (Collapsed by default)
        self.details_box = QTextEdit()
        self.details_box.setReadOnly(True)
        self.details_box.setVisible(False)
        self.details_box.setMinimumHeight(100)
        if details:
            self.details_box.setText(details)
            
        main_layout.addWidget(self.details_box)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_details = QPushButton("Show Details")
        self.btn_details.clicked.connect(self.toggle_details)
        if not details:
            self.btn_details.setEnabled(False)
            
        btn_ok = QPushButton("OK")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_details)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        
        main_layout.addLayout(btn_layout)
        
        # Adjust size to fit content
        self.adjustSize()

    def toggle_details(self):
        visible = self.details_box.isVisible()
        self.details_box.setVisible(not visible)
        self.btn_details.setText("Hide Details" if not visible else "Show Details")
        
        # Resize dialog to fit new content
        if not visible:
            # expanding
            self.resize(self.width(), self.height() + 100)
        else:
            # collapsing
            self.resize(self.width(), self.height() - 100)
            self.adjustSize()

class GlobalExceptionHandler:
    def __init__(self):
        self.logger = logging.getLogger("GlobalExceptionHandler")
        
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        error_msg = str(exc_value)
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        self.logger.critical(f"Uncaught exception: {error_msg}", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Only show GUI if QApplication exists
        app = QApplication.instance()
        if app:
            # We use a custom dialog to show stack trace
            dialog = ErrorDialog(
                "Critical Error", 
                f"An unexpected error occurred:\n{error_msg}\n\nPlease check logs for more info.",
                details=tb_str
            )
            dialog.exec_()
        else:
            print("Critical Error:", error_msg, file=sys.stderr)
            print(tb_str, file=sys.stderr)

_handler = GlobalExceptionHandler()

def install_exception_handler():
    sys.excepthook = _handler.handle_exception

def show_error(title, message, details=None, parent=None):
    """
    Helper to show centralized error dialog anywhere in the app.
    """
    if details:
        logging.getLogger("ErrorHandler").warning(f"{title}: {message}\nDetails: {details}")
    else:
        logging.getLogger("ErrorHandler").warning(f"{title}: {message}")
        
    dialog = ErrorDialog(title, message, details, parent)
    dialog.exec_()
