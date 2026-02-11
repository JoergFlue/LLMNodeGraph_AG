"""
Centralized theme configuration for the AntiGravity UI.

This module provides all UI constants including colors, spacing, sizing,
typography, and timing values. All UI components should import from this
module instead of using hard-coded values.

Usage:
    from ui.theme import Colors, Sizing, Spacing, Typography, Timing, Styles
    
    # Use in code
    painter.setPen(QPen(QColor(Colors.SELECTION), 3))
    self.width = Sizing.NODE_MIN_WIDTH
"""


class Colors:
    """Color palette for the application."""
    
    # Background colors
    CANVAS_BG = "#161616"
    NODE_BG = "#2b2b2b"
    GRID_COLOR = "#333"
    
    # Header colors
    NODE_HEADER = "#383838"
    NODE_HEADER_SELECTED = "#1a4d7a"
    NODE_HEADER_DIRTY = "#4d4418"
    
    # Text colors
    TEXT_PRIMARY = "#fff"
    TEXT_SECONDARY = "#aaa"
    TEXT_TERTIARY = "#888"
    TEXT_DISABLED = "#666"
    
    # Accent colors
    SELECTION = "#00aaff"
    DIRTY = "#e6c60d"
    SUCCESS = "#4caf50"
    WARNING = "#e6c60d"
    ERROR = "#d32f2f"
    
    # Status colors
    RUNNING = "#00ff00"
    QUEUED = "#e6c60d"
    
    # Border colors
    BORDER_DEFAULT = "#444"
    BORDER_ACTIVE = "#00aaff"
    
    # Wire colors
    WIRE_DEFAULT = "#888"
    
    # Overlay colors
    OVERLAY_BG = "rgba(0, 0, 0, 180)"
    
    # Meter colors
    METER_BG = "#222"
    METER_LOW = "#2d8a4e"
    METER_MEDIUM = "#e6c60d"
    METER_HIGH = "#d32f2f"
    
    # Port colors
    PORT_DEFAULT = "#777"
    PORT_ACTIVE = "#fff"
    PORT_ADD = "#555"
    PORT_BORDER = "#333"
    
    # Text edit colors
    TEXTEDIT_BG = "#1e1e1e"
    TEXTEDIT_TEXT = "#e0e0e0"
    TEXTEDIT_BORDER = "#444"
    OUTPUT_BG = "#151515"
    OUTPUT_TEXT = "#aaf"
    OUTPUT_BORDER = "#333"
    
    # Button colors
    BUTTON_RUN_BG = "#2d5a37"
    BUTTON_RUN_HOVER = "#3d7a47"
    BUTTON_RUN_PRESSED = "#1d3a27"
    BUTTON_CANCEL_BG = "#7a2d2d"
    BUTTON_CANCEL_HOVER = "#8a3d3d"
    BUTTON_CANCEL_PRESSED = "#5a1d1d"
    
    # Name edit colors
    NAME_EDIT_BG = "#1a4d7a"
    NAME_EDIT_TEXT = "#ffffff"
    NAME_EDIT_BORDER = "#00aaff"
    NAME_EDIT_ERROR_BG = "#4a1a1a"
    NAME_EDIT_ERROR_BORDER = "#ff0000"
    
    # Log window colors
    LOG_BG = "#111"
    LOG_TEXT = "#eee"
    LOG_DEFAULT = "#cccccc"
    LOG_QT = "#4caf50"
    LOG_LLM = "#2196f3"
    LOG_CORE = "#ff9800"
    LOG_ERROR = "#f44336"
    LOG_WARNING = "#ffeb3b"


class Spacing:
    """Spacing constants for margins, gaps, and padding."""
    
    MARGIN_SMALL = 5
    MARGIN_MEDIUM = 10
    MARGIN_LARGE = 15
    MARGIN_XLARGE = 20
    
    GAP_SMALL = 5
    GAP_MEDIUM = 10
    GAP_LARGE = 15
    
    PADDING_SMALL = 4
    PADDING_MEDIUM = 8


class Sizing:
    """Size constants for UI elements."""
    
    # Node dimensions
    NODE_MIN_WIDTH = 380
    NODE_MAX_WIDTH = 800
    NODE_MIN_HEIGHT = 300
    NODE_MAX_HEIGHT = 1200
    NODE_DEFAULT_WIDTH = 400
    NODE_DEFAULT_HEIGHT = 500
    
    # Node sections
    HEADER_HEIGHT = 75
    FOOTER_HEIGHT = 50
    
    # Components
    BUTTON_WIDTH = 80
    BUTTON_HEIGHT = 30
    PORT_SIZE = 8
    PORT_HEIGHT = 16
    RESIZE_HANDLE_SIZE = 16
    
    # Text fields
    MIN_PROMPT_HEIGHT = 80
    MIN_OUTPUT_HEIGHT = 100
    
    # Canvas
    GRID_SIZE = 40
    ZOOM_FACTOR = 1.15
    
    # Wire
    WIRE_WIDTH = 2
    WIRE_CONTROL_DIST_MIN = 50
    
    # Meters
    METER_WIDTH = 120
    METER_HEIGHT = 8
    
    # Status Spinner
    SPINNER_RADIUS = 16
    SPINNER_WIDTH = 4
    OVERLAY_WIDTH = 120
    OVERLAY_HEIGHT = 80
    
    # Layout Metrics
    HEADER_TITLE_HEIGHT = 36
    HEADER_TEXT_X = 38
    HEADER_TEXT_Y = 24
    STATUS_DOT_X = 15
    STATUS_DOT_Y = 12
    STATUS_DOT_SIZE = 12
    
    PROVIDER_LABEL_X = 15
    PROVIDER_LABEL_Y = 50
    TRACE_LABEL_Y = 68



