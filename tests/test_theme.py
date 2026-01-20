"""
Unit tests for the theme module.

Tests verify that the theme module has all required constants
and that they are of the correct type.
"""

import pytest


def test_colors_class_exists():
    """Verify Colors class is defined with all required attributes."""
    from ui.theme import Colors
    
    required_attrs = [
        'CANVAS_BG', 'NODE_BG', 'NODE_HEADER', 'NODE_HEADER_SELECTED',
        'NODE_HEADER_DIRTY', 'TEXT_PRIMARY', 'TEXT_SECONDARY', 'TEXT_TERTIARY',
        'TEXT_DISABLED', 'SELECTION', 'DIRTY', 'SUCCESS', 'WARNING', 'ERROR',
        'RUNNING', 'QUEUED', 'BORDER_DEFAULT', 'BORDER_ACTIVE', 'WIRE_DEFAULT',
        'OVERLAY_BG', 'GRID_COLOR'
    ]
    
    for attr in required_attrs:
        assert hasattr(Colors, attr), f"Colors.{attr} not defined"
        value = getattr(Colors, attr)
        assert isinstance(value, str), f"Colors.{attr} must be string, got {type(value)}"


def test_spacing_class_exists():
    """Verify Spacing class is defined with all required attributes."""
    from ui.theme import Spacing
    
    required_attrs = [
        'MARGIN_SMALL', 'MARGIN_MEDIUM', 'MARGIN_LARGE', 'MARGIN_XLARGE',
        'GAP_SMALL', 'GAP_MEDIUM', 'GAP_LARGE',
        'PADDING_SMALL', 'PADDING_MEDIUM'
    ]
    
    for attr in required_attrs:
        assert hasattr(Spacing, attr), f"Spacing.{attr} not defined"
        value = getattr(Spacing, attr)
        assert isinstance(value, int), f"Spacing.{attr} must be int, got {type(value)}"


def test_sizing_class_exists():
    """Verify Sizing class is defined with all required attributes."""
    from ui.theme import Sizing
    
    required_attrs = [
        'NODE_MIN_WIDTH', 'NODE_MAX_WIDTH', 'NODE_MIN_HEIGHT', 'NODE_MAX_HEIGHT',
        'NODE_DEFAULT_WIDTH', 'NODE_DEFAULT_HEIGHT',
        'HEADER_HEIGHT', 'FOOTER_HEIGHT',
        'BUTTON_WIDTH', 'BUTTON_HEIGHT',
        'PORT_SIZE', 'PORT_HEIGHT',
        'RESIZE_HANDLE_SIZE',
        'MIN_PROMPT_HEIGHT', 'MIN_OUTPUT_HEIGHT',
        'GRID_SIZE', 'ZOOM_FACTOR'
    ]
    
    for attr in required_attrs:
        assert hasattr(Sizing, attr), f"Sizing.{attr} not defined"
        value = getattr(Sizing, attr)
        # ZOOM_FACTOR is a float, others are int
        if attr == 'ZOOM_FACTOR':
            assert isinstance(value, (int, float)), f"Sizing.{attr} must be numeric"
        else:
            assert isinstance(value, int), f"Sizing.{attr} must be int, got {type(value)}"


def test_typography_class_exists():
    """Verify Typography class is defined with all required attributes."""
    from ui.theme import Typography
    
    required_attrs = [
        'FAMILY_PRIMARY', 'FAMILY_MONOSPACE',
        'SIZE_SMALL', 'SIZE_MEDIUM', 'SIZE_NORMAL', 'SIZE_LARGE', 'SIZE_XLARGE',
        'WEIGHT_NORMAL', 'WEIGHT_BOLD'
    ]
    
    for attr in required_attrs:
        assert hasattr(Typography, attr), f"Typography.{attr} not defined"


def test_timing_class_exists():
    """Verify Timing class is defined with all required attributes."""
    from ui.theme import Timing
    
    required_attrs = [
        'SPINNER_UPDATE_MS', 'SPINNER_ROTATION_DEGREES'
    ]
    
    for attr in required_attrs:
        assert hasattr(Timing, attr), f"Timing.{attr} not defined"
        value = getattr(Timing, attr)
        assert isinstance(value, int), f"Timing.{attr} must be int, got {type(value)}"


def test_color_values_are_valid():
    """Verify all color values are valid hex or rgba strings."""
    from ui.theme import Colors
    import re
    
    hex_pattern = re.compile(r'^#[0-9a-fA-F]{3,8}$')
    rgba_pattern = re.compile(r'^rgba?\([^)]+\)$')
    
    for attr_name in dir(Colors):
        if attr_name.isupper():
            value = getattr(Colors, attr_name)
            assert hex_pattern.match(value) or rgba_pattern.match(value), \
                f"Colors.{attr_name} has invalid color value: {value}"


def test_sizing_constraints():
    """Verify sizing constraints are logical."""
    from ui.theme import Sizing
    
    assert Sizing.NODE_MIN_WIDTH < Sizing.NODE_MAX_WIDTH, \
        "NODE_MIN_WIDTH must be less than NODE_MAX_WIDTH"
    assert Sizing.NODE_MIN_HEIGHT < Sizing.NODE_MAX_HEIGHT, \
        "NODE_MIN_HEIGHT must be less than NODE_MAX_HEIGHT"
    assert Sizing.HEADER_HEIGHT > 0, "HEADER_HEIGHT must be positive"
    assert Sizing.FOOTER_HEIGHT > 0, "FOOTER_HEIGHT must be positive"
    assert Sizing.MIN_PROMPT_HEIGHT > 0, "MIN_PROMPT_HEIGHT must be positive"
    assert Sizing.MIN_OUTPUT_HEIGHT > 0, "MIN_OUTPUT_HEIGHT must be positive"
    assert Sizing.ZOOM_FACTOR > 1.0, "ZOOM_FACTOR must be greater than 1.0"


def test_spacing_values_are_positive():
    """Verify all spacing values are positive."""
    from ui.theme import Spacing
    
    for attr_name in dir(Spacing):
        if attr_name.isupper():
            value = getattr(Spacing, attr_name)
            assert value > 0, f"Spacing.{attr_name} must be positive, got {value}"


def test_typography_sizes_are_positive():
    """Verify all typography sizes are positive."""
    from ui.theme import Typography
    
    size_attrs = ['SIZE_SMALL', 'SIZE_MEDIUM', 'SIZE_NORMAL', 'SIZE_LARGE', 'SIZE_XLARGE']
    
    for attr in size_attrs:
        value = getattr(Typography, attr)
        assert value > 0, f"Typography.{attr} must be positive, got {value}"
