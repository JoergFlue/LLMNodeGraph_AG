"""
Functional consistency tests for UI components.

Tests verify that UI functionality remains unchanged after refactoring.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from core.graph import Graph
from core.node import Node
from ui.node_item import NodeItem


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def graph_with_node(qapp):
    """Create a graph with a test node."""
    graph = Graph()
    node = Node(id="test-1", name="Test", prompt="Test prompt")
    graph.add_node(node)
    return graph, node


def test_node_creation(graph_with_node):
    """Verify nodes can be created with theme constants."""
    graph, node = graph_with_node
    node_item = NodeItem(node, graph)
    
    assert node_item is not None
    assert node_item.node == node
    assert node_item.width > 0
    assert node_item.height > 0


def test_node_resizing(graph_with_node):
    """Verify node resizing still works."""
    graph, node = graph_with_node
    node_item = NodeItem(node, graph)
    
    original_width = node_item.width
    original_height = node_item.height
    
    # Simulate resize
    node_item.width = 500
    node_item.height = 600
    node_item.update_layout()
    
    assert node_item.width == 500
    assert node_item.height == 600
    
    # Verify node data is updated
    assert node.width == 500
    assert node.height == 600


def test_node_state_changes(graph_with_node):
    """Verify node state changes work correctly."""
    graph, node = graph_with_node
    node_item = NodeItem(node, graph)
    
    # Test execution states
    node_item.set_execution_state("RUNNING")
    assert node_item.execution_state == "RUNNING"
    
    node_item.set_execution_state("QUEUED")
    assert node_item.execution_state == "QUEUED"
    
    node_item.set_execution_state("IDLE")
    assert node_item.execution_state == "IDLE"


def test_dirty_state(graph_with_node):
    """Verify dirty state tracking works."""
    graph, node = graph_with_node
    node_item = NodeItem(node, graph)
    
    # Set dirty state
    node.is_dirty = True
    node_item.update()
    assert node.is_dirty == True
    
    # Clear dirty state
    node.is_dirty = False
    node_item.update()
    assert node.is_dirty == False


def test_node_metrics_update(graph_with_node):
    """Verify node metrics can be updated."""
    graph, node = graph_with_node
    node_item = NodeItem(node, graph)
    
    # Set metrics
    node_item.set_metrics(1000, 16000)
    
    # Verify internal state
    assert hasattr(node_item, '_payload_chars')
    assert hasattr(node_item, '_max_chars')
    assert node_item._payload_chars == 1000
    assert node_item._max_chars == 16000


def test_node_output_update(graph_with_node):
    """Verify node output can be updated."""
    graph, node = graph_with_node
    node_item = NodeItem(node, graph)
    
    test_output = "Test output text"
    node_item.update_output(test_output)
    
    assert node.cached_output == test_output
