
import sys
import logging
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

# Adjust path to include project root
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.logging_setup import setup_logging, ContextFilter
from core.error_handler import GlobalExceptionHandler

class TestLogging(unittest.TestCase):
    def test_context_filter(self):
        # Setup
        logger = logging.getLogger("TestLogger")
        logger.setLevel(logging.INFO)
        
        # Capture output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = logging.Formatter('%(node_id)s%(message)s')
        handler.setFormatter(formatter)
        handler.addFilter(ContextFilter())
        logger.addHandler(handler)
        
        # Test default (no context)
        logger.info("Test Message")
        self.assertEqual(stream.getvalue().strip(), "Test Message")
        
        # Test with context
        stream.truncate(0)
        stream.seek(0)
        
        extra = {'node_id': '[Node1] '}
        adapter = logging.LoggerAdapter(logger, extra)
        adapter.info("Context Message")
        self.assertEqual(stream.getvalue().strip(), "[Node1] Context Message")

class TestErrorHandler(unittest.TestCase):
    @patch('core.error_handler.QApplication')
    @patch('core.error_handler.ErrorDialog')
    def test_handler_invokes_dialog(self, MockDialog, MockApp):
        # Setup
        handler = GlobalExceptionHandler()
        MockApp.instance.return_value = True # Simulate running app
        
        # Simulate Exception
        try:
            raise ValueError("Test Error")
        except ValueError:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            handler.handle_exception(exc_type, exc_value, exc_traceback)
            
        # Verify Dialog Created
        MockDialog.assert_called_once()
        args, _ = MockDialog.call_args
        self.assertEqual(args[0], "Critical Error")
        self.assertIn("Test Error", args[1])

if __name__ == '__main__':
    unittest.main()