class Typography:
    """Typography constants for fonts and text styling."""
    
    FAMILY_PRIMARY = "Segoe UI"
    FAMILY_MONOSPACE = "Consolas"
    
    SIZE_SMALL = 8
    SIZE_MEDIUM = 9
    SIZE_NORMAL = 10
    SIZE_LARGE = 11
    SIZE_XLARGE = 13
    
    WEIGHT_NORMAL = 400
    WEIGHT_BOLD = 700
    
    # Font Families
    FONT_UI = "Segoe UI"
    FONT_MONO = "Consolas"


class Timing:
    """Timing constants for animations and updates."""
    
    SPINNER_UPDATE_MS = 50
    SPINNER_ROTATION_DEGREES = 30


class Styles:
    """Qt stylesheet constants for widgets."""
    
    PROMPT_EDIT = f"""
        QTextEdit {{
            background-color: {Colors.TEXTEDIT_BG}; 
            color: {Colors.TEXTEDIT_TEXT}; 
            border: 1px solid {Colors.TEXTEDIT_BORDER}; 
            border-radius: 4px;
            font-family: '{Typography.FAMILY_MONOSPACE}', monospace;
            font-size: {Typography.SIZE_LARGE}px;
        }}
    """
    
    OUTPUT_EDIT = f"""
        QTextEdit {{
            background-color: {Colors.OUTPUT_BG}; 
            color: {Colors.OUTPUT_TEXT}; 
            border: 1px solid {Colors.OUTPUT_BORDER}; 
            border-radius: 4px;
            font-family: '{Typography.FAMILY_MONOSPACE}', monospace;
            font-size: {Typography.SIZE_LARGE}px;
        }}
    """
    
    BUTTON_RUN = f"""
        QPushButton {{
            background-color: {Colors.SUCCESS}; 
            color: white; 
            border-radius: 4px; 
            font-weight: bold;
            border: none;
        }}
        QPushButton:hover {{ background-color: #3d7a47; }}
        QPushButton:pressed {{ background-color: #1d3a27; }}
    """
    
    BUTTON_CANCEL = f"""
        QPushButton {{
            background-color: {Colors.BUTTON_CANCEL_BG}; 
            color: white; 
            border-radius: 4px; 
            font-weight: bold;
            border: none;
        }}
        QPushButton:hover {{ background-color: {Colors.BUTTON_CANCEL_HOVER}; }}
        QPushButton:pressed {{ background-color: {Colors.BUTTON_CANCEL_PRESSED}; }}
    """
    
    NAME_EDIT = f"""
        QLineEdit {{
            background-color: {Colors.NAME_EDIT_BG};
            color: {Colors.NAME_EDIT_TEXT};
            border: 1px solid {Colors.NAME_EDIT_BORDER};
            border-radius: 2px;
            font-family: '{Typography.FAMILY_PRIMARY}';
            font-size: {Typography.SIZE_XLARGE}px;
            font-weight: bold;
            padding: 0px {Spacing.PADDING_SMALL}px;
        }}
    """
    
    NAME_EDIT_ERROR = f"""
        QLineEdit {{ 
            background-color: {Colors.NAME_EDIT_ERROR_BG}; 
            color: #ffffff; 
            border: 1px solid {Colors.NAME_EDIT_ERROR_BORDER}; 
            font-family: '{Typography.FAMILY_PRIMARY}'; 
            font-size: {Typography.SIZE_XLARGE}px; 
            font-weight: bold; 
        }}
    """
    
    LOG_WINDOW = f"""
        background-color: {Colors.LOG_BG}; 
        color: {Colors.LOG_TEXT}; 
        font-family: {Typography.FAMILY_MONOSPACE}, monospace;
    """
    
    MAIN_WINDOW = f"""
        QMainWindow {{ background-color: #1e1e1e; color: #e0e0e0; }}
        QMenuBar {{ background-color: #2b2b2b; color: #eee; }}
        QMenuBar::item:selected {{ background-color: #444; }}
        QMenu {{ 
            background-color: #2b2b2b; 
            border: 1px solid #444; 
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 10px 6px 10px;
            border: 1px solid transparent;
        }}
        QMenu::item:selected {{ 
            background-color: #3e3e3e; 
            border: 1px solid {Colors.SELECTION};
            border-radius: 3px;
        }}
        QMenu::separator {{
            height: 1px;
            background: #444;
            margin: 4px 8px;
        }}
    """
    
    TAB_WIDGET = f"""
        QTabWidget::pane {{ border: 1px solid #444; top: -1px; }}
        QTabBar::tab {{
            background: #2b2b2b;
            color: #aaa;
            padding: 8px 12px;
            border: 1px solid #444;
            border-bottom: none;
            min-width: 100px;
        }}
        QTabBar::tab:selected {{
            background: #1e1e1e;
            color: #fff;
            border-bottom: 1px solid #1e1e1e;
        }}
        QTabBar::tab:!selected:hover {{
            background: #333;
        }}
    """
