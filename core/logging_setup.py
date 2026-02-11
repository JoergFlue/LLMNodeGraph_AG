"""
Logging Setup - Configures application logging.
"""

import logging
import sys
from PySide6.QtCore import QObject, Signal

class QtLogSignaler(QObject):
    """Signals log records to the UI thread."""
    log_signal = Signal(object) # Carries LogRecord

class ContextFilter(logging.Filter):
    """
    Injects context information (node_id) into logs.
    """
    def filter(self, record):
        """
        Add node_id/request_id to record if missing.
        """
        if not hasattr(record, 'node_id'):
            record.node_id = ''
        if not hasattr(record, 'request_id'):
            record.request_id = ''
        return True

class QtLogHandler(logging.Handler):
    """
    Custom handler that emits log records via Qt signal.
    """
    def __init__(self, signaler: QtLogSignaler):
        """
        Initialize the handler.
        
        Args:
            signaler (QtLogSignaler): The object to emit signals from.
        """
        super().__init__()
        self.signaler = signaler

    def emit(self, record):
        """Emit the log record signal."""
        self.signaler.log_signal.emit(record)

def setup_logging():
    """
    Configure the application logging system.
    
    Sets up:
    1. Root logger level.
    2. Terminal handler (ERROR+).
    3. Custom Qt handler (INFO+).
    4. Formatters and filters.
    
    Returns:
        Tuple[QtLogSignaler, QtLogHandler]: The signaler and handler instances.
    """
    root_val = logging.getLogger()
    root_val.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid doubling
    if root_val.handlers:
        for handler in root_val.handlers:
            root_val.removeHandler(handler)
    
    # Common Formatter
    # [Time] [Level] [Logger] [NodeID] Message
    log_format = '%(asctime)s - %(levelname)s - %(name)s - %(node_id)s%(message)s'
    formatter = logging.Formatter(log_format)
    
    # Context Filter
    context_filter = ContextFilter()
    
    # 1. Terminal Handler (Critical/Error only)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.ERROR) 
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(context_filter)
    root_val.addHandler(stream_handler)
    
    # 2. Window Handler (All Info+)
    signaler = QtLogSignaler()
    qt_handler = QtLogHandler(signaler)
    qt_handler.setLevel(logging.INFO)
    qt_handler.setFormatter(formatter)
    qt_handler.addFilter(context_filter)
    root_val.addHandler(qt_handler)
    
    return signaler, qt_handler
