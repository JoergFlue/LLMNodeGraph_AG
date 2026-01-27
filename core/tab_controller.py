"""
TabController - Manages tab lifecycle and coordination.

This controller handles tab creation, destruction, and state management,
implementing the Presenter layer for tab operations in the MVP pattern.
"""

import logging
from typing import Optional, List, Dict
from dataclasses import dataclass
from uuid import uuid4

from PySide6.QtCore import QObject, Signal

from core.graph import Graph
from core.graph_controller import GraphController


@dataclass
class TabInfo:
    """Information about a tab."""
    tab_id: str
    graph_controller: GraphController
    editor_tab: Optional[object] = None  # EditorTab widget
    is_active: bool = False


class TabController(QObject):
    """
    Controller for tab lifecycle and management.
    
    Responsibilities:
    - Tab creation and destruction
    - Active tab tracking
    - Tab state synchronization
    - Close confirmation logic
    - Coordination between tabs and graph controllers
    
    Signals:
        tab_created: Emitted when a new tab is created (tab_id, display_name)
        tab_closed: Emitted when a tab is closed (tab_id)
        tab_activated: Emitted when a tab becomes active (tab_id)
        tab_dirty_changed: Emitted when tab dirty state changes (tab_id, is_dirty)
    """
    
    # Signals
    tab_created = Signal(str, str)  # tab_id, display_name
    tab_closed = Signal(str)  # tab_id
    tab_activated = Signal(str)  # tab_id
    tab_dirty_changed = Signal(str, bool)  # tab_id, is_dirty
    
    def __init__(self, queue_manager=None):
        """
        Initialize the TabController.
        
        Args:
            queue_manager: LLMQueueManager instance for tab coordination
        """
        super().__init__()
        self.logger = logging.getLogger("TabController")
        self.queue_manager = queue_manager
        
        self._tabs: Dict[str, TabInfo] = {}
        self._active_tab_id: Optional[str] = None
    
    def create_tab(
        self,
        graph: Optional[Graph] = None,
        file_path: Optional[str] = None,
        editor_tab: Optional[object] = None
    ) -> TabInfo:
        """
        Create a new tab.
        
        Args:
            graph: Optional existing graph. If None, creates new empty graph.
            file_path: Optional file path for the graph.
            editor_tab: Optional EditorTab widget reference.
            
        Returns:
            TabInfo for the created tab.
        """
        tab_id = str(uuid4())
        
        # Create graph controller
        if graph is None:
            graph = GraphController.create_new_graph()
        
        graph_controller = GraphController(graph=graph, file_path=file_path)
        
        # Create tab info
        tab_info = TabInfo(
            tab_id=tab_id,
            graph_controller=graph_controller,
            editor_tab=editor_tab,
            is_active=False
        )
        
        self._tabs[tab_id] = tab_info
        
        # Emit signal
        display_name = graph_controller.get_display_name()
        self.tab_created.emit(tab_id, display_name)
        
        self.logger.info(f"Created tab {tab_id}: {display_name}")
        
        return tab_info
    
    def close_tab(self, tab_id: str, force: bool = False) -> bool:
        """
        Close a tab.
        
        Args:
            tab_id: ID of the tab to close.
            force: If True, close without checking for unsaved changes.
            
        Returns:
            True if tab was closed, False if cancelled by user.
        """
        if tab_id not in self._tabs:
            self.logger.warning(f"Attempted to close non-existent tab {tab_id}")
            return False
        
        tab_info = self._tabs[tab_id]
        
        # Check for unsaved changes unless forced
        if not force and tab_info.graph_controller.is_dirty:
            # This should be handled by the UI layer (showing dialog)
            # Controller just reports the state
            self.logger.info(f"Tab {tab_id} has unsaved changes")
            return False
        
        # Remove tab
        del self._tabs[tab_id]
        
        # Update active tab if this was active
        if self._active_tab_id == tab_id:
            self._active_tab_id = None
            
            # Set another tab as active if available
            if self._tabs:
                new_active_id = list(self._tabs.keys())[0]
                self.set_active_tab(new_active_id)
        
        self.tab_closed.emit(tab_id)
        self.logger.info(f"Closed tab {tab_id}")
        
        return True
    
    def get_tab(self, tab_id: str) -> Optional[TabInfo]:
        """
        Get tab information by ID.
        
        Args:
            tab_id: ID of the tab.
            
        Returns:
            TabInfo if found, None otherwise.
        """
        return self._tabs.get(tab_id)
    
    def get_active_tab(self) -> Optional[TabInfo]:
        """
        Get the currently active tab.
        
        Returns:
            TabInfo of active tab, or None if no tabs exist.
        """
        if self._active_tab_id:
            return self._tabs.get(self._active_tab_id)
        return None
    
    def set_active_tab(self, tab_id: str) -> bool:
        """
        Set the active tab.
        
        Args:
            tab_id: ID of the tab to activate.
            
        Returns:
            True if successful, False if tab doesn't exist.
        """
        if tab_id not in self._tabs:
            self.logger.warning(f"Attempted to activate non-existent tab {tab_id}")
            return False
        
        # Deactivate previous tab
        if self._active_tab_id and self._active_tab_id in self._tabs:
            self._tabs[self._active_tab_id].is_active = False
        
        # Activate new tab
        self._active_tab_id = tab_id
        self._tabs[tab_id].is_active = True
        
        self.tab_activated.emit(tab_id)
        self.logger.info(f"Activated tab {tab_id}")
        
        return True
    
    def get_all_tabs(self) -> List[TabInfo]:
        """
        Get all tabs.
        
        Returns:
            List of all TabInfo objects.
        """
        return list(self._tabs.values())
    
    def get_tab_count(self) -> int:
        """
        Get the number of tabs.
        
        Returns:
            Number of tabs.
        """
        return len(self._tabs)
    
    def has_unsaved_changes(self, tab_id: str) -> bool:
        """
        Check if a tab has unsaved changes.
        
        Args:
            tab_id: ID of the tab.
            
        Returns:
            True if tab has unsaved changes, False otherwise.
        """
        tab_info = self._tabs.get(tab_id)
        if tab_info:
            return tab_info.graph_controller.is_dirty
        return False
    
    def get_dirty_tabs(self) -> List[TabInfo]:
        """
        Get all tabs with unsaved changes.
        
        Returns:
            List of TabInfo objects with unsaved changes.
        """
        return [
            tab_info for tab_info in self._tabs.values()
            if tab_info.graph_controller.is_dirty
        ]
    
    def mark_tab_dirty(self, tab_id: str):
        """
        Mark a tab as having unsaved changes.
        
        Args:
            tab_id: ID of the tab.
        """
        tab_info = self._tabs.get(tab_id)
        if tab_info:
            was_dirty = tab_info.graph_controller.is_dirty
            tab_info.graph_controller.mark_dirty()
            
            if not was_dirty:
                self.tab_dirty_changed.emit(tab_id, True)
    
    def mark_tab_clean(self, tab_id: str):
        """
        Mark a tab as saved (no unsaved changes).
        
        Args:
            tab_id: ID of the tab.
        """
        tab_info = self._tabs.get(tab_id)
        if tab_info:
            was_dirty = tab_info.graph_controller.is_dirty
            tab_info.graph_controller.mark_clean()
            
            if was_dirty:
                self.tab_dirty_changed.emit(tab_id, False)
    
    def get_tab_display_name(self, tab_id: str, include_dirty: bool = True) -> str:
        """
        Get display name for a tab.
        
        Args:
            tab_id: ID of the tab.
            include_dirty: Whether to include dirty indicator (*).
            
        Returns:
            Display name string, or "Unknown" if tab doesn't exist.
        """
        tab_info = self._tabs.get(tab_id)
        if tab_info:
            return tab_info.graph_controller.get_window_title(include_dirty)
        return "Unknown"
    
    def close_all_tabs(self, force: bool = False) -> bool:
        """
        Close all tabs.
        
        Args:
            force: If True, close without checking for unsaved changes.
            
        Returns:
            True if all tabs were closed, False if any were cancelled.
        """
        tab_ids = list(self._tabs.keys())
        
        for tab_id in tab_ids:
            if not self.close_tab(tab_id, force):
                return False
        
        return True
    
    def find_tab_by_file_path(self, file_path: str) -> Optional[TabInfo]:
        """
        Find a tab by its file path.
        
        Args:
            file_path: File path to search for.
            
        Returns:
            TabInfo if found, None otherwise.
        """
        for tab_info in self._tabs.values():
            if tab_info.graph_controller.file_path == file_path:
                return tab_info
        return None
