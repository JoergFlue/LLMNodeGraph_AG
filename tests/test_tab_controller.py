"""
Unit tests for TabController.

Tests all tab management operations including creation, closing,
activation, dirty state tracking, and multi-tab scenarios.
"""

import pytest
from unittest.mock import Mock, MagicMock

from core.tab_controller import TabController, TabInfo
from core.graph import Graph
from core.node import Node


class TestTabControllerCreation:
    """Test tab creation operations."""
    
    def test_controller_init(self, mock_queue_manager):
        """Test controller initialization."""
        controller = TabController(queue_manager=mock_queue_manager)
        
        assert controller.queue_manager == mock_queue_manager
        assert controller.get_tab_count() == 0
        assert controller.get_active_tab() is None
    
    def test_create_tab_empty(self, mock_queue_manager):
        """Test creating tab with no graph."""
        controller = TabController(queue_manager=mock_queue_manager)
        
        tab_info = controller.create_tab()
        
        assert tab_info is not None
        assert tab_info.tab_id is not None
        assert tab_info.graph_controller is not None
        assert len(tab_info.graph_controller.graph.nodes) == 0
        assert controller.get_tab_count() == 1
    
    def test_create_tab_with_graph(self, mock_queue_manager, sample_graph):
        """Test creating tab with existing graph."""
        controller = TabController(queue_manager=mock_queue_manager)
        
        tab_info = controller.create_tab(graph=sample_graph)
        
        assert tab_info.graph_controller.graph == sample_graph
        assert len(tab_info.graph_controller.graph.nodes) == 3
    
    def test_create_tab_with_file_path(self, mock_queue_manager):
        """Test creating tab with file path."""
        controller = TabController(queue_manager=mock_queue_manager)
        
        tab_info = controller.create_tab(file_path="/test/path.json")
        
        assert tab_info.graph_controller.file_path == "/test/path.json"
    
    def test_create_tab_emits_signal(self, mock_queue_manager):
        """Test tab creation emits signal."""
        controller = TabController(queue_manager=mock_queue_manager)
        signal_spy = Mock()
        controller.tab_created.connect(signal_spy)
        
        tab_info = controller.create_tab()
        
        signal_spy.assert_called_once()
        args = signal_spy.call_args[0]
        assert args[0] == tab_info.tab_id
        assert args[1] == "Untitled"  # Default display name
    
    def test_create_multiple_tabs(self, mock_queue_manager):
        """Test creating multiple tabs."""
        controller = TabController(queue_manager=mock_queue_manager)
        
        tab1 = controller.create_tab()
        tab2 = controller.create_tab()
        tab3 = controller.create_tab()
        
        assert controller.get_tab_count() == 3
        assert tab1.tab_id != tab2.tab_id != tab3.tab_id


class TestTabControllerClosing:
    """Test tab closing operations."""
    
    def test_close_tab_clean(self, mock_queue_manager):
        """Test closing tab with no unsaved changes."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab_info = controller.create_tab()
        
        result = controller.close_tab(tab_info.tab_id)
        
        assert result is True
        assert controller.get_tab_count() == 0
    
    def test_close_tab_dirty_without_force(self, mock_queue_manager):
        """Test closing dirty tab without force returns False."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab_info = controller.create_tab()
        tab_info.graph_controller.mark_dirty()
        
        result = controller.close_tab(tab_info.tab_id, force=False)
        
        assert result is False
        assert controller.get_tab_count() == 1
    
    def test_close_tab_dirty_with_force(self, mock_queue_manager):
        """Test closing dirty tab with force succeeds."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab_info = controller.create_tab()
        tab_info.graph_controller.mark_dirty()
        
        result = controller.close_tab(tab_info.tab_id, force=True)
        
        assert result is True
        assert controller.get_tab_count() == 0
    
    def test_close_nonexistent_tab(self, mock_queue_manager):
        """Test closing non-existent tab returns False."""
        controller = TabController(queue_manager=mock_queue_manager)
        
        result = controller.close_tab("nonexistent-id")
        
        assert result is False
    
    def test_close_tab_emits_signal(self, mock_queue_manager):
        """Test tab closing emits signal."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab_info = controller.create_tab()
        signal_spy = Mock()
        controller.tab_closed.connect(signal_spy)
        
        controller.close_tab(tab_info.tab_id)
        
        signal_spy.assert_called_once_with(tab_info.tab_id)
    
    def test_close_all_tabs_clean(self, mock_queue_manager):
        """Test closing all clean tabs."""
        controller = TabController(queue_manager=mock_queue_manager)
        controller.create_tab()
        controller.create_tab()
        controller.create_tab()
        
        result = controller.close_all_tabs()
        
        assert result is True
        assert controller.get_tab_count() == 0
    
    def test_close_all_tabs_with_dirty(self, mock_queue_manager):
        """Test closing all tabs when some are dirty."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab1 = controller.create_tab()
        tab2 = controller.create_tab()
        tab2.graph_controller.mark_dirty()
        
        result = controller.close_all_tabs(force=False)
        
        assert result is False
        assert controller.get_tab_count() > 0
    
    def test_close_all_tabs_force(self, mock_queue_manager):
        """Test force closing all tabs."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab1 = controller.create_tab()
        tab2 = controller.create_tab()
        tab2.graph_controller.mark_dirty()
        
        result = controller.close_all_tabs(force=True)
        
        assert result is True
        assert controller.get_tab_count() == 0


