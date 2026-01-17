
from typing import Dict, Optional
import json
from PySide6.QtWidgets import QMainWindow, QToolBar, QMessageBox, QFileDialog, QTabWidget, QLabel
from PySide6.QtGui import QAction, QIcon, QCloseEvent
from PySide6.QtCore import QPointF, Qt
from core.settings_manager import SettingsManager
from core.graph import Graph
from core.logging_setup import setup_logging
import logging

from services.llm_queue_manager import LLMQueueManager
from .editor_tab import EditorTab
from .settings_dialog import SettingsDialog
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
        
        # LLM Queue Manager
        self.queue_manager = LLMQueueManager()
        # EditorTab connects itself to queue_manager signals
        
        # UI Setup: Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tabs)
        
        # --- Menus ---
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+Alt+N")
        new_action.triggered.connect(self.new_graph)
        file_menu.addAction(new_action)
        
        load_action = QAction("Open...", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_graph)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_current_tab)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_current_tab_as)
        file_menu.addAction(save_as_action)
        
        save_all_action = QAction("Save All", self)
        save_all_action.triggered.connect(self.save_all)
        file_menu.addAction(save_all_action)
        
        file_menu.addSeparator()
        
        close_file_action = QAction("Close File", self)
        close_file_action.setShortcut("Ctrl+W")
        close_file_action.triggered.connect(self.close_current_tab)
        file_menu.addAction(close_file_action)
        
        file_menu.addSeparator()
        
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
            QTabWidget::pane { border: 1px solid #444; top: -1px; }
            QTabBar::tab {
                background: #2b2b2b;
                color: #aaa;
                padding: 8px 12px;
                border: 1px solid #444;
                border-bottom: none;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: #1e1e1e;
                color: #fff;
                border-bottom: 1px solid #1e1e1e;
            }
            QTabBar::tab:!selected:hover {
                background: #333;
            }
        """)
        
        # Start with one empty tab
        self.new_graph()

    @property
    def clipboard(self):
        tab = self.get_current_tab()
        return tab.clipboard if tab else []

    def get_current_tab(self) -> Optional[EditorTab]:
        widget = self.tabs.currentWidget()
        if isinstance(widget, EditorTab):
            return widget
        return None

    def update_window_title(self):
        tab = self.get_current_tab()
        if tab:
            import os
            filename = os.path.basename(tab.current_file_path) if tab.current_file_path else "Untitled"
            if tab.is_dirty:
                filename += "*"
            self.setWindowTitle(f"{filename} - AntiGravity")
        else:
            self.setWindowTitle("AntiGravity")

    def on_tab_changed(self, index):
        self.update_window_title()
        self.update_undo_redo_actions()

    def on_tab_dirty_changed(self, is_dirty):
        # Find which tab sent this
        sender = self.sender()
        if isinstance(sender, EditorTab):
            idx = self.tabs.indexOf(sender)
            if idx != -1:
                import os
                filename = os.path.basename(sender.current_file_path) if sender.current_file_path else "Untitled"
                if is_dirty:
                    filename += "*"
                self.tabs.setTabText(idx, filename)
                
            if sender == self.get_current_tab():
                self.update_window_title()

    def on_tab_status_message(self, message, timeout):
        if self.sender() == self.get_current_tab():
            self.statusBar().showMessage(message, timeout)

    # --- Tab Management ---
    def add_tab(self, graph: Optional[Graph] = None, filename: str = None):
        tab = EditorTab(self, graph, self.queue_manager)
        if filename:
            tab.current_file_path = filename
        
        tab.dirty_changed.connect(self.on_tab_dirty_changed)
        tab.status_message.connect(self.on_tab_status_message)
        tab.command_manager.add_listener(self.update_undo_redo_actions)
        
        import os
        display_name = os.path.basename(filename) if filename else "Untitled"
        index = self.tabs.addTab(tab, display_name)
        self.tabs.setCurrentIndex(index)
        return tab

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if isinstance(widget, EditorTab):
            if widget.close_check():
                self.tabs.removeTab(index)
                widget.deleteLater()
                if self.tabs.count() == 0:
                     self.new_graph()

    def close_current_tab(self):
        idx = self.tabs.currentIndex()
        if idx != -1:
            self.close_tab(idx)

    def closeEvent(self, event: QCloseEvent):
        # Check all tabs
        for i in reversed(range(self.tabs.count())):
            widget = self.tabs.widget(i)
            if isinstance(widget, EditorTab):
                self.tabs.setCurrentIndex(i) # Show tab being checked
                if not widget.close_check():
                    event.ignore()
                    return
        
        # If all checks passed
        event.accept()

    # --- Actions ---
    def new_graph(self):
        self.add_tab()

    def load_graph(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Graph", "", "JSON Files (*.json)")
        if not path: return
        try:
            self.logger.info(f"Loading graph from {path}")
            with open(path, 'r') as f:
                data = json.load(f)
            
            graph = Graph.from_dict(data)
            self.add_tab(graph, path)
            self.logger.info("Load successful")
        except Exception as e:
            self.logger.error(f"Load failed: {e}")
            QMessageBox.critical(self, "Load Error", str(e))

    def save_current_tab(self):
        tab = self.get_current_tab()
        if tab:
            if not tab.current_file_path:
                self.save_current_tab_as()
            else:
                tab.save_to_path(tab.current_file_path)
                self.update_window_title()

    def save_current_tab_as(self):
        tab = self.get_current_tab()
        if tab:
            path, _ = QFileDialog.getSaveFileName(self, "Save Graph", "", "JSON Files (*.json)")
            if not path: return
            if not path.endswith(".json"):
                path += ".json"
            tab.save_to_path(path)
            
            # Update Tab Name
            import os
            self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(path))
            self.update_window_title()

    def save_all(self):
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, EditorTab) and widget.is_dirty:
                self.tabs.setCurrentIndex(i)
                if not widget.current_file_path:
                    self.save_current_tab_as()
                else:
                    widget.save_to_path(widget.current_file_path)

    def merge_graph(self):
        tab = self.get_current_tab()
        if not tab: return
        
        path, _ = QFileDialog.getOpenFileName(self, "Merge Graph", "", "JSON Files (*.json)")
        if not path: return
        
        try:
            import os
            filename = os.path.splitext(os.path.basename(path))[0]
            self.logger.info(f"Merging graph from {path}")
            with open(path, 'r') as f:
                data = json.load(f)
            
            new_graph = Graph.from_dict(data)
            
            # 1. Remap IDs
            id_map = {}
            nodes_to_add = []
            
            for node in new_graph.nodes.values():
                old_id = node.id
                new_id = tab.graph.generate_copy_id(old_id) 
                node.id = new_id
                id_map[old_id] = new_id
                
                # Check for Name Collisions
                if node.name:
                    base_name = node.name
                    if tab.graph.is_name_unique(base_name):
                         pass
                    else:
                        import re
                        match = re.search(r'_copy(\d+)$', base_name)
                        if match:
                             base_name = base_name[:match.start()]
                        
                        suffix = 1
                        while not tab.graph.is_name_unique(f"{base_name}_{filename}_{suffix}"):
                             suffix += 1
                        node.name = f"{base_name}_{filename}_{suffix}"
                        
                node.pos_x += 50
                node.pos_y += 50
                nodes_to_add.append(node)
                
            # 2. Add Links
            links_to_add = []
            for link in new_graph.links.values():
                 new_source = id_map.get(link.source_id)
                 new_target = id_map.get(link.target_id)
                 if new_source and new_target:
                      from core.node import Link
                      new_link = Link(source_id=new_source, target_id=new_target)
                      links_to_add.append(new_link)
            
            from core.command import PasteNodesAndLinksCommand
            cmd = PasteNodesAndLinksCommand(tab.graph, nodes_to_add, links_to_add)
            tab.command_manager.execute(cmd)
            
            # Create Visuals
            tab.refresh_visuals()
            
            # Select merged nodes
            tab.scene.clearSelection()
            for node in nodes_to_add:
                if node.id in tab.node_items:
                    tab.node_items[node.id].setSelected(True)
                    
            self.logger.info("Merge successful")
            self.statusBar().showMessage(f"Merged {path}", 3000)
            
        except Exception as e:
            self.logger.error(f"Merge failed: {e}")
            QMessageBox.critical(self, "Merge Error", str(e))

    # --- Delegated Actions ---
    def undo(self):
        tab = self.get_current_tab()
        if tab: tab.undo()

    def redo(self):
        tab = self.get_current_tab()
        if tab: tab.redo()

    def add_node(self):
        tab = self.get_current_tab()
        if tab: tab.add_node_center()
    
    def add_node_at(self, pos: QPointF):
        # Used by context menu on canvas
        tab = self.get_current_tab()
        if tab: tab.add_node_at(pos)

    def copy_selection(self):
        tab = self.get_current_tab()
        if tab: tab.copy_selection()

    def cut_selection(self):
        tab = self.get_current_tab()
        if tab: tab.cut_selection()

    def paste_selection(self):
        tab = self.get_current_tab()
        if tab: tab.paste_selection()

    def trigger_rename(self):
        tab = self.get_current_tab()
        if tab: tab.trigger_rename()

    def duplicate_selection(self):
        tab = self.get_current_tab()
        if tab: tab.duplicate_selection()

    def delete_selection(self):
        tab = self.get_current_tab()
        if tab: tab.delete_selection()

    def update_undo_redo_actions(self):
        tab = self.get_current_tab()
        if tab:
            self.undo_action.setEnabled(tab.command_manager.can_undo())
            self.redo_action.setEnabled(tab.command_manager.can_redo())
            
            undo_desc = tab.command_manager.get_undo_description()
            redo_desc = tab.command_manager.get_redo_description()
            
            self.undo_action.setText(f"Undo {undo_desc}" if undo_desc else "Undo")
            self.redo_action.setText(f"Redo {redo_desc}" if redo_desc else "Redo")
        else:
            self.undo_action.setEnabled(False)
            self.redo_action.setEnabled(False)

    def show_log_window(self):
        self.log_window.show()
        self.log_window.raise_()
        
    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            pass
