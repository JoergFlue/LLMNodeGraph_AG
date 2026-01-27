"""
Shared pytest fixtures for AntiGravity tests.

Provides common test infrastructure including Qt application setup,
mock objects, and temporary file fixtures.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal

from core.graph import Graph
from core.node import Node
from services.llm_queue_manager import LLMQueueManager


@pytest.fixture(scope="session")
def qapp():
    """
    Create a shared QApplication instance for all tests.
    
    Qt requires a QApplication instance to exist before creating any widgets.
    This fixture ensures one exists for the entire test session.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def sample_graph():
    """
    Create a sample graph with test data.
    
    Returns a Graph with 3 nodes and 2 links for testing.
    """
    graph = Graph()
    
    # Create nodes
    node1 = Node(name="Node_0001", prompt="Test prompt 1")
    node1.pos_x = 100
    node1.pos_y = 100
    
    node2 = Node(name="Node_0002", prompt="Test prompt 2")
    node2.pos_x = 400
    node2.pos_y = 100
    
    node3 = Node(name="Node_0003", prompt="Test prompt 3")
    node3.pos_x = 400
    node3.pos_y = 400
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(node3)
    
    # Create links
    link1 = graph.add_link(node1.id, node2.id)
    link2 = graph.add_link(node2.id, node3.id)
    
    return graph


@pytest.fixture
def empty_graph():
    """Create an empty graph for testing."""
    return Graph()


@pytest.fixture
def mock_queue_manager():
    """
    Create a mock LLMQueueManager for testing.
    
    Provides mock implementations of all queue manager signals and methods.
    """
    mock = Mock(spec=LLMQueueManager)
    
    # Create mock signals
    mock.task_started = Mock()
    mock.task_started.connect = Mock()
    mock.task_started.emit = Mock()
    
    mock.task_finished = Mock()
    mock.task_finished.connect = Mock()
    mock.task_finished.emit = Mock()
    
    mock.task_failed = Mock()
    mock.task_failed.connect = Mock()
    mock.task_failed.emit = Mock()
    
    mock.task_queued = Mock()
    mock.task_queued.connect = Mock()
    mock.task_queued.emit = Mock()
    
    # Mock methods
    mock.submit_task = Mock()
    mock.cancel_task = Mock()
    mock.shutdown = Mock()
    
    return mock


@pytest.fixture
def temp_graph_file(tmp_path, sample_graph):
    """
    Create a temporary graph file for I/O testing.
    
    Args:
        tmp_path: pytest's temporary directory fixture
        sample_graph: Sample graph fixture
        
    Returns:
        Path to the temporary JSON file
    """
    file_path = tmp_path / "test_graph.json"
    
    # Write sample graph to file
    data = sample_graph.to_dict()
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return file_path


@pytest.fixture
def temp_empty_file(tmp_path):
    """
    Create a temporary empty JSON file.
    
    Useful for testing file creation and "Save As" operations.
    """
    file_path = tmp_path / "empty_graph.json"
    return file_path


@pytest.fixture
def invalid_graph_file(tmp_path):
    """
    Create a temporary file with invalid JSON.
    
    Useful for testing error handling.
    """
    file_path = tmp_path / "invalid.json"
    with open(file_path, 'w') as f:
        f.write("{ invalid json content }")
    
    return file_path


@pytest.fixture
def graph_with_collision(sample_graph):
    """
    Create a second graph with node IDs that collide with sample_graph.
    
    Useful for testing merge collision handling.
    """
    graph = Graph()
    
    # Get first node ID from sample_graph
    first_node_id = list(sample_graph.nodes.keys())[0]
    
    # Create node with same ID (collision)
    node = Node(id=first_node_id, name="Collision_Node", prompt="Collision test")
    node.pos_x = 200
    node.pos_y = 200
    
    graph.add_node(node)
    
    return graph


@pytest.fixture
def mock_file_dialog():
    """
    Create a mock QFileDialog for testing file operations.
    
    Returns a mock that can be configured to return specific file paths.
    """
    mock = Mock()
    mock.getOpenFileName = Mock(return_value=("", ""))
    mock.getSaveFileName = Mock(return_value=("", ""))
    return mock


@pytest.fixture
def graph_dict_data() -> Dict[str, Any]:
    """
    Return raw dictionary data for a graph.
    
    Useful for testing graph loading without file I/O.
    """
    return {
        "version": "2.0",
        "app_settings": {
            "global_token_limit": 16384
        },
        "nodes": [
            {
                "id": "test-node-1",
                "name": "Test_0001",
                "prompt": "Test prompt",
                "cached_output": "",
                "is_dirty": False,
                "pos": [100, 100],
                "width": 300,
                "height": 400,
                "input_links": [],
                "config": {
                    "provider": "Default",
                    "model": "llama3",
                    "max_tokens": 4096,
                    "trace_depth": 3
                }
            }
        ],
        "links": []
    }
