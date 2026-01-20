"""
Test that theme constants match the original hard-coded values.

This ensures the refactoring doesn't accidentally change colors/sizes.
All values here are extracted from the original UI code before refactoring.
"""

from ui.theme import Colors, Sizing, Spacing, Typography, Timing


def test_colors_match_original_values():
    """Verify theme colors match original hard-coded values."""
    # Canvas and background colors
    assert Colors.CANVAS_BG == "#161616"
    assert Colors.NODE_BG == "#2b2b2b"
    assert Colors.GRID_COLOR == "#333"
    
    # Header colors
    assert Colors.NODE_HEADER == "#383838"
    assert Colors.NODE_HEADER_SELECTED == "#1a4d7a"
    assert Colors.NODE_HEADER_DIRTY == "#4d4418"
    
    # Text colors
    assert Colors.TEXT_PRIMARY == "#fff"
    assert Colors.TEXT_SECONDARY == "#aaa"
    assert Colors.TEXT_TERTIARY == "#888"
    assert Colors.TEXT_DISABLED == "#666"
    
    # Accent colors
    assert Colors.SELECTION == "#00aaff"
    assert Colors.DIRTY == "#e6c60d"
    assert Colors.SUCCESS == "#4caf50"
    assert Colors.WARNING == "#e6c60d"
    assert Colors.ERROR == "#d32f2f"
    
    # Status colors
    assert Colors.RUNNING == "#00ff00"
    assert Colors.QUEUED == "#e6c60d"
    
    # Border colors
    assert Colors.BORDER_DEFAULT == "#444"
    assert Colors.BORDER_ACTIVE == "#00aaff"
    
    # Wire colors
    assert Colors.WIRE_DEFAULT == "#888"
    
    # Overlay colors
    assert Colors.OVERLAY_BG == "rgba(0, 0, 0, 180)"


def test_sizing_match_original_values():
    """Verify theme sizing matches original hard-coded values."""
    # Node dimensions
    assert Sizing.NODE_MIN_WIDTH == 380
    assert Sizing.NODE_MAX_WIDTH == 800
    assert Sizing.NODE_MIN_HEIGHT == 300
    assert Sizing.NODE_MAX_HEIGHT == 1200
    
    # Node sections
    assert Sizing.HEADER_HEIGHT == 75
    assert Sizing.FOOTER_HEIGHT == 50
    
    # Components
    assert Sizing.BUTTON_WIDTH == 80
    assert Sizing.BUTTON_HEIGHT == 30
    assert Sizing.PORT_SIZE == 8
    assert Sizing.PORT_HEIGHT == 16
    assert Sizing.RESIZE_HANDLE_SIZE == 16
    
    # Text fields
    assert Sizing.MIN_PROMPT_HEIGHT == 80
    assert Sizing.MIN_OUTPUT_HEIGHT == 100
    
    # Canvas
    assert Sizing.GRID_SIZE == 40
    assert Sizing.ZOOM_FACTOR == 1.15


def test_spacing_match_original_values():
    """Verify theme spacing matches original hard-coded values."""
    assert Spacing.MARGIN_LARGE == 15
    assert Spacing.GAP_MEDIUM == 10
    assert Spacing.GAP_SMALL == 5
    assert Spacing.PADDING_SMALL == 4


def test_typography_match_original_values():
    """Verify theme typography matches original values."""
    assert Typography.FAMILY_PRIMARY == "Segoe UI"
    assert Typography.FAMILY_MONOSPACE == "Consolas"
    
    assert Typography.SIZE_SMALL == 8
    assert Typography.SIZE_MEDIUM == 9
    assert Typography.SIZE_NORMAL == 10
    assert Typography.SIZE_LARGE == 11
    assert Typography.SIZE_XLARGE == 13
    
    assert Typography.WEIGHT_NORMAL == 400
    assert Typography.WEIGHT_BOLD == 700


def test_timing_match_original_values():
    """Verify theme timing matches original values."""
    assert Timing.SPINNER_UPDATE_MS == 50
    assert Timing.SPINNER_ROTATION_DEGREES == 30
