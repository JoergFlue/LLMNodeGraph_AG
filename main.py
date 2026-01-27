import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import AntiGravityWindow
from core.error_handler import install_exception_handler

def main():
    install_exception_handler()
    app = QApplication(sys.argv)
    window = AntiGravityWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
