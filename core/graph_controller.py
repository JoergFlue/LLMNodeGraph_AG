"""
GraphController - Manages graph-level operations and file I/O.

This controller separates graph business logic from UI concerns,
implementing the Presenter layer in the MVP pattern.
"""

import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from .graph import Graph
from .error_handler import show_error


class GraphController:
    """
    Controller for graph-level operations.
    
    Responsibilities:
    - Graph creation, loading, and saving
    - Graph merging with collision handling
    - File path management
    - Dirty state tracking
    """
    
    def __init__(self, graph: Optional[Graph] = None, file_path: Optional[str] = None):
        """
        Initialize the GraphController.
        
        Args:
            graph: Optional existing graph. If None, creates empty graph.
            file_path: Optional file path associated with the graph.
        """
        self.logger = logging.getLogger("GraphController")
        self._graph = graph if graph is not None else Graph()
        self._file_path = file_path
        self._is_dirty = False
    
    @property
    def graph(self) -> Graph:
        """Get the managed graph."""
        return self._graph
    
    @property
    def file_path(self) -> Optional[str]:
        """Get the current file path."""
        return self._file_path
    
    @file_path.setter
    def file_path(self, path: Optional[str]):
        """Set the current file path."""
        self._file_path = path
    
    @property
    def is_dirty(self) -> bool:
        """Check if the graph has unsaved changes."""
        return self._is_dirty
    
    def mark_dirty(self):
        """Mark the graph as having unsaved changes."""
        self._is_dirty = True
    
    def mark_clean(self):
        """Mark the graph as saved (no unsaved changes)."""
        self._is_dirty = False
    
    @staticmethod
    def create_new_graph() -> Graph:
        """
        Create a new empty graph.
        
        Returns:
            A new Graph instance.
        """
        return Graph()
    
    @staticmethod
    def load_graph(file_path: str) -> Graph:
        """
        Load a graph from a file.
        
        Args:
            file_path: Path to the graph JSON file.
            
        Returns:
            Loaded Graph instance.
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
            json.JSONDecodeError: If the file contains invalid JSON.
            Exception: For other loading errors.
        """
        logger = logging.getLogger("GraphController")
        logger.info(f"Loading graph from {file_path}")
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Graph file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        graph = Graph.from_dict(data)
        logger.info(f"Successfully loaded graph with {len(graph.nodes)} nodes")
        return graph
    
    def save_graph(self, file_path: Optional[str] = None) -> bool:
        """
        Save the graph to a file.
        
        Args:
            file_path: Path to save to. If None, uses current file_path.
            
        Returns:
            True if save successful, False otherwise.
            
        Raises:
            ValueError: If no file path is provided and none is set.
        """
        save_path = file_path or self._file_path
        
        if not save_path:
            raise ValueError("No file path specified for save operation")
        
        try:
            self.logger.info(f"Saving graph to {save_path}")
            data = self._graph.to_dict()
            
            with open(save_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self._file_path = save_path
            self._is_dirty = False
            self.logger.info("Save successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Save failed: {e}", exc_info=True)
            raise
    
    def merge_graph(self, source_path: str) -> Dict[str, Any]:
        """
        Merge another graph into the current graph.
        
        Args:
            source_path: Path to the graph file to merge.
            
        Returns:
            Dictionary with merge results:
            - 'nodes_added': Number of nodes added
            - 'links_added': Number of links added
            - 'id_collisions': Number of ID collisions resolved
            - 'name_collisions': Number of name collisions resolved
            
        Raises:
            FileNotFoundError: If source file doesn't exist.
            json.JSONDecodeError: If source file contains invalid JSON.
        """
        self.logger.info(f"Merging graph from {source_path}")
        
        path = Path(source_path)
        if not path.exists():
            raise FileNotFoundError(f"Source graph file not found: {source_path}")
        
        with open(source_path, 'r') as f:
            data = json.load(f)
        
        # Track merge statistics
        original_node_count = len(self._graph.nodes)
        original_link_count = len(self._graph.links)
        
        # Extract filename for collision handling
        filename = path.stem
        
        # Perform merge (Graph.merge_graph handles collisions)
        self._graph.merge_graph(data, filename)
        
        # Calculate statistics
        nodes_added = len(self._graph.nodes) - original_node_count
        links_added = len(self._graph.links) - original_link_count
        
        self._is_dirty = True
        
        result = {
            'nodes_added': nodes_added,
            'links_added': links_added,
            'filename': filename
        }
        
        self.logger.info(f"Merge complete: {nodes_added} nodes, {links_added} links added")
        return result
    
    def get_display_name(self) -> str:
        """
        Get a display name for the graph.
        
        Returns:
            Filename if file_path is set, otherwise "Untitled".
        """
        if self._file_path:
            return Path(self._file_path).name
        return "Untitled"
    
    def get_window_title(self, include_dirty: bool = True) -> str:
        """
        Get a window title for the graph.
        
        Args:
            include_dirty: Whether to append '*' for dirty state.
            
        Returns:
            Window title string.
        """
        title = self.get_display_name()
        if include_dirty and self._is_dirty:
            title += "*"
        return title
