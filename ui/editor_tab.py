
from typing import Dict, Optional, List
import json
import logging
import os

from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QFileDialog
from PySide6.QtCore import Signal, QPointF

from core.graph import Graph
from core.node import Node, Link
from core.assembler import ContextAssembler
from core.command_manager import CommandManager
from core.command import (
    AddNodeCommand, DeleteNodesCommand, MoveNodesCommand, 
    AddLinkCommand, DeleteLinkCommand, EditPromptCommand, 
    EditOutputCommand, PasteNodesAndLinksCommand
)
from core.settings_manager import SettingsManager

from .canvas import CanvasScene, CanvasView
from .node_item import NodeItem
from .wire_item import WireItem

class EditorTab(QWidget):
    # Signal emitted when the tab's dirty state changes
    dirty_changed = Signal(bool)
    # Signal to update status bar message
    status_message = Signal(str, int)

    def __init__(self, parent=None, graph: Optional[Graph] = None, queue_manager = None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(f"QT.EditorTab.{id(self)}")
        self.queue_manager = queue_manager
        
        # State
        self.current_file_path: Optional[str] = None
        self._is_dirty = False
        
        # Core Logic
        self.graph = graph if graph else Graph()
        self.node_items: Dict[str, NodeItem] = {}
        self.wires: Dict[str, WireItem] = {}
        
        # Interaction State
        self.temp_wire: Optional[WireItem] = None
        self.dragging_source_id: Optional[str] = None
        self.clipboard = [] 
        
        # Undo/Redo System
        self.command_manager = CommandManager()
        self.command_manager.add_listener(self.on_command_executed)
        
        # UI Setup
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.scene = CanvasScene()
        self.view = CanvasView(self.scene)
        self.layout.addWidget(self.view)
        
        # Build initial visuals
        self.refresh_visuals()
        
        # Connect Queue Manager
        if self.queue_manager:
            self.queue_manager.task_started.connect(self.on_task_started)
            self.queue_manager.task_finished.connect(self.on_task_finished)
            self.queue_manager.task_failed.connect(self.on_task_failed)
            self.queue_manager.task_queued.connect(self.on_task_queued)

    @property
    def is_dirty(self):
        return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, value):
        if self._is_dirty != value:
            self._is_dirty = value
            self.dirty_changed.emit(value)

    def on_command_executed(self):
        self.is_dirty = True
        # Parent window will handle updating undo/redo actions availability if this is the active tab

    def add_node_at(self, pos: QPointF):
        self.logger.info(f"Adding node at {pos.x()}, {pos.y()}")
        node = Node() # Generates UUID
        node.name = self.graph.generate_new_node_name()
        node.pos_x = pos.x() - 150
        node.pos_y = pos.y() - 100
        
        # Apply Defaults from Settings
        settings = SettingsManager()
        provider = settings.value("default_provider", "Ollama")
        
        if provider == "OpenAI":
            node.config.model = settings.value("openai_model", "gpt-4o")
        elif provider == "Gemini":
            node.config.model = settings.value("gemini_model", "gemini-1.5-flash")
        else:
             node.config.model = settings.value("ollama_model", "llama3")
             
        # Use command pattern
        cmd = AddNodeCommand(self.graph, node)
        self.command_manager.execute(cmd)
        
        self.create_node_item(node)
        self.update_metrics(node.id)
        self.refresh_visuals()
        return node

    def add_node_center(self):
        viewport_rect = self.view.viewport().rect()
        center_scene = self.view.mapToScene(viewport_rect.center())
        self.add_node_at(center_scene)

    def copy_selection(self):
        selected_nodes = [item.node.id for item in self.scene.selectedItems() if isinstance(item, NodeItem)]
        if not selected_nodes:
            self.clipboard = None
            return
            
        clipboard_data = {
            "nodes": [],
            "links": []
        }
        
        for node_id in selected_nodes:
            node = self.graph.nodes[node_id]
            clipboard_data["nodes"].append(node.to_dict())
            
        for link in self.graph.links.values():
            if link.source_id in selected_nodes and link.target_id in selected_nodes:
                clipboard_data["links"].append({
                    "source_id": link.source_id,
                    "target_id": link.target_id
                })
                
        self.clipboard = clipboard_data
        self.logger.info(f"Copied {len(selected_nodes)} nodes")

    def cut_selection(self):
        self.copy_selection()
        if self.clipboard:
            self.delete_selection()

    def paste_selection(self):
        if not self.clipboard:
            return
            
        import uuid
        import re
        id_map = {}
        new_nodes = []
        new_links = []
        
        # 1. Prepare nodes
        for node_data in self.clipboard["nodes"]:
            old_id = node_data['id']
            new_node = Node.from_dict(node_data)
            new_id = self.graph.generate_copy_id(old_id)
            new_node.id = new_id
            id_map[old_id] = new_id
            
            # Ensure name uniqueness
            if new_node.name:
                base_name = new_node.name
                base_name = re.sub(r'_copy\d+$', '', base_name)
                
                name_num = 1
                test_name = f"{base_name}_copy{name_num:02d}"
                while not self.graph.is_name_unique(test_name, exclude_node_id=new_id):
                    name_num += 1
                    test_name = f"{base_name}_copy{name_num:02d}"
                new_node.name = test_name
            
            # Offset position
            new_node.pos_x += 40
            new_node.pos_y += 40
            new_nodes.append(new_node)
            
        # 2. Prepare internal links
        for link_data in self.clipboard["links"]:
            new_source = id_map.get(link_data["source_id"])
            new_target = id_map.get(link_data["target_id"])
            
            if new_source and new_target:
                link = Link(source_id=new_source, target_id=new_target)
                new_links.append(link)
                
        cmd = PasteNodesAndLinksCommand(self.graph, new_nodes, new_links)
        self.command_manager.execute(cmd)
        
        # Select new nodes
        self.scene.clearSelection()
        self.refresh_visuals()
        
        for node in new_nodes:
            if node.id in self.node_items:
                self.node_items[node.id].setSelected(True)

    def duplicate_selection(self):
        self.copy_selection()
        self.paste_selection()

    def delete_selection(self):
        selected_nodes = [item for item in self.scene.selectedItems() if isinstance(item, NodeItem)]
        if not selected_nodes:
            return
            
        nodes_to_delete = [item.node for item in selected_nodes]
        node_ids = [n.id for n in nodes_to_delete]
        
        links_to_delete = []
        for link in self.graph.links.values():
            if link.source_id in node_ids or link.target_id in node_ids:
                links_to_delete.append(link)
                
        cmd = DeleteNodesCommand(self.graph, nodes_to_delete, links_to_delete)
        self.command_manager.execute(cmd)
        self.refresh_visuals()

    def create_node_item(self, node):
        item = NodeItem(node, self.graph)
        self.scene.addItem(item)
        self.node_items[node.id] = item
        
        # Connect signals
        item.promptChanged.connect(self.on_prompt_changed)
        item.runClicked.connect(self.on_run_clicked)
        item.cancelClicked.connect(self.on_cancel_clicked)
        item.wireDragStarted.connect(self.on_wire_drag_started)
        item.wireDragMoved.connect(self.on_wire_drag_moved)
        item.wireDragReleased.connect(self.on_wire_drag_released)
        item.positionChanged.connect(self.on_node_moved)
        
        # Undo/Redo signals
        item.moveFinished.connect(self.on_move_finished)
        item.promptEditFinished.connect(self.on_prompt_edit_finished)
        item.outputEditFinished.connect(self.on_output_edit_finished)
        item.nameEditFinished.connect(self.on_name_edit_finished)

    def on_prompt_changed(self, node_id, new_prompt):
        self.update_metrics(node_id)
        # Assuming dirty state is handled by edit finished command

    def on_run_clicked(self, node_id):
        node = self.graph.nodes.get(node_id)
        if not node: return
        
        if not self.queue_manager:
            QMessageBox.critical(self, "Error", "LLM Worker not initialized")
            return

        assembler = ContextAssembler(self.graph)
        try:
            prompt = assembler.assemble(node)
        except Exception as e:
            QMessageBox.critical(self, "Assembly Error", str(e))
            return
            
        config = {
            "model": node.config.model,
            "provider": node.config.provider,
            "max_tokens": node.config.max_tokens,
            "trace_depth": node.config.trace_depth
        }
        
        self.queue_manager.submit_task(node_id, prompt, config)

    def on_cancel_clicked(self, node_id):
        if self.queue_manager:
            self.queue_manager.cancel_task(node_id)
        if node_id in self.node_items:
            self.node_items[node_id].set_execution_state("IDLE")

    def on_task_queued(self, node_id):
        if node_id in self.node_items:
            self.node_items[node_id].set_execution_state("QUEUED")

    def on_task_started(self, node_id):
        if node_id in self.node_items:
            self.node_items[node_id].set_execution_state("RUNNING")

    def on_task_finished(self, node_id, result):
        if node_id not in self.node_items:
            return

        self.node_items[node_id].set_execution_state("IDLE")
        node = self.graph.nodes.get(node_id)
        if node:
            node.cached_output = result
            # We don't mark dirty for LLM output? 
            # Original code: self.graph.mark_dirty(node_id) -> handled logic node state
            # but usually output is transient or cached. If we save, we usually save output?
            # Yes, Graph.to_dict saves cached_output. So this changes file content.
            self.is_dirty = True 
            
            # Update UI Widget
            self.node_items[node_id].update_output(result)
            
            # Update Downstream Metrics
            for link in self.graph.links.values():
                if link.source_id == node_id:
                     self.update_metrics(link.target_id)
                
            self.refresh_visuals()

    def on_task_failed(self, node_id, error_msg):
        if node_id in self.node_items:
             self.node_items[node_id].set_execution_state("IDLE")
             
             # Only show popup if this tab is active? 
             # Or just log it? Original code showed popup.
             # Ideally we shouldn't pop up for background tabs.
             # But for now, let's keep it.
             node = self.graph.nodes.get(node_id)
             display_name = node.name if node else node_id
             QMessageBox.warning(self, "Execution Error", f"Node {display_name} failed:\n{error_msg}")

    def on_node_moved(self, node_id):
        node = self.graph.nodes.get(node_id)
        if not node: return
        for link_id in node.input_links:
            self.update_wire_visual(link_id)
        for link_id, link in self.graph.links.items():
            if link.source_id == node_id:
                self.update_wire_visual(link_id)

    def update_wire_visual(self, link_id):
        if link_id not in self.wires: return
        wire = self.wires[link_id]
        link = self.graph.links[link_id]
        
        source_item = self.node_items.get(link.source_id)
        target_item = self.node_items.get(link.target_id)
        
        if source_item and target_item:
            start_pos = source_item.mapToScene(source_item.width - 6, 66)
            try:
                idx = target_item.node.input_links.index(link_id)
                y_offset = 60 + idx * 20 + 6
                end_pos = target_item.mapToScene(0, y_offset)
                wire.update_positions(start_pos, end_pos)
            except ValueError:
                pass

    def update_metrics(self, node_id):
        node = self.graph.nodes.get(node_id)
        if not node: return
        item = self.node_items.get(node_id)
        if not item: return
        
        total_chars = len(node.prompt)
        for link_id in node.input_links:
            link = self.graph.links.get(link_id)
            if link:
                source = self.graph.nodes.get(link.source_id)
                if source and source.cached_output:
                    total_chars += len(source.cached_output)
        
        item.set_metrics(total_chars, node.config.max_tokens * 4)

    def on_wire_drag_started(self, source_id, pos):
        self.dragging_source_id = source_id
        self.temp_wire = WireItem(pos, pos)
        self.scene.addItem(self.temp_wire)

    def on_wire_drag_moved(self, pos):
        if self.temp_wire:
            self.temp_wire.update_positions(self.temp_wire.source_pos, pos)

    def on_wire_drag_released(self, pos):
        if not self.temp_wire: return

        target_node_id = None
        items = self.scene.items(pos)
        for item in items:
            if isinstance(item, NodeItem):
                if item.node.id == self.dragging_source_id: continue
                if item.check_input_drop(pos):
                    target_node_id = item.node.id
                    break
        
        if target_node_id:
            # Check dupes
            existing = False
            target_node = self.graph.nodes[target_node_id]
            for input_link_id in target_node.input_links:
                l = self.graph.links[input_link_id]
                if l.source_id == self.dragging_source_id:
                    existing = True
                    break
            
            if not existing:
                link = Link(source_id=self.dragging_source_id, target_id=target_node_id)
                cmd = AddLinkCommand(self.graph, link)
                self.command_manager.execute(cmd)
                
                self.create_visual_wire(link)
                self.node_items[target_node_id].update()
                self.update_metrics(target_node_id)
        else:
            # Drop on empty space -> Create New Node & Link
            self.logger.info("Wire dropped on empty space: Creating new node")
            new_node = Node() # Generates UUID
            new_node.name = self.graph.generate_new_node_name()
            new_node.pos_x = pos.x() - 150
            new_node.pos_y = pos.y() - 100
            
            settings = SettingsManager()
            provider = settings.value("default_provider", "Ollama")
            
            if provider == "OpenAI":
                new_node.config.model = settings.value("openai_model", "gpt-4o")
            elif provider == "Gemini":
                new_node.config.model = settings.value("gemini_model", "gemini-1.5-flash")
            else:
                 new_node.config.model = settings.value("ollama_model", "llama3")

            node_cmd = AddNodeCommand(self.graph, new_node)
            self.command_manager.execute(node_cmd)
            self.create_node_item(new_node)
            
            link = Link(source_id=self.dragging_source_id, target_id=new_node.id)
            link_cmd = AddLinkCommand(self.graph, link)
            self.command_manager.execute(link_cmd)
            self.create_visual_wire(link)
            
            self.node_items[new_node.id].update()

        self.scene.removeItem(self.temp_wire)
        self.temp_wire = None
        self.dragging_source_id = None
        self.refresh_visuals()

    def create_visual_wire(self, link):
        source_item = self.node_items.get(link.source_id)
        target_item = self.node_items.get(link.target_id)
        
        if source_item and target_item:
            start_pos = source_item.mapToScene(source_item.width - 6, 66)
            try:
                idx = target_item.node.input_links.index(link.id)
                y_offset = 60 + idx * 20 + 6
                end_pos = target_item.mapToScene(0, y_offset)
                wire = WireItem(start_pos, end_pos)
                self.scene.addItem(wire)
                self.wires[link.id] = wire
            except ValueError:
                pass

    def refresh_visuals(self):
        # 1. Sync graph nodes with UI items
        to_remove = []
        for nid in self.node_items:
            if nid not in self.graph.nodes:
                to_remove.append(nid)
        for nid in to_remove:
            item = self.node_items.pop(nid)
            self.scene.removeItem(item)
            
        for node in self.graph.nodes.values():
            if node.id not in self.node_items:
                self.create_node_item(node)
                
        # 2. Sync graph links with UI wires
        to_remove_wires = []
        for lid in self.wires:
            if lid not in self.graph.links:
                to_remove_wires.append(lid)
        for lid in to_remove_wires:
            wire = self.wires.pop(lid)
            self.scene.removeItem(wire)
            
        for link in self.graph.links.values():
            if link.id not in self.wires:
                self.create_visual_wire(link)
                
        # 3. Update all positions and visuals
        for node_id, item in self.node_items.items():
            node = self.graph.nodes[node_id]
            item.setPos(node.pos_x, node.pos_y)
            item.width = node.width
            item.height = node.height
            item.update_layout()
            item.update()
            
        for lid in self.wires:
            self.update_wire_visual(lid)

    def undo(self):
        if self.command_manager.undo():
            self.refresh_visuals()
            self.status_message.emit(f"Undone: {self.command_manager.get_redo_description()}", 3000)
            self.is_dirty = True

    def redo(self):
        if self.command_manager.redo():
            self.refresh_visuals()
            self.status_message.emit(f"Redone: {self.command_manager.get_undo_description()}", 3000)
            self.is_dirty = True

    def on_move_finished(self, node_id, old_pos, new_pos):
        cmd = MoveNodesCommand(self.graph, [(node_id, old_pos.x(), old_pos.y(), new_pos.x(), new_pos.y())])
        self.command_manager.execute(cmd)

    def on_prompt_edit_finished(self, node_id, old_text, new_text):
        cmd = EditPromptCommand(self.graph, node_id, old_text, new_text)
        self.command_manager.execute(cmd)

    def on_output_edit_finished(self, node_id, old_text, new_text):
        cmd = EditOutputCommand(self.graph, node_id, old_text, new_text)
        self.command_manager.execute(cmd)

    def on_name_edit_finished(self, node_id, old_name, new_name):
        if old_name != new_name:
            from core.command import RenameNodeCommand
            cmd = RenameNodeCommand(self.graph, node_id, old_name, new_name)
            self.command_manager.execute(cmd)
            self.refresh_visuals()

    def trigger_rename(self):
        selected_nodes = [item for item in self.scene.selectedItems() if isinstance(item, NodeItem)]
        if selected_nodes:
            selected_nodes[0].edit_name()

    def save_to_path(self, path):
        try:
            self.logger.info(f"Saving graph to {path}")
            data = self.graph.to_dict()
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            self.current_file_path = path
            self.is_dirty = False
            self.status_message.emit(f"Saved to {path}", 3000)
            return True
        except Exception as e:
            self.logger.error(f"Save failed: {e}")
            QMessageBox.critical(self, "Save Error", str(e))
            return False

    def close_check(self):
        """Returns True if safe to close, False if cancelled."""
        if self.is_dirty:
            filename = os.path.basename(self.current_file_path) if self.current_file_path else "Untitled"
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Unsaved Changes")
            msg_box.setText(f"Save changes to {filename}?")
            msg_box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Save)
            ret = msg_box.exec()
            
            if ret == QMessageBox.Save:
                # If we have a path, save. properties
                # If no path, we need to ask parent window to handle "Save As" flow
                # Actually, EditorTab shouldn't pop up dialogs that require interaction with parent window's logic easily?
                # Well, QFileDialog is fine.
                if self.current_file_path:
                    return self.save_to_path(self.current_file_path)
                else:
                    path, _ = QFileDialog.getSaveFileName(self, "Save Graph", "", "JSON Files (*.json)")
                    if path:
                        if not path.endswith(".json"):
                            path += ".json"
                        return self.save_to_path(path)
                    else:
                        return False # Cancelled save dialog
            elif ret == QMessageBox.Discard:
                return True
            else:
                return False # Cancel
        return True