class TestTabControllerActivation:
    """Test tab activation and tracking."""
    
    def test_set_active_tab(self, mock_queue_manager):
        """Test setting active tab."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab_info = controller.create_tab()
        
        result = controller.set_active_tab(tab_info.tab_id)
        
        assert result is True
        assert controller.get_active_tab() == tab_info
        assert tab_info.is_active is True
    
    def test_set_active_nonexistent_tab(self, mock_queue_manager):
        """Test setting non-existent tab as active."""
        controller = TabController(queue_manager=mock_queue_manager)
        
        result = controller.set_active_tab("nonexistent-id")
        
        assert result is False
    
    def test_switch_active_tab(self, mock_queue_manager):
        """Test switching between active tabs."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab1 = controller.create_tab()
        tab2 = controller.create_tab()
        
        controller.set_active_tab(tab1.tab_id)
        assert controller.get_active_tab() == tab1
        assert tab1.is_active is True
        
        controller.set_active_tab(tab2.tab_id)
        assert controller.get_active_tab() == tab2
        assert tab1.is_active is False
        assert tab2.is_active is True
    
    def test_set_active_tab_emits_signal(self, mock_queue_manager):
        """Test setting active tab emits signal."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab_info = controller.create_tab()
        signal_spy = Mock()
        controller.tab_activated.connect(signal_spy)
        
        controller.set_active_tab(tab_info.tab_id)
        
        signal_spy.assert_called_once_with(tab_info.tab_id)
    
    def test_close_active_tab_switches_to_another(self, mock_queue_manager):
        """Test closing active tab switches to another tab."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab1 = controller.create_tab()
        tab2 = controller.create_tab()
        
        controller.set_active_tab(tab1.tab_id)
        controller.close_tab(tab1.tab_id)
        
        # Should auto-switch to remaining tab
        assert controller.get_active_tab() == tab2


