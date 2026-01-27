"""
Unit tests for GraphController.

Tests all graph file operations including creation, loading, saving,
merging, and error handling.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from core.graph_controller import GraphController
from core.graph import Graph
from core.node import Node


class TestGraphControllerCreation:
    """Test graph creation operations."""
    
    def test_create_new_graph_static(self):
        """Test static method creates empty graph."""
        graph = GraphController.create_new_graph()
        
        assert isinstance(graph, Graph)
        assert len(graph.nodes) == 0
        assert len(graph.links) == 0
    
    def test_controller_init_empty(self):
        """Test controller initialization with no graph."""
        controller = GraphController()
        
        assert controller.graph is not None
        assert isinstance(controller.graph, Graph)
        assert controller.file_path is None
        assert controller.is_dirty is False
    
    def test_controller_init_with_graph(self, sample_graph):
        """Test controller initialization with existing graph."""
        controller = GraphController(graph=sample_graph, file_path="/test/path.json")
        
        assert controller.graph == sample_graph
        assert controller.file_path == "/test/path.json"
        assert controller.is_dirty is False


class TestGraphControllerLoading:
    """Test graph loading operations."""
    
    def test_load_graph_success(self, temp_graph_file):
        """Test successful graph loading."""
        graph = GraphController.load_graph(str(temp_graph_file))
        
        assert isinstance(graph, Graph)
        assert len(graph.nodes) == 3
        assert len(graph.links) == 2
    
    def test_load_graph_nonexistent_file(self):
        """Test loading from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            GraphController.load_graph("/nonexistent/path.json")
    
    def test_load_graph_invalid_json(self, invalid_graph_file):
        """Test loading invalid JSON raises error."""
        with pytest.raises(json.JSONDecodeError):
            GraphController.load_graph(str(invalid_graph_file))
    
    def test_load_graph_sets_properties(self, temp_graph_file):
        """Test that loaded graph has correct properties."""
        graph = GraphController.load_graph(str(temp_graph_file))
        
        # Check global settings
        assert graph.global_token_limit == 16384
        
        # Check nodes have required properties
        for node in graph.nodes.values():
            assert hasattr(node, 'id')
            assert hasattr(node, 'name')
            assert hasattr(node, 'prompt')


class TestGraphControllerSaving:
    """Test graph saving operations."""
    
    def test_save_graph_new_file(self, tmp_path, sample_graph):
        """Test saving graph to new file."""
        controller = GraphController(graph=sample_graph)
        save_path = tmp_path / "new_graph.json"
        
        result = controller.save_graph(str(save_path))
        
        assert result is True
        assert save_path.exists()
        assert controller.file_path == str(save_path)
        assert controller.is_dirty is False
    
    def test_save_graph_overwrite(self, temp_graph_file, sample_graph):
        """Test overwriting existing file."""
        controller = GraphController(graph=sample_graph)
        
        result = controller.save_graph(str(temp_graph_file))
        
        assert result is True
        assert temp_graph_file.exists()
    
    def test_save_graph_no_path_raises_error(self, sample_graph):
        """Test saving without path raises error."""
        controller = GraphController(graph=sample_graph)
        
        with pytest.raises(ValueError, match="No file path specified"):
            controller.save_graph()
    
    def test_save_graph_uses_stored_path(self, tmp_path, sample_graph):
        """Test saving uses stored file path."""
        save_path = tmp_path / "stored_path.json"
        controller = GraphController(graph=sample_graph, file_path=str(save_path))
        
        result = controller.save_graph()
        
        assert result is True
        assert save_path.exists()
    
    def test_save_graph_marks_clean(self, tmp_path, sample_graph):
        """Test saving marks graph as clean."""
        controller = GraphController(graph=sample_graph)
        controller.mark_dirty()
        save_path = tmp_path / "test.json"
        
        assert controller.is_dirty is True
        controller.save_graph(str(save_path))
        assert controller.is_dirty is False
    
    def test_save_graph_valid_json(self, tmp_path, sample_graph):
        """Test saved file contains valid JSON."""
        controller = GraphController(graph=sample_graph)
        save_path = tmp_path / "valid.json"
        
        controller.save_graph(str(save_path))
        
        # Verify file can be loaded as JSON
        with open(save_path, 'r') as f:
            data = json.load(f)
        
        assert "version" in data
        assert "nodes" in data
        assert "links" in data
        assert len(data["nodes"]) == 3
        assert len(data["links"]) == 2


class TestGraphControllerMerging:
    """Test graph merging operations."""
    
    def test_merge_graph_success(self, tmp_path, sample_graph):
        """Test successful graph merge."""
        # Create controller with initial graph
        controller = GraphController(graph=Graph())
        
        # Create source file
        source_path = tmp_path / "merge_source.json"
        with open(source_path, 'w') as f:
            json.dump(sample_graph.to_dict(), f)
        
        # Perform merge
        result = controller.merge_graph(str(source_path))
        
        assert result['nodes_added'] == 3
        assert result['links_added'] == 2
        assert controller.is_dirty is True
    
    def test_merge_graph_nonexistent_file(self, sample_graph):
        """Test merging from non-existent file raises error."""
        controller = GraphController(graph=sample_graph)
        
        with pytest.raises(FileNotFoundError):
            controller.merge_graph("/nonexistent/merge.json")
    
    def test_merge_graph_invalid_json(self, invalid_graph_file, sample_graph):
        """Test merging invalid JSON raises error."""
        controller = GraphController(graph=sample_graph)
        
        with pytest.raises(json.JSONDecodeError):
            controller.merge_graph(str(invalid_graph_file))
    
    def test_merge_graph_marks_dirty(self, tmp_path, sample_graph):
        """Test merge marks graph as dirty."""
        controller = GraphController(graph=Graph())
        controller.mark_clean()
        
        source_path = tmp_path / "merge.json"
        with open(source_path, 'w') as f:
            json.dump(sample_graph.to_dict(), f)
        
        assert controller.is_dirty is False
        controller.merge_graph(str(source_path))
        assert controller.is_dirty is True
    
    def test_merge_graph_with_collisions(self, tmp_path, sample_graph):
        """Test merge handles ID collisions correctly."""
        # Create controller with sample graph
        controller = GraphController(graph=sample_graph)
        original_node_ids = set(sample_graph.nodes.keys())
        
        # Create merge source with same graph (will have ID collisions)
        source_path = tmp_path / "collision.json"
        with open(source_path, 'w') as f:
            json.dump(sample_graph.to_dict(), f)
        
        # Perform merge
        result = controller.merge_graph(str(source_path))
        
        # Should have doubled the nodes
        assert len(controller.graph.nodes) == 6
        
        # New nodes should have different IDs
        new_node_ids = set(controller.graph.nodes.keys())
        assert len(new_node_ids) == 6  # All unique


