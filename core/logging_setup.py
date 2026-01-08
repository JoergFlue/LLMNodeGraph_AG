
import logging
from PySide6.QtCore import QObject, Signal

class QtLogSignaler(QObject):
    log_signal = Signal(object) # Carries LogRecord

class QtLogHandler(logging.Handler):
    def __init__(self, signaler: QtLogSignaler):
        super().__init__()
        self.signaler = signaler

    def emit(self, record):
        self.signaler.log_signal.emit(record)

def setup_logging():
    root_val = logging.getLogger()
    root_val.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid doubling
    if root_val.handlers:
        for handler in root_val.handlers:
            root_val.removeHandler(handler)
    
    # 1. Terminal Handler (Critical/Error only)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.ERROR)
    stream_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(stream_formatter)
    root_val.addHandler(stream_handler)
    
    # 2. Window Handler (All Info+)
    signaler = QtLogSignaler()
    qt_handler = QtLogHandler(signaler)
    qt_handler.setLevel(logging.INFO)
    qt_formatter = logging.Formatter('%(name)s: %(message)s')
    qt_handler.setFormatter(qt_formatter)
    root_val.addHandler(qt_handler)
    
    return signaler, qt_handler