class TestTabControllerDirtyState:
    """Test dirty state tracking."""
    
    def test_has_unsaved_changes_clean(self, mock_queue_manager):
        """Test checking unsaved changes on clean tab."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab_info = controller.create_tab()
        
        assert controller.has_unsaved_changes(tab_info.tab_id) is False
    
    def test_has_unsaved_changes_dirty(self, mock_queue_manager):
        """Test checking unsaved changes on dirty tab."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab_info = controller.create_tab()
        tab_info.graph_controller.mark_dirty()
        
        assert controller.has_unsaved_changes(tab_info.tab_id) is True
    
    def test_mark_tab_dirty(self, mock_queue_manager):
        """Test marking tab as dirty."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab_info = controller.create_tab()
        
        controller.mark_tab_dirty(tab_info.tab_id)
        
        assert controller.has_unsaved_changes(tab_info.tab_id) is True
    
    def test_mark_tab_clean(self, mock_queue_manager):
        """Test marking tab as clean."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab_info = controller.create_tab()
        controller.mark_tab_dirty(tab_info.tab_id)
        
        controller.mark_tab_clean(tab_info.tab_id)
        
        assert controller.has_unsaved_changes(tab_info.tab_id) is False
    
    def test_mark_dirty_emits_signal(self, mock_queue_manager):
        """Test marking dirty emits signal."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab_info = controller.create_tab()
        signal_spy = Mock()
        controller.tab_dirty_changed.connect(signal_spy)
        
        controller.mark_tab_dirty(tab_info.tab_id)
        
        signal_spy.assert_called_once_with(tab_info.tab_id, True)
    
    def test_mark_clean_emits_signal(self, mock_queue_manager):
        """Test marking clean emits signal."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab_info = controller.create_tab()
        controller.mark_tab_dirty(tab_info.tab_id)
        signal_spy = Mock()
        controller.tab_dirty_changed.connect(signal_spy)
        
        controller.mark_tab_clean(tab_info.tab_id)
        
        signal_spy.assert_called_once_with(tab_info.tab_id, False)
    
    def test_get_dirty_tabs(self, mock_queue_manager):
        """Test getting all dirty tabs."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab1 = controller.create_tab()
        tab2 = controller.create_tab()
        tab3 = controller.create_tab()
        
        controller.mark_tab_dirty(tab1.tab_id)
        controller.mark_tab_dirty(tab3.tab_id)
        
        dirty_tabs = controller.get_dirty_tabs()
        
        assert len(dirty_tabs) == 2
        assert tab1 in dirty_tabs
        assert tab3 in dirty_tabs
        assert tab2 not in dirty_tabs


class TestTabControllerQueries:
    """Test tab query operations."""
    
    def test_get_tab(self, mock_queue_manager):
        """Test getting tab by ID."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab_info = controller.create_tab()
        
        retrieved = controller.get_tab(tab_info.tab_id)
        
        assert retrieved == tab_info
    
    def test_get_nonexistent_tab(self, mock_queue_manager):
        """Test getting non-existent tab returns None."""
        controller = TabController(queue_manager=mock_queue_manager)
        
        retrieved = controller.get_tab("nonexistent-id")
        
        assert retrieved is None
    
    def test_get_all_tabs(self, mock_queue_manager):
        """Test getting all tabs."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab1 = controller.create_tab()
        tab2 = controller.create_tab()
        tab3 = controller.create_tab()
        
        all_tabs = controller.get_all_tabs()
        
        assert len(all_tabs) == 3
        assert tab1 in all_tabs
        assert tab2 in all_tabs
        assert tab3 in all_tabs
    
    def test_get_tab_count(self, mock_queue_manager):
        """Test getting tab count."""
        controller = TabController(queue_manager=mock_queue_manager)
        
        assert controller.get_tab_count() == 0
        
        controller.create_tab()
        assert controller.get_tab_count() == 1
        
        controller.create_tab()
        assert controller.get_tab_count() == 2
    
    def test_get_tab_display_name(self, mock_queue_manager):
        """Test getting tab display name."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab_info = controller.create_tab(file_path="/test/graph.json")
        
        name = controller.get_tab_display_name(tab_info.tab_id)
        
        assert name == "graph.json"
    
    def test_get_tab_display_name_dirty(self, mock_queue_manager):
        """Test getting display name for dirty tab."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab_info = controller.create_tab(file_path="/test/graph.json")
        controller.mark_tab_dirty(tab_info.tab_id)
        
        name = controller.get_tab_display_name(tab_info.tab_id, include_dirty=True)
        
        assert name == "graph.json*"
    
    def test_find_tab_by_file_path(self, mock_queue_manager):
        """Test finding tab by file path."""
        controller = TabController(queue_manager=mock_queue_manager)
        tab1 = controller.create_tab(file_path="/test/graph1.json")
        tab2 = controller.create_tab(file_path="/test/graph2.json")
        
        found = controller.find_tab_by_file_path("/test/graph2.json")
        
        assert found == tab2
    
    def test_find_tab_by_nonexistent_path(self, mock_queue_manager):
        """Test finding tab by non-existent path returns None."""
        controller = TabController(queue_manager=mock_queue_manager)
        controller.create_tab(file_path="/test/graph.json")
        
        found = controller.find_tab_by_file_path("/nonexistent.json")
        
        assert found is None


class TestTabControllerIntegration:
    """Integration tests for complete workflows."""
    
    def test_create_modify_close_workflow(self, mock_queue_manager, sample_graph):
        """Test complete tab lifecycle."""
        controller = TabController(queue_manager=mock_queue_manager)
        
        # Create tab
        tab_info = controller.create_tab(graph=sample_graph)
        assert controller.get_tab_count() == 1
        
        # Modify (mark dirty)
        controller.mark_tab_dirty(tab_info.tab_id)
        assert controller.has_unsaved_changes(tab_info.tab_id)
        
        # Try to close (should fail without force)
        result = controller.close_tab(tab_info.tab_id, force=False)
        assert result is False
        assert controller.get_tab_count() == 1
        
        # Force close
        result = controller.close_tab(tab_info.tab_id, force=True)
        assert result is True
        assert controller.get_tab_count() == 0
    
    def test_multiple_tabs_workflow(self, mock_queue_manager):
        """Test working with multiple tabs."""
        controller = TabController(queue_manager=mock_queue_manager)
        
        # Create multiple tabs
        tab1 = controller.create_tab(file_path="/test/graph1.json")
        tab2 = controller.create_tab(file_path="/test/graph2.json")
        tab3 = controller.create_tab(file_path="/test/graph3.json")
        
        # Set active tab
        controller.set_active_tab(tab2.tab_id)
        assert controller.get_active_tab() == tab2
        
        # Mark some dirty
        controller.mark_tab_dirty(tab1.tab_id)
        controller.mark_tab_dirty(tab3.tab_id)
        
        # Get dirty tabs
        dirty = controller.get_dirty_tabs()
        assert len(dirty) == 2
        
        # Close clean tab
        result = controller.close_tab(tab2.tab_id)
        assert result is True
        assert controller.get_tab_count() == 2
        
        # Active should switch to remaining tab
        assert controller.get_active_tab() in [tab1, tab3]
    
    def test_signal_coordination(self, mock_queue_manager):
        """Test that all signals are emitted correctly."""
        controller = TabController(queue_manager=mock_queue_manager)
        
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
        created_spy.assert_called_once()
        
        # Activate tab
        controller.set_active_tab(tab_info.tab_id)
        activated_spy.assert_called_once()
        
        # Mark dirty
        controller.mark_tab_dirty(tab_info.tab_id)
        dirty_spy.assert_called_once()
        
        # Close tab
        controller.close_tab(tab_info.tab_id, force=True)
        closed_spy.assert_called_once()