class TestGraphControllerDirtyState:
    """Test dirty state tracking."""
    
    def test_initial_state_clean(self):
        """Test new controller starts clean."""
        controller = GraphController()
        assert controller.is_dirty is False
    
    def test_mark_dirty(self):
        """Test marking graph as dirty."""
        controller = GraphController()
        controller.mark_dirty()
        assert controller.is_dirty is True
    
    def test_mark_clean(self):
        """Test marking graph as clean."""
        controller = GraphController()
        controller.mark_dirty()
        controller.mark_clean()
        assert controller.is_dirty is False
    
    def test_save_clears_dirty(self, tmp_path, sample_graph):
        """Test save operation clears dirty flag."""
        controller = GraphController(graph=sample_graph)
        controller.mark_dirty()
        
        save_path = tmp_path / "test.json"
        controller.save_graph(str(save_path))
        
        assert controller.is_dirty is False


class TestGraphControllerFilePathManagement:
    """Test file path management."""
    
    def test_initial_file_path_none(self):
        """Test new controller has no file path."""
        controller = GraphController()
        assert controller.file_path is None
    
    def test_set_file_path(self):
        """Test setting file path."""
        controller = GraphController()
        controller.file_path = "/test/path.json"
        assert controller.file_path == "/test/path.json"
    
    def test_save_updates_file_path(self, tmp_path, sample_graph):
        """Test save updates file path."""
        controller = GraphController(graph=sample_graph)
        save_path = tmp_path / "test.json"
        
        controller.save_graph(str(save_path))
        
        assert controller.file_path == str(save_path)
    
    def test_get_display_name_with_path(self):
        """Test display name with file path."""
        controller = GraphController()
        controller.file_path = "/test/folder/my_graph.json"
        
        assert controller.get_display_name() == "my_graph.json"
    
    def test_get_display_name_without_path(self):
        """Test display name without file path."""
        controller = GraphController()
        assert controller.get_display_name() == "Untitled"
    
    def test_get_window_title_clean(self):
        """Test window title for clean graph."""
        controller = GraphController()
        controller.file_path = "/test/graph.json"
        
        assert controller.get_window_title() == "graph.json"
    
    def test_get_window_title_dirty(self):
        """Test window title for dirty graph."""
        controller = GraphController()
        controller.file_path = "/test/graph.json"
        controller.mark_dirty()
        
        assert controller.get_window_title() == "graph.json*"
    
    def test_get_window_title_untitled_dirty(self):
        """Test window title for untitled dirty graph."""
        controller = GraphController()
        controller.mark_dirty()
        
        assert controller.get_window_title() == "Untitled*"


class TestGraphControllerIntegration:
    """Integration tests for complete workflows."""
    
    def test_create_save_load_workflow(self, tmp_path):
        """Test complete create -> save -> load workflow."""
        # Create and populate graph
        controller1 = GraphController()
        node = Node(name="Test_0001", prompt="Test")
        controller1.graph.add_node(node)
        
        # Save
        save_path = tmp_path / "workflow.json"
        controller1.save_graph(str(save_path))
        
        # Load in new controller
        graph2 = GraphController.load_graph(str(save_path))
        
        # Verify
        assert len(graph2.nodes) == 1
        assert list(graph2.nodes.values())[0].name == "Test_0001"
    
    def test_load_modify_save_workflow(self, temp_graph_file):
        """Test load -> modify -> save workflow."""
        # Load
        graph = GraphController.load_graph(str(temp_graph_file))
        controller = GraphController(graph=graph, file_path=str(temp_graph_file))
        
        # Modify
        node = Node(name="New_Node", prompt="New")
        controller.graph.add_node(node)
        controller.mark_dirty()
        
        # Save
        controller.save_graph()
        
        # Reload and verify
        graph2 = GraphController.load_graph(str(temp_graph_file))
        assert len(graph2.nodes) == 4  # Original 3 + 1 new
    
    def test_merge_multiple_graphs(self, tmp_path, sample_graph):
        """Test merging multiple graphs."""
        controller = GraphController()
        
        # Create two source files
        source1 = tmp_path / "source1.json"
        source2 = tmp_path / "source2.json"
        
        with open(source1, 'w') as f:
            json.dump(sample_graph.to_dict(), f)
        with open(source2, 'w') as f:
            json.dump(sample_graph.to_dict(), f)
        
        # Merge both
        result1 = controller.merge_graph(str(source1))
        result2 = controller.merge_graph(str(source2))
        
        # Should have 6 nodes total
        assert len(controller.graph.nodes) == 6
        assert result1['nodes_added'] == 3
        assert result2['nodes_added'] == 3
