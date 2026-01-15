
from typing import Dict, Optional
import json
from PySide6.QtWidgets import QMainWindow, QToolBar, QMessageBox, QFileDialog
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import QPointF, Qt
from core.settings_manager import SettingsManager
from core.graph import Graph
from core.node import Node, Link
from core.assembler import ContextAssembler
from core.logging_setup import setup_logging
import logging

from services.worker import LLMWorker
from core.command_manager import CommandManager
from core.command import (
    AddNodeCommand, DeleteNodesCommand, MoveNodesCommand, 
    AddLinkCommand, DeleteLinkCommand, EditPromptCommand, 
    EditOutputCommand, PasteNodesAndLinksCommand
)
from .canvas import CanvasScene, CanvasView
from .node_item import NodeItem
from .wire_item import WireItem
from .node_item import NodeItem
from .wire_item import WireItem
from .settings_dialog import SettingsDialog
from .node_settings_dialog import NodeSettingsDialog
from .log_window import LogWindow

class AntiGravityWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AntiGravity: Branching LLM Logic Engine")
        self.resize(1200, 800)
        
        # Logging
        self.log_signaler, self.log_handler = setup_logging()
        self.logger = logging.getLogger("QT.Window")
        self.logger.info("Initializing Application Window")
        
        self.log_window = LogWindow()
        self.log_signaler.log_signal.connect(self.log_window.append_log)
        
        # Core Logic
        self.graph = Graph()
        self.node_items: Dict[str, NodeItem] = {}
        self.wires: Dict[str, WireItem] = {}
        
        # Interaction State
        self.temp_wire: Optional[WireItem] = None
        self.dragging_source_id: Optional[str] = None
        self.clipboard = [] # List of node dicts for copy/paste
        
        # Undo/Redo System
        self.command_manager = CommandManager()
        self.command_manager.add_listener(self.update_undo_redo_actions)
        
        # UI Setup
        self.scene = CanvasScene()
        self.view = CanvasView(self.scene)
        self.setCentralWidget(self.view)
        
        # --- Menus ---
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_graph)
        file_menu.addAction(save_action)
        
        load_action = QAction("Load", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_graph)
        file_menu.addAction(load_action)
        
        merge_action = QAction("Merge Graph...", self)
        merge_action.setShortcut("Ctrl+Shift+O")
        merge_action.triggered.connect(self.merge_graph)
        file_menu.addAction(merge_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit Menu
        edit_menu = menubar.addMenu("Edit")
        
        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(self.undo)
        edit_menu.addAction(self.undo_action)
        
        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(self.redo)
        edit_menu.addAction(self.redo_action)
        
        edit_menu.addSeparator()
        
        add_node_action = QAction("Add Node", self)
        add_node_action.setShortcut("Ctrl+N")
        add_node_action.triggered.connect(self.add_node)
        edit_menu.addAction(add_node_action)
        
        edit_menu.addSeparator()
        
        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy_selection)
        edit_menu.addAction(copy_action)
        
        cut_action = QAction("Cut", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.cut_selection)
        edit_menu.addAction(cut_action)
        
        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste_selection)
        edit_menu.addAction(paste_action)
        
        rename_action = QAction("Rename", self)
        rename_action.setShortcut("F2")
        rename_action.triggered.connect(self.trigger_rename)
        edit_menu.addAction(rename_action)
        
        duplicate_action = QAction("Duplicate", self)
        duplicate_action.setShortcut("Alt+D")
        duplicate_action.triggered.connect(self.duplicate_selection)
        edit_menu.addAction(duplicate_action)
        
        edit_menu.addSeparator()
        
        delete_action = QAction("Delete", self)
        delete_action.setShortcut("Delete")
        delete_action.setShortcutContext(Qt.WindowShortcut)
        delete_action.triggered.connect(self.delete_selection)
        edit_menu.addAction(delete_action)

        # Window/Tools Menu
        window_menu = menubar.addMenu("Window")
        
        log_action = QAction("Open Log Window", self)
        log_action.triggered.connect(self.show_log_window)
        window_menu.addAction(log_action)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        window_menu.addAction(settings_action)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; color: #e0e0e0; }
            QMenuBar { background-color: #2b2b2b; color: #eee; }
            QMenuBar::item:selected { background-color: #444; }
            QMenu { 
                background-color: #2b2b2b; 
                border: 1px solid #444; 
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 10px 6px 10px;
                border: 1px solid transparent;
            }
            QMenu::item:selected { 
                background-color: #3e3e3e; 
                border: 1px solid #00aaff;
                border-radius: 3px;
            }
            QMenu::separator {
                height: 1px;
                background: #444;
                margin: 4px 8px;
            }
        """)

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

    def copy_selection(self):
        selected_nodes = [item.node.id for item in self.scene.selectedItems() if isinstance(item, NodeItem)]
        if not selected_nodes:
            self.clipboard = None
            return
            
        clipboard_data = {
            "nodes": [],
            "links": []
        }
        
        # Store node data
        for node_id in selected_nodes:
            node = self.graph.nodes[node_id]
            clipboard_data["nodes"].append(node.to_dict())
            
        # Store internal links (links where both source and target are selected)
        for link in self.graph.links.values():
            if link.source_id in selected_nodes and link.target_id in selected_nodes:
                clipboard_data["links"].append({
                    "source_id": link.source_id,
                    "target_id": link.target_id
                })
                
        self.clipboard = clipboard_data
        self.logger.info(f"Copied {len(selected_nodes)} nodes and {len(clipboard_data['links'])} internal links")

    def cut_selection(self):
        self.copy_selection()
        if self.clipboard:
            self.delete_selection()
            self.logger.info("Cut selection")

    def paste_selection(self):
        if not self.clipboard:
            return
            
        self.logger.info(f"Pasting {len(self.clipboard['nodes'])} nodes")
        
        import uuid
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
            
            # Ensure name uniqueness if it has a custom name
            if new_node.name:
                base_name = new_node.name
                # Strip existing _copyXX suffix if present to avoid piling them up
                import re
                base_name = re.sub(r'_copy\d+$', '', base_name)
                
                name_num = 1
                test_name = f"{base_name}_copy{name_num:02d}"
                while not self.graph.is_name_unique(test_name, exclude_node_id=new_id):
                    name_num += 1
                    test_name = f"{base_name}_copy{name_num:02d}"
                new_node.name = test_name
            
            # Offset position to avoid exact overlap
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
                
        # 3. Execute command
        cmd = PasteNodesAndLinksCommand(self.graph, new_nodes, new_links)
        self.command_manager.execute(cmd)
        
        # 4. Create visual items
        for node in new_nodes:
            self.create_node_item(node)
        for link in new_links:
            self.create_visual_wire(link)
            
        # 5. Select the new nodes
        self.scene.clearSelection()
        for node in new_nodes:
            if node.id in self.node_items:
                self.node_items[node.id].setSelected(True)
                
        self.refresh_visuals()

    def duplicate_selection(self):
        self.copy_selection()
        self.paste_selection()

    def delete_selection(self):
        selected_nodes = [item for item in self.scene.selectedItems() if isinstance(item, NodeItem)]
        if not selected_nodes:
            return
            
        nodes_to_delete = [item.node for item in selected_nodes]
        node_ids = [n.id for n in nodes_to_delete]
        
        # Find links connected to these nodes
        links_to_delete = []
        for link in self.graph.links.values():
            if link.source_id in node_ids or link.target_id in node_ids:
                links_to_delete.append(link)
                
        cmd = DeleteNodesCommand(self.graph, nodes_to_delete, links_to_delete)
        self.command_manager.execute(cmd)
        
        self.refresh_visuals()

    def add_node(self):
        self.logger.info("Adding new node via menu")
        viewport_rect = self.view.viewport().rect()
        center_scene = self.view.mapToScene(viewport_rect.center())
        self.add_node_at(center_scene)

    def create_node_item(self, node):
        item = NodeItem(node, self.graph)
        self.scene.addItem(item)
        self.node_items[node.id] = item
        
        # Connect signals
        item.promptChanged.connect(self.on_prompt_changed)
        item.runClicked.connect(self.on_run_clicked)
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
        # Update metrics but don't create command yet
        self.update_metrics(node_id)
        # Visuals for dirty state
        self.refresh_visuals()

    def on_run_clicked(self, node_id):
        node = self.graph.nodes.get(node_id)
        if not node:
            return
            
        assembler = ContextAssembler(self.graph)
        try:
            prompt = assembler.assemble(node)
        except Exception as e:
            QMessageBox.critical(self, "Assembly Error", str(e))
            return
            
        # Manage Workers
        if not hasattr(self, 'workers'):
            self.workers = []
        self.workers = [w for w in self.workers if w.isRunning()]
        
        config = {
            "model": node.config.model,
            "provider": node.config.provider,
            "max_tokens": node.config.max_tokens,
            "trace_depth": node.config.trace_depth
        }
        
        worker = LLMWorker(node_id, prompt, config)
        worker.finished.connect(self.on_worker_finished)
        worker.error.connect(self.on_worker_error)
        
        self.workers.append(worker)
        worker.start()

    def on_worker_finished(self, node_id, result):
        node = self.graph.nodes.get(node_id)
        if node:
            node.cached_output = result
            self.graph.mark_dirty(node_id)
            node.is_dirty = False
            
            # Update UI Widget
            if node_id in self.node_items:
                self.node_items[node_id].update_output(result)
            
            # Update Downstream Metrics (Children)
            for link in self.graph.links.values():
                if link.source_id == node_id:
                     self.update_metrics(link.target_id)
                
            self.refresh_visuals()

    def on_worker_error(self, node_id, error_msg):
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
        
        # 1. Prompt Len
        total_chars = len(node.prompt)
        
        # 2. Input Context (Recursive or Shallow?)
        # For the meter "Context Payload", it usually means what is sent to LLM.
        # This includes History + Implicit Inputs.
        # Let's do a shallow sum of all inputs for now, or use Assembler dry run?
        # Assembler dry run is expensive. Let's do Sum of Inputs.
        
        for link_id in node.input_links:
            link = self.graph.links.get(link_id)
            if link:
                source = self.graph.nodes.get(link.source_id)
                if source and source.cached_output:
                    total_chars += len(source.cached_output)
        
        # Update Item
        item.set_metrics(total_chars, node.config.max_tokens * 4) # approx 4 chars/token

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
            
            # Apply Defaults from Settings
            settings = SettingsManager()
            provider = settings.value("default_provider", "Ollama")
            
            if provider == "OpenAI":
                new_node.config.model = settings.value("openai_model", "gpt-4o")
            elif provider == "Gemini":
                new_node.config.model = settings.value("gemini_model", "gemini-1.5-flash")
            else:
                 new_node.config.model = settings.value("ollama_model", "llama3")

            # Execute as single operation (Add Node + Add Link)
            # We can use a composite command if we want, or just two commands.
            # Two commands is simpler for now, but user might want to undo once.
            # Actually, let's just use two commands, it's fine.
            
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
        # Remove items that are no longer in graph
        to_remove = []
        for nid in self.node_items:
            if nid not in self.graph.nodes:
                to_remove.append(nid)
        for nid in to_remove:
            item = self.node_items.pop(nid)
            self.scene.removeItem(item)
            
        # Add items that are in graph but not in UI
        for node in self.graph.nodes.values():
            if node.id not in self.node_items:
                self.create_node_item(node)
                
        # 2. Sync graph links with UI wires
        # Remove wires no longer in graph
        to_remove_wires = []
        for lid in self.wires:
            if lid not in self.graph.links:
                to_remove_wires.append(lid)
        for lid in to_remove_wires:
            wire = self.wires.pop(lid)
            self.scene.removeItem(wire)
            
        # Add wires in graph but not in UI
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
            self.logger.info(f"Undo: {self.command_manager.get_redo_description()}")
            self.refresh_visuals()
            self.statusBar().showMessage(f"Undone: {self.command_manager.get_redo_description()}", 3000)

    def redo(self):
        if self.command_manager.redo():
            self.logger.info(f"Redo: {self.command_manager.get_undo_description()}")
            self.refresh_visuals()
            self.statusBar().showMessage(f"Redone: {self.command_manager.get_undo_description()}", 3000)

    def update_undo_redo_actions(self):
        self.undo_action.setEnabled(self.command_manager.can_undo())
        self.redo_action.setEnabled(self.command_manager.can_redo())
        
        undo_desc = self.command_manager.get_undo_description()
        redo_desc = self.command_manager.get_redo_description()
        
        self.undo_action.setText(f"Undo {undo_desc}" if undo_desc else "Undo")
        self.redo_action.setText(f"Redo {redo_desc}" if redo_desc else "Redo")

    def on_move_finished(self, node_id, old_pos, new_pos):
        # Handle multiple selection moves
        selected_nodes = [item for item in self.scene.selectedItems() if isinstance(item, NodeItem)]
        
        move_data = []
        if any(item.node.id == node_id for item in selected_nodes):
            # This was a multi-selection move
            for item in selected_nodes:
                # We need to know the offset for other nodes
                # But actually NodeItem already updated node.pos_x/y
                # So we just capture the current state vs what we might have had.
                # Actually, the simplest is to just use the delta from the primary node.
                delta_x = new_pos.x() - old_pos.x()
                delta_y = new_pos.y() - old_pos.y()
                
                # Note: node_item.mouseReleaseEvent emitted this for ONE node.
                # If multiple were moved, they all might emit or just one?
                # QGraphicsItem handles multi-move internally.
                # For now, let's just record the one that finished.
                # If we want true multi-move undo, we'd need to capture all start positions.
                # Let's simplify: only record the node that emitted the signal.
                # This works if only one node is moved or if we only care about that one.
                # TODO: Support true multi-node move undo.
                pass
        
        # Simple single node move command for now to ensure it works
        cmd = MoveNodesCommand(self.graph, [(node_id, old_pos.x(), old_pos.y(), new_pos.x(), new_pos.y())])
        self.command_manager.execute(cmd)

    def on_prompt_edit_finished(self, node_id, old_text, new_text):
        cmd = EditPromptCommand(self.graph, node_id, old_text, new_text)
        self.command_manager.execute(cmd)

    def on_output_edit_finished(self, node_id, old_text, new_text):
        cmd = EditOutputCommand(self.graph, node_id, old_text, new_text)
        self.command_manager.execute(cmd)

    def trigger_rename(self):
        selected_nodes = [item for item in self.scene.selectedItems() if isinstance(item, NodeItem)]
        if selected_nodes:
            selected_nodes[0].edit_name()

    def on_name_edit_finished(self, node_id, old_name, new_name):
        # Validation already handled in NodeItem
        if old_name != new_name:
            from core.command import RenameNodeCommand
            cmd = RenameNodeCommand(self.graph, node_id, old_name, new_name)
            self.command_manager.execute(cmd)
            self.refresh_visuals()

    # --- Persistence ---
    def save_graph(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Graph", "", "JSON Files (*.json)")
        if not path: return
        try:
            self.logger.info(f"Saving graph to {path}")
            data = self.graph.to_dict()
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved to {path}")
            self.logger.info("Save successful")
        except Exception as e:
            self.logger.error(f"Save failed: {e}")
            QMessageBox.critical(self, "Save Error", str(e))

    def load_graph(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Graph", "", "JSON Files (*.json)")
        if not path: return
        try:
            self.logger.info(f"Loading graph from {path}")
            with open(path, 'r') as f:
                data = json.load(f)
            
            self.graph = Graph.from_dict(data)
            self.scene.clear()
            self.node_items.clear()
            self.wires.clear()
            self.temp_wire = None
            
            # Rebuild UI
            for node in self.graph.nodes.values():
                self.create_node_item(node)
                
            for link in self.graph.links.values():
                self.create_visual_wire(link)
                
            self.refresh_visuals()
            print(f"Loaded from {path}")
            self.logger.info("Load successful")
        except Exception as e:
            self.logger.error(f"Load failed: {e}")
            QMessageBox.critical(self, "Load Error", str(e))

    def merge_graph(self):
        path, _ = QFileDialog.getOpenFileName(self, "Merge Graph", "", "JSON Files (*.json)")
        if not path: return
        try:
            import os
            filename = os.path.splitext(os.path.basename(path))[0]
            self.logger.info(f"Merging graph from {path}")
            
            with open(path, 'r') as f:
                data = json.load(f)
            
            self.graph.merge_graph(data, filename)
            
            # Since merge_graph updates the internal graph state, we just need to sync UI
            self.refresh_visuals()
            
            self.logger.info("Merge successful")
            self.statusBar().showMessage(f"Merged {path}", 3000)
        except Exception as e:
            self.logger.error(f"Merge failed: {e}")
            QMessageBox.critical(self, "Merge Error", str(e))

    def open_settings(self):
        self.logger.info("Opening Settings Dialog")
        dlg = SettingsDialog(self)
        dlg.exec()

    def show_log_window(self):
        self.log_window.show()
        self.log_window.raise_()
        self.log_window.activateWindow()
