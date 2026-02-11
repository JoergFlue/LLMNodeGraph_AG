"""
AntiGravity API - High-level interface for application operations.
Designed for integration testing and external automation.
"""

import logging
import time
from typing import Optional, List, Tuple, Dict, Any
from PySide6.QtCore import QPointF, QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from core.graph import Graph
from core.node import Node, Link
from core.command import AddLinkCommand, DeleteLinkCommand, DeleteNodesCommand
from core.provider_status import ProviderStatusManager
from ui.main_window import AntiGravityWindow
from ui.editor_tab import EditorTab

class AntiGravityAPI:
    """
    Facade class providing a stable API for interacting with the AntiGravity application.
    """
    def __init__(self, window: AntiGravityWindow):
        self.window = window
        self.logger = logging.getLogger("AntiGravity.API")

    # --- Node Operations ---
    
    def create_node(self, name: str = None, pos: Tuple[float, float] = (100, 100)) -> str:
        """
        Create a new node in the active tab.
        
        Args:
            name: Optional name for the node.
            pos: (x, y) position in the scene.
            
        Returns:
            str: The ID of the created node.
        """
        tab = self.window.get_current_tab()
        if not tab:
            raise RuntimeError("No active tab")
            
        node = tab.add_node_at(QPointF(pos[0], pos[1]))
        if name:
            tab.on_name_edit_finished(node.id, node.name, name)
            
        return node.id

    def delete_node(self, node_id: str):
        """
        Delete a node from the active tab.
        
        Args:
            node_id: ID of the node to delete.
        """
        tab = self.window.get_current_tab()
        if not tab:
            raise RuntimeError("No active tab")
            
        node = tab.graph.nodes.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found in active graph")
            
        # Use DeleteNodesCommand to ensure undo/redo and link cleanup
        links_to_delete = [l for l in tab.graph.links.values() 
                           if l.source_id == node_id or l.target_id == node_id]
        
        cmd = DeleteNodesCommand(tab.graph, [node], links_to_delete)
        tab.command_manager.execute(cmd)
        tab.refresh_visuals()

    def set_node_prompt(self, node_id: str, prompt: str):
        """
        Set the prompt text for a node.
        
        Args:
            node_id: ID of the node.
            prompt: The new prompt text.
        """
        tab = self.window.get_current_tab()
        if not tab:
            raise RuntimeError("No active tab")
            
        node = tab.graph.nodes.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
            
        tab.on_prompt_edit_finished(node_id, node.prompt, prompt)

    def get_node_output(self, node_id: str) -> str:
        """
        Get the current cached output of a node.
        
        Args:
            node_id: ID of the node.
            
        Returns:
            str: The cached output.
        """
        tab = self.window.get_current_tab()
        if not tab:
            raise RuntimeError("No active tab")
            
        node = tab.graph.nodes.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
            
        return node.cached_output

    # --- Connection Operations ---

    def create_connection(self, source_id: str, target_id: str) -> str:
        """
        Create a connection (link) between two nodes.
        
        Args:
            source_id: ID of the source node.
            target_id: ID of the target node.
            
        Returns:
            str: The ID of the created link.
        """
        tab = self.window.get_current_tab()
        if not tab:
            raise RuntimeError("No active tab")
            
        if source_id not in tab.graph.nodes:
            raise ValueError(f"Source node {source_id} not found")
        if target_id not in tab.graph.nodes:
            raise ValueError(f"Target node {target_id} not found")
            
        link = Link(source_id=source_id, target_id=target_id)
        cmd = AddLinkCommand(tab.graph, link)
        tab.command_manager.execute(cmd)
        tab.refresh_visuals()
        return link.id

    def delete_connection(self, link_id: str):
        """
        Delete a connection by ID.
        
        Args:
            link_id: ID of the link to delete.
        """
        tab = self.window.get_current_tab()
        if not tab:
            raise RuntimeError("No active tab")
            
        link = tab.graph.links.get(link_id)
        if not link:
            raise ValueError(f"Link {link_id} not found")
            
        cmd = DeleteLinkCommand(tab.graph, link)
        tab.command_manager.execute(cmd)
        tab.refresh_visuals()

    # --- Scene Management ---

    def create_scene(self) -> EditorTab:
        """Create a new empty scene (tab)."""
        return self.window.new_graph()

    def save_scene(self, path: str):
        """
        Save the current scene to a file.
        
        Args:
            path: File path to save to.
        """
        tab = self.window.get_current_tab()
        if not tab:
            raise RuntimeError("No active tab")
        tab.save_to_path(path)

    def open_scene(self, path: str) -> EditorTab:
        """
        Open a scene from a file.
        
        Args:
            path: Path to the .json graph file.
            
        Returns:
            EditorTab: The newly created tab.
        """
        import json
        with open(path, 'r') as f:
            data = json.load(f)
        graph = Graph.from_dict(data)
        return self.window.add_tab(graph, path)

    def close_scene(self, force: bool = True):
        """
        Close the current scene.
        
        Args:
            force: If True, bypass unsaved changes check.
        """
        idx = self.window.tabs.currentIndex()
        if idx == -1:
            return
            
        tab = self.window.get_current_tab()
        if force and tab:
            tab.is_dirty = False
            
        self.window.close_tab(idx)

    # --- Window Management ---

    def show_log_window(self, show: bool = True):
        """Show or hide the log window."""
        if show:
            self.window.show_log_window()
        else:
            self.window.log_window.hide()

    def show_settings(self, show: bool = True):
        """Show or hide the settings dialog."""
        if show:
            self.window.open_settings()
        else:
            if self.window.settings_dialog:
                self.window.settings_dialog.hide()

    # --- Provider Status ---

    def get_provider_status(self, provider: str) -> Optional[bool]:
        """
        Get the connectivity status of a provider.
        
        Args:
            provider: Provider name (e.g., 'OpenAI', 'Ollama').
            
        Returns:
            bool: True if online, False if offline, None if checking/unknown.
        """
        return ProviderStatusManager.instance().get_status(provider)

    def check_all_providers(self):
        """Trigger a check for all providers."""
        ProviderStatusManager.instance().check_all()

    # --- Execution ---

    def run_node(self, node_id: str):
        """
        Trigger execution for a specific node.
        
        Args:
            node_id: ID of the node to run.
        """
        tab = self.window.get_current_tab()
        if not tab:
            raise RuntimeError("No active tab")
        tab.on_run_clicked(node_id)

    def wait_for_node(self, node_id: str, timeout_ms: int = 15000) -> bool:
        """
        Wait for a node to finish execution by polling its status.
        
        Args:
            node_id: ID of the node.
            timeout_ms: Timeout in milliseconds.
            
        Returns:
            bool: True if finished, False if timed out.
        """
        tab = self.window.get_current_tab()
        node = tab.graph.nodes.get(node_id)
        if not node:
            return False
            
        start_time = time.time()
        while time.time() - start_time < timeout_ms / 1000:
            # Check if node is no longer dirty AND has output
            # (Note: is_dirty is cleared in on_task_finished)
            if not node.is_dirty and node.cached_output:
                return True
            
            QApplication.processEvents()
            time.sleep(0.1)
            
        return False
