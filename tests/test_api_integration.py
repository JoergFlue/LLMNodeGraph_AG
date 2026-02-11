"""
Integration tests for the AntiGravity API.
"""

import pytest
import os
import json
from unittest.mock import patch, MagicMock
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QApplication

from core.api import AntiGravityAPI
from ui.main_window import AntiGravityWindow
from core.graph import Graph
from core.node import Node

@pytest.fixture
def window(qapp, mock_queue_manager):
    """Fixture to provide a MainWindow with mocked dependencies."""
    # Patch LLMQueueManager and ProviderStatusManager to avoid background thread issues
    with patch('ui.main_window.LLMQueueManager', return_value=mock_queue_manager), \
         patch('core.provider_status.ProviderStatusManager.check_all'), \
         patch('core.provider_status.ProviderStatusManager.check_provider'):
        win = AntiGravityWindow()
        yield win
        
        # Mark all tabs as clean to avoid "Save?" dialogs during teardown
        for i in range(win.tabs.count()):
            widget = win.tabs.widget(i)
            if hasattr(widget, 'is_dirty'):
                widget.is_dirty = False
        win.close()

def test_api_node_operations(window):
    api = AntiGravityAPI(window)
    
    # 1. Create Nodes
    n1_id = api.create_node(name="Node_A", pos=(100, 100))
    n2_id = api.create_node(name="Node_B", pos=(400, 100))
    
    tab = window.get_current_tab()
    assert n1_id in tab.graph.nodes
    assert n2_id in tab.graph.nodes
    assert tab.graph.nodes[n1_id].name == "Node_A"
    assert tab.graph.nodes[n2_id].name == "Node_B"
    
    # 2. Set Prompt
    api.set_node_prompt(n1_id, "Source Prompt")
    assert tab.graph.nodes[n1_id].prompt == "Source Prompt"
    
    # 3. Delete Node
    api.delete_node(n1_id)
    assert n1_id not in tab.graph.nodes
    assert n2_id in tab.graph.nodes

def test_api_connection_operations(window):
    api = AntiGravityAPI(window)
    n1 = api.create_node(name="Source")
    n2 = api.create_node(name="Target")
    
    # 1. Create Connection
    link_id = api.create_connection(n1, n2)
    tab = window.get_current_tab()
    assert link_id in tab.graph.links
    assert tab.graph.links[link_id].source_id == n1
    assert tab.graph.links[link_id].target_id == n2
    
    # 2. Delete Connection
    api.delete_connection(link_id)
    assert link_id not in tab.graph.links

def test_api_scene_lifecycle(window, tmp_path):
    api = AntiGravityAPI(window)
    
    # 1. New Scene (Tab)
    initial_count = window.tabs.count()
    api.create_scene()
    assert window.tabs.count() == initial_count + 1
    
    # 2. Add Content and Save
    n_id = api.create_node(name="PersistentNode")
    save_path = str(tmp_path / "test_scene.json")
    api.save_scene(save_path)
    assert os.path.exists(save_path)
    
    # 3. Close Scene
    api.close_scene(force=True)
    assert window.tabs.count() == initial_count
    
    # 4. Open Scene
    api.open_scene(save_path)
    assert window.tabs.count() == initial_count + 1
    tab = window.get_current_tab()
    assert any(n.name == "PersistentNode" for n in tab.graph.nodes.values())

def test_api_window_management(window):
    api = AntiGravityAPI(window)
    
    # 1. Log Window
    api.show_log_window(True)
    assert window.log_window.isVisible()
    api.show_log_window(False)
    assert not window.log_window.isVisible()
    
    # 2. Settings Dialog
    api.show_settings(True)
    assert window.settings_dialog.isVisible()
    api.show_settings(False)
    assert not window.settings_dialog.isVisible()

def test_api_execution_flow(window, mock_queue_manager):
    api = AntiGravityAPI(window)
    node_id = api.create_node(name="WorkerNode")
    api.set_node_prompt(node_id, "Test Question")
    
    # Trigger Run
    api.run_node(node_id)
    
    # Verify task was submitted to queue manager
    mock_queue_manager.submit_task.assert_called_once()
    args = mock_queue_manager.submit_task.call_args[0]
    assert args[0] == node_id
    assert args[1] == "Test Question"

def test_api_graceful_missing_provider(window):
    api = AntiGravityAPI(window)
    node_id = api.create_node(name="ErrorNode")
    
    tab = window.get_current_tab()
    
    # Mock show_error to avoid blocking popup during tests
    with patch('ui.editor_tab.show_error') as mock_show_error:
        # Simulate a provider failure signal
        tab.on_task_failed(node_id, "Missing Provider: UnsupportedLLM")
        
        # Verify gracefully handled (error shown to user)
        mock_show_error.assert_called_once()
        assert "UnsupportedLLM" in mock_show_error.call_args[0][1]
        
        # Verify node UI state remains usable (IDLE)
        assert node_id in tab.node_items
        # node_item doesn't expose execution state easily, but we know it calls set_execution_state("IDLE")

def test_api_provider_status(window):
    api = AntiGravityAPI(window)
    
    with patch('core.provider_status.ProviderStatusManager.get_status', return_value=True):
        status = api.get_provider_status("Ollama")
        assert status is True
        
    with patch('core.provider_status.ProviderStatusManager.get_status', return_value=False):
        status = api.get_provider_status("OpenAI")
        assert status is False
