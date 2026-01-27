"""
Integration tests for MainWindow with controllers.

These tests verify that the controllers integrate correctly with
the existing UI components and workflows.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from core.graph_controller import GraphController
from core.tab_controller import TabController
from core.graph import Graph
from core.node import Node


class TestGraphControllerIntegration:
    """Integration tests for GraphController with file system."""
    
    def test_full_file_workflow(self, tmp_path, sample_graph):
        """Test complete file workflow: create -> save -> load -> modify -> save."""
        # Create controller with graph
        controller1 = GraphController(graph=sample_graph)
        save_path = tmp_path / "integration_test.json"
        
        # Save
        result = controller1.save_graph(str(save_path))
        assert result is True
        assert save_path.exists()
        
        # Load in new controller
        loaded_graph = GraphController.load_graph(str(save_path))
        controller2 = GraphController(graph=loaded_graph, file_path=str(save_path))
        
        # Verify loaded correctly
        assert len(controller2.graph.nodes) == 3
        assert len(controller2.graph.links) == 2
        assert controller2.is_dirty is False
        
        # Modify
        new_node = Node(name="New_Node", prompt="New prompt")
        controller2.graph.add_node(new_node)
        controller2.mark_dirty()
        assert controller2.is_dirty is True
        
        # Save again
        controller2.save_graph()
        assert controller2.is_dirty is False
        
        # Reload and verify modification persisted
        final_graph = GraphController.load_graph(str(save_path))
        assert len(final_graph.nodes) == 4
    
    def test_merge_workflow(self, tmp_path, sample_graph):
        """Test merging multiple graphs."""
        # Create main graph
        main_controller = GraphController()
        
        # Create merge sources
        source1_path = tmp_path / "source1.json"
        source2_path = tmp_path / "source2.json"
        
        with open(source1_path, 'w') as f:
            json.dump(sample_graph.to_dict(), f)
        
        # Create second graph with different nodes
        graph2 = Graph()
        node = Node(name="Merge_Node", prompt="Merge test")
        graph2.add_node(node)
        
        with open(source2_path, 'w') as f:
            json.dump(graph2.to_dict(), f)
        
        # Merge both
        result1 = main_controller.merge_graph(str(source1_path))
        assert result1['nodes_added'] == 3
        
        result2 = main_controller.merge_graph(str(source2_path))
        assert result2['nodes_added'] == 1
        
        # Verify total
        assert len(main_controller.graph.nodes) == 4
        assert main_controller.is_dirty is True


class TestTabControllerIntegration:
    """Integration tests for TabController with GraphController."""
    
    def test_tab_with_graph_controller_workflow(self, mock_queue_manager, sample_graph):
        """Test tab controller managing graph controllers."""
        tab_controller = TabController(queue_manager=mock_queue_manager)
        
        # Create tab with graph
        tab_info = tab_controller.create_tab(graph=sample_graph, file_path="/test/graph.json")
        
        # Verify graph controller is set up correctly
        assert tab_info.graph_controller.graph == sample_graph
        assert tab_info.graph_controller.file_path == "/test/graph.json"
        assert tab_info.graph_controller.is_dirty is False
        
        # Modify graph through controller
        new_node = Node(name="Test_Node", prompt="Test")
        tab_info.graph_controller.graph.add_node(new_node)
        tab_controller.mark_tab_dirty(tab_info.tab_id)
        
        # Verify dirty state propagated
        assert tab_controller.has_unsaved_changes(tab_info.tab_id)
        assert tab_info.graph_controller.is_dirty is True
    
    def test_multiple_tabs_with_different_graphs(self, mock_queue_manager, sample_graph):
        """Test managing multiple tabs with different graphs."""
        tab_controller = TabController(queue_manager=mock_queue_manager)
        
        # Create tabs with different graphs
        tab1 = tab_controller.create_tab(graph=sample_graph, file_path="/test/graph1.json")
        tab2 = tab_controller.create_tab(graph=Graph(), file_path="/test/graph2.json")
        tab3 = tab_controller.create_tab(graph=Graph())
        
        # Verify each has its own graph
        assert len(tab1.graph_controller.graph.nodes) == 3
        assert len(tab2.graph_controller.graph.nodes) == 0
        assert len(tab3.graph_controller.graph.nodes) == 0
        
        # Modify one shouldn't affect others
        new_node = Node(name="Tab2_Node", prompt="Tab 2")
        tab2.graph_controller.graph.add_node(new_node)
        
        assert len(tab1.graph_controller.graph.nodes) == 3
        assert len(tab2.graph_controller.graph.nodes) == 1
        assert len(tab3.graph_controller.graph.nodes) == 0
    
    def test_tab_save_workflow(self, tmp_path, mock_queue_manager, sample_graph):
        """Test saving through tab controller."""
        tab_controller = TabController(queue_manager=mock_queue_manager)
        
        # Create tab
        tab_info = tab_controller.create_tab(graph=sample_graph)
        tab_controller.mark_tab_dirty(tab_info.tab_id)
        
        # Save through graph controller
        save_path = tmp_path / "tab_save.json"
        result = tab_info.graph_controller.save_graph(str(save_path))
        
        assert result is True
        assert save_path.exists()
        assert tab_info.graph_controller.is_dirty is False
        
        # Tab should reflect clean state
        assert not tab_controller.has_unsaved_changes(tab_info.tab_id)


class TestControllerErrorHandling:
    """Test error handling in controllers."""
    
    def test_graph_controller_handles_invalid_file(self, tmp_path):
        """Test GraphController handles invalid files gracefully."""
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(json.JSONDecodeError):
            GraphController.load_graph(str(invalid_file))
    
    def test_graph_controller_handles_missing_file(self):
        """Test GraphController handles missing files gracefully."""
        with pytest.raises(FileNotFoundError):
            GraphController.load_graph("/nonexistent/file.json")
    
    def test_tab_controller_handles_invalid_operations(self, mock_queue_manager):
        """Test TabController handles invalid operations gracefully."""
        controller = TabController(queue_manager=mock_queue_manager)
        
        # Try to close non-existent tab
        result = controller.close_tab("nonexistent-id")
        assert result is False
        
        # Try to activate non-existent tab
        result = controller.set_active_tab("nonexistent-id")
        assert result is False
        
        # Try to get non-existent tab
        tab = controller.get_tab("nonexistent-id")
        assert tab is None


class TestControllerSignals:
    """Test that controller signals work correctly."""
    
    def test_tab_controller_signals(self, mock_queue_manager):
        """Test all tab controller signals are emitted."""
        controller = TabController(queue_manager=mock_queue_manager)
        
        # Set up signal spies
        created_spy = Mock()
        closed_spy = Mock()
        activated_spy = Mock()
        dirty_spy = Mock()
        
        controller.tab_created.connect(created_spy)
        controller.tab_closed.connect(closed_spy)
        controller.tab_activated.connect(activated_spy)
        controller.tab_dirty_changed.connect(dirty_spy)
        
        # Create tab
        tab_info = controller.create_tab()
        assert created_spy.call_count == 1
        
        # Activate
        controller.set_active_tab(tab_info.tab_id)
        assert activated_spy.call_count == 1
        
        # Mark dirty
        controller.mark_tab_dirty(tab_info.tab_id)
        assert dirty_spy.call_count == 1
        
        # Mark clean
        controller.mark_tab_clean(tab_info.tab_id)
        assert dirty_spy.call_count == 2
        
        # Close
        controller.close_tab(tab_info.tab_id, force=True)
        assert closed_spy.call_count == 1


class TestControllerStateConsistency:
    """Test that controller state remains consistent."""
    
    def test_graph_controller_state_after_operations(self, tmp_path, sample_graph):
        """Test GraphController maintains consistent state."""
        controller = GraphController(graph=sample_graph)
        save_path = tmp_path / "state_test.json"
        
        # Initial state
        assert controller.is_dirty is False
        assert controller.file_path is None
        
        # After marking dirty
        controller.mark_dirty()
        assert controller.is_dirty is True
        
        # After save
        controller.save_graph(str(save_path))
        assert controller.is_dirty is False
        assert controller.file_path == str(save_path)
        
        # After merge
        merge_path = tmp_path / "merge.json"
        with open(merge_path, 'w') as f:
            json.dump(Graph().to_dict(), f)
        
        controller.merge_graph(str(merge_path))
        assert controller.is_dirty is True  # Merge should mark dirty
    
    def test_tab_controller_state_after_operations(self, mock_queue_manager):
        """Test TabController maintains consistent state."""
        controller = TabController(queue_manager=mock_queue_manager)
        
        # Create tabs
        tab1 = controller.create_tab()
        tab2 = controller.create_tab()
        tab3 = controller.create_tab()
        
        assert controller.get_tab_count() == 3
        
        # Activate tab2
        controller.set_active_tab(tab2.tab_id)
        assert controller.get_active_tab() == tab2
        
        # Close tab2
        controller.close_tab(tab2.tab_id)
        assert controller.get_tab_count() == 2
        
        # Active should switch to another tab
        active = controller.get_active_tab()
        assert active in [tab1, tab3]
        
        # Close all
        controller.close_all_tabs(force=True)
        assert controller.get_tab_count() == 0
        assert controller.get_active_tab() is None


class TestControllerPerformance:
    """Test controller performance with larger datasets."""
    
    def test_graph_controller_with_many_nodes(self, tmp_path):
        """Test GraphController handles large graphs efficiently."""
        # Create graph with many nodes
        graph = Graph()
        for i in range(100):
            node = Node(name=f"Node_{i:04d}", prompt=f"Prompt {i}")
            node.pos_x = (i % 10) * 100
            node.pos_y = (i // 10) * 100
            graph.add_node(node)
        
        # Save
        controller = GraphController(graph=graph)
        save_path = tmp_path / "large_graph.json"
        
        result = controller.save_graph(str(save_path))
        assert result is True
        
        # Load
        loaded_graph = GraphController.load_graph(str(save_path))
        assert len(loaded_graph.nodes) == 100
    
    def test_tab_controller_with_many_tabs(self, mock_queue_manager):
        """Test TabController handles many tabs efficiently."""
        controller = TabController(queue_manager=mock_queue_manager)
        
        # Create many tabs
        tabs = []
        for i in range(50):
            tab = controller.create_tab(file_path=f"/test/graph_{i}.json")
            tabs.append(tab)
        
        assert controller.get_tab_count() == 50
        
        # Get all tabs
        all_tabs = controller.get_all_tabs()
        assert len(all_tabs) == 50
        
        # Find specific tab
        found = controller.find_tab_by_file_path("/test/graph_25.json")
        assert found == tabs[25]
