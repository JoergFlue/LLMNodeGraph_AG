"""
Integration tests for UI components using theme constants.

Tests verify that UI components correctly import and use theme constants.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from core.graph import Graph
from core.node import Node
from ui.node_item import NodeItem
from ui.wire_item import WireItem
from ui.canvas import CanvasScene
from ui.theme import Colors, Sizing, Spacing


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def sample_graph():
    """Create a sample graph for testing."""
    graph = Graph()
    return graph


@pytest.fixture
def sample_node(sample_graph):
    """Create a sample node."""
    node = Node(
        id="test-node-1",
        name="Test Node",
        prompt="Test prompt",
        pos_x=100,
        pos_y=100
    )
    sample_graph.add_node(node)
    return node


def test_node_item_imports_theme(qapp, sample_node, sample_graph):
    """Verify NodeItem imports theme constants."""
    node_item = NodeItem(sample_node, sample_graph)
    
    # Verify that the node_item module imports theme
    from ui import node_item as node_item_module
    assert hasattr(node_item_module, 'Colors'), "NodeItem should import Colors from theme"
    assert hasattr(node_item_module, 'Sizing'), "NodeItem should import Sizing from theme"
    assert hasattr(node_item_module, 'Spacing'), "NodeItem should import Spacing from theme"


def test_node_item_respects_min_dimensions(qapp, sample_node, sample_graph):
    """Verify NodeItem respects theme sizing constants."""
    node_item = NodeItem(sample_node, sample_graph)
    
    # Check that node respects minimum dimensions
    assert node_item.width >= Sizing.NODE_MIN_WIDTH, \
        f"Node width {node_item.width} is less than minimum {Sizing.NODE_MIN_WIDTH}"
    assert node_item.height >= Sizing.NODE_MIN_HEIGHT, \
        f"Node height {node_item.height} is less than minimum {Sizing.NODE_MIN_HEIGHT}"


def test_wire_item_imports_theme(qapp):
    """Verify WireItem imports theme constants."""
    wire = WireItem(QPointF(0, 0), QPointF(100, 100))
    
    from ui import wire_item as wire_item_module
    assert hasattr(wire_item_module, 'Colors'), "WireItem should import Colors from theme"


def test_canvas_scene_imports_theme(qapp):
    """Verify CanvasScene imports theme constants."""
    scene = CanvasScene()
    
    from ui import canvas as canvas_module
    assert hasattr(canvas_module, 'Colors'), "Canvas should import Colors from theme"
    
    # Verify background brush is set
    brush = scene.backgroundBrush()
    assert brush is not None, "Canvas should have background brush set"


def test_node_item_creation(qapp, sample_node, sample_graph):
    """Verify nodes can be created successfully."""
    node_item = NodeItem(sample_node, sample_graph)
    
    assert node_item is not None
    assert node_item.node == sample_node
    assert node_item.width > 0
    assert node_item.height > 0


def test_node_item_has_required_constants(qapp, sample_node, sample_graph):
    """Verify NodeItem class has required constant attributes."""
    node_item = NodeItem(sample_node, sample_graph)
    
    # Check class constants
    assert hasattr(NodeItem, 'MIN_PROMPT_HEIGHT')
    assert hasattr(NodeItem, 'MIN_OUTPUT_HEIGHT')
    assert hasattr(NodeItem, 'RESIZE_HANDLE_SIZE')
    assert hasattr(NodeItem, 'MIN_HEIGHT')
    assert hasattr(NodeItem, 'MAX_HEIGHT')
    assert hasattr(NodeItem, 'MAX_WIDTH')
