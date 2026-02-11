
from PySide6.QtWidgets import QGraphicsObject, QGraphicsProxyWidget, QTextEdit, QPushButton, QGraphicsItem, QLineEdit
from PySide6.QtCore import QRectF, Qt, Signal, QPointF, QRegularExpression, QTimer, QTime
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont, QRegularExpressionValidator, QFontMetrics

from core.node import Node
from core.graph import Graph
from core.provider_status import ProviderStatusManager
from core.provider_manager import ProviderManager
from .node_settings_dialog import NodeSettingsDialog
from .theme import Colors, Sizing, Spacing, Typography, Timing, Styles
from .node_layout_manager import NodeLayoutManager
from .node_painter import NodePainter
from core.event_bus import EventBus

class StatusOverlayItem(QGraphicsItem):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_item = parent
        # Important: High Z-Value to draw on top of QGraphicsProxyWidgets (children of NodeItem)
        self.setZValue(100)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.setEnabled(False) # Don't catch events, let them pass through to children or parent node 
        
    def boundingRect(self):
        return self.parent_item.boundingRect()
        
    def paint(self, painter: QPainter, option, widget):
        state = self.parent_item.execution_state
        if state not in ["RUNNING", "QUEUED"]:
            return
            

            
        width = self.parent_item.width
        height = self.parent_item.height
        
        # Center of the node
        cx = width / 2
        cy = height / 2
        
        # Draw semi-transparent background for better visibility
        overlay_w = Sizing.OVERLAY_WIDTH
        overlay_h = Sizing.OVERLAY_HEIGHT
        bg_rect = QRectF(cx - overlay_w/2, cy - overlay_h/2, overlay_w, overlay_h)
        painter.setBrush(QBrush(QColor(Colors.OVERLAY_BG)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bg_rect, 10, 10)
        
        # Prepare Spinner
        painter.save()
        painter.translate(cx, cy - 10)
        
        spinner_angle = getattr(self.parent_item, 'spinner_angle', 0)
        painter.rotate(spinner_angle)
        
        # Simple Circle Spinner
        pen_width = Sizing.SPINNER_WIDTH
        radius = Sizing.SPINNER_RADIUS
        
        # Track
        painter.setPen(QPen(QColor(Colors.BORDER_DEFAULT), pen_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(-radius, -radius, radius * 2, radius * 2)
        
        # Active Arc
        if state == "RUNNING":
            arc_color = QColor(Colors.RUNNING)
        else:
            arc_color = QColor(Colors.QUEUED) # Yellow/Dirty for queued
            
        pen = QPen(arc_color, pen_width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # Draw a 90 degree arc
        painter.drawArc(-radius, -radius, radius * 2, radius * 2, 0, 90 * 16)
        
        painter.restore()
        
        # Text Below
        painter.setFont(QFont(Typography.FAMILY_PRIMARY, Typography.SIZE_NORMAL, QFont.Bold))
        painter.setPen(QPen(QColor(Colors.TEXT_PRIMARY)))
        
        text_y = cy + 25
        status_text = ""
        if state == "RUNNING":
            secs = self.parent_item.elapsed_ms / 1000.0
            status_text = f"{secs:.1f}s"
        else:
            status_text = "Queued"
            
        # Center text
        metrics = painter.fontMetrics()
        tw = metrics.horizontalAdvance(status_text)
        painter.drawText(cx - tw/2, text_y, status_text)

class NodeItem(QGraphicsObject):
    # Signals
    promptChanged = Signal(str, str) # node_id, new_prompt
    runClicked = Signal(str) # node_id
    cancelClicked = Signal(str) # node_id - NEW
    
    # Undo/Redo Support Signals
    moveFinished = Signal(str, QPointF, QPointF) # node_id, old_pos, new_pos
    promptEditFinished = Signal(str, str, str) # node_id, old_text, new_text
    outputEditFinished = Signal(str, str, str) # node_id, old_text, new_text
    nameEditFinished = Signal(str, str, str) # node_id, old_name, new_name
    
    # Wiring Signals
    wireDragStarted = Signal(str, QPointF)  # node_id, scene_pos
    wireDragMoved = Signal(QPointF)
    wireDragReleased = Signal(QPointF)
    inputWireDragStarted = Signal(str, str, QPointF)  # node_id, link_id_to_remove, scene_pos
    positionChanged = Signal(str)
    
    # Resize constants
    RESIZE_HANDLE_SIZE = Sizing.RESIZE_HANDLE_SIZE
    MIN_WIDTH = Sizing.NODE_MIN_WIDTH
    MAX_WIDTH = Sizing.NODE_MAX_WIDTH
    MIN_HEIGHT = Sizing.NODE_MIN_HEIGHT
    MAX_HEIGHT = Sizing.NODE_MAX_HEIGHT
    MIN_PROMPT_HEIGHT = Sizing.MIN_PROMPT_HEIGHT
    MIN_OUTPUT_HEIGHT = Sizing.MIN_OUTPUT_HEIGHT

    def __init__(self, node: Node, graph: Graph):
        super().__init__()
        self.node = node
        self.graph = graph
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # Layout Manager
        self.layout_manager = NodeLayoutManager(self)
        
        # Execution State
        self.execution_state = "IDLE" # IDLE, QUEUED, RUNNING
        self.run_timer = QTimer()
        self.run_timer.timeout.connect(self.on_timer_tick)
        self.run_start_time = None
        self.elapsed_ms = 0
        self.spinner_angle = 0
        
        self.provider_status = ProviderStatusManager.instance()
        self.provider_status.status_changed.connect(self.on_provider_status_changed)
        
        # Listen for global settings changes
        EventBus.instance().settings_changed.connect(self.on_settings_changed)
        
        # Initial Check
        # Trigger a check if we don't know the status yet
        effective_provider = self.resolve_effective_provider()
        if self.provider_status.get_status(effective_provider) is None:
             pass # get_status triggers check internally

        
        # Read size from node
        self.width = max(self.node.width, self.MIN_WIDTH)
        self.height = max(self.node.height, self.MIN_HEIGHT)
        self.setPos(node.pos_x, node.pos_y)
        
        # Resize state
        self.is_resizing = False
        self.is_resizing_separator = False
        self.is_wiring = False
        self.is_wiring_from_input = False  # Track if dragging from input port
        
        # Overlay
        self.status_overlay = StatusOverlayItem(self)
        self.status_overlay.hide() # Hidden by default until RUNNING or QUEUED
        self.resize_start_pos = None
        self.resize_start_size = None
        self.resize_start_heights = None
        
        # --- UI PROXIES ---
        
        # 1. Prompt Editor
        class PromptEdit(QTextEdit):
            focusOut = Signal()
            def __init__(self, parent_item):
                super().__init__()
                self.parent_item = parent_item
                self.old_text = ""
                
            def focusInEvent(self, event):
                self.old_text = self.toPlainText()
                super().focusInEvent(event)
                
            def focusOutEvent(self, event):
                if self.toPlainText() != self.old_text:
                    self.parent_item.promptEditFinished.emit(self.parent_item.node.id, self.old_text, self.toPlainText())
                super().focusOutEvent(event)
                self.focusOut.emit()

            def keyPressEvent(self, event):
                if event.key() == Qt.Key_Return and (event.modifiers() & Qt.ControlModifier):
                    self.parent_item.on_run_btn_clicked()
                    return
                super().keyPressEvent(event)

        self.prompt_edit = PromptEdit(self)
        self.prompt_edit.setPlaceholderText("System: Enter prompt here...")
        self.prompt_edit.setPlainText(node.prompt)
        # Enable scroll wheel handling
        self.prompt_edit.setAcceptDrops(True)
        self.prompt_edit.setStyleSheet(Styles.PROMPT_EDIT)
        self.proxy_prompt = QGraphicsProxyWidget(self)
        self.proxy_prompt.setWidget(self.prompt_edit)
        self.prompt_edit.textChanged.connect(self.on_text_changed)
        
        # 2. Output Display (ReadOnly)
        self.output_edit = QTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("Output (Cached): Waiting for run...")
        self.output_edit.setMarkdown(node.cached_output or "")
        self.output_edit.setStyleSheet(Styles.OUTPUT_EDIT)
        self.proxy_output = QGraphicsProxyWidget(self)
        self.proxy_output.setWidget(self.output_edit)
        
        # 3. Run Button
        self.run_btn = QPushButton("RUN")
        self.run_btn.setStyleSheet(Styles.BUTTON_RUN)
        self.proxy_btn = QGraphicsProxyWidget(self)
        self.proxy_btn.setWidget(self.run_btn)
        self.run_btn.clicked.connect(self.on_run_btn_clicked)
        
        # 4. Name Editor (Header)
        class NameEdit(QLineEdit):
            finished = Signal(str)
            def __init__(self, parent_item):
                super().__init__()
                self.parent_item = parent_item
                self.old_text = ""
                self._is_handling_finish = False
                
            def focusInEvent(self, event):
                self.old_text = self.text()
                super().focusInEvent(event)
                
            def focusOutEvent(self, event):
                if not self._is_handling_finish and self.isVisible():
                    self.complete_editing()
                super().focusOutEvent(event)

            def keyPressEvent(self, event):
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    self.complete_editing()
                    return
                if event.key() == Qt.Key_Escape:
                    self.setText(self.old_text)
                    self._is_handling_finish = True
                    self.hide()
                    if self.parent_item.scene() and self.parent_item.scene().views():
                        self.parent_item.scene().views()[0].setFocus()
                    self._is_handling_finish = False
                    return
                super().keyPressEvent(event)

            def complete_editing(self):
                if self._is_handling_finish: return
                self._is_handling_finish = True
                
                new_name = self.text().strip()
                
                # Validation logic
                error_msg = ""
                if not new_name:
                    error_msg = "Node name cannot be empty."
                elif not self.parent_item.graph.is_name_unique(new_name, exclude_node_id=self.parent_item.node.id):
                    error_msg = f"The name '{new_name}' is already in use by another node."
                
                if error_msg:
                    from PySide6.QtWidgets import QMessageBox
                    box = QMessageBox(self.parent_item.scene().views()[0])
                    box.setIcon(QMessageBox.Warning)
                    box.setWindowTitle("Invalid Node Name")
                    box.setText(f"{error_msg}\n\nClick 'OK' to reset to the original name, or 'Cancel' to continue editing.")
                    box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                    
                    if box.exec() == QMessageBox.Ok:
                        # Reset and Close
                        self.setText(self.old_text)
                        self.hide()
                        if self.parent_item.scene() and self.parent_item.scene().views():
                            self.parent_item.scene().views()[0].setFocus()
                    else:
                        # Continue editing
                        self.setFocus()
                        self._is_handling_finish = False
                        return
                else:
                    # Valid - Finish
                    self.hide()
                    if self.parent_item.scene() and self.parent_item.scene().views():
                        self.parent_item.scene().views()[0].setFocus()
                    if new_name != self.old_text:
                        self.finished.emit(new_name)
                    
                self._is_handling_finish = False

        self.name_edit = NameEdit(self)
        self.name_edit.setMaxLength(32)
        # Alphanumeric, space, and underscore
        regex = QRegularExpression("^[a-zA-Z0-9 _]*$")
        validator = QRegularExpressionValidator(regex, self.name_edit)
        self.name_edit.setValidator(validator)
        
        self.name_edit.setStyleSheet(Styles.NAME_EDIT)
        self.proxy_name = QGraphicsProxyWidget(self)
        self.proxy_name.setWidget(self.name_edit)
        self.proxy_name.hide()
        self.name_edit.finished.connect(self.on_name_edit_finished)
        self.name_edit.textChanged.connect(self.on_name_changed)

        # Set tooltip
        self.set_name_tooltip()

        # Initial layout
        self.update_layout()

    def set_name_tooltip(self):
        display_name = self.node.name or "Unnamed Node"
        self.setToolTip(f"Node: {display_name}")

    def get_min_width(self):
        return self.layout_manager.get_min_width()

    def update_layout(self):
        self.layout_manager.update_structure()
        
        # Update bounding rect
        self.prepareGeometryChange()
        self.update()
    
    def on_text_changed(self):
        self.node.prompt = self.prompt_edit.toPlainText()
        self.promptChanged.emit(self.node.id, self.node.prompt)

    def edit_name(self):
        self.name_edit.setText(self.node.name or self.node.id)
        self.proxy_name.show()
        self.name_edit.setFocus()
        self.name_edit.selectAll()
        self.update()

    def on_name_changed(self, text):
        text = text.strip()
        is_empty = not text
        is_duplicate = not self.graph.is_name_unique(text, exclude_node_id=self.node.id)
        
        if is_empty or is_duplicate:
            self.name_edit.setStyleSheet(Styles.NAME_EDIT_ERROR)
        else:
            self.name_edit.setStyleSheet(Styles.NAME_EDIT)

    def on_name_edit_finished(self, new_name):
        self.nameEditFinished.emit(self.node.id, self.node.name, new_name)
        self.set_name_tooltip()
        self.update()
        
    def update_output(self, text: str):
        self.node.cached_output = text
        self.output_edit.setMarkdown(text)
        self.update() # Redraw for token/status updates

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)
    
    def get_resize_handle_rect(self):
        return self.layout_manager.get_resize_handle_rect()
    
    def get_separator_rect(self):
        return self.layout_manager.get_separator_rect()
    
    def get_cursor_for_position(self, pos):
        """Get appropriate cursor for position."""
        if self.get_resize_handle_rect().contains(pos):
            return Qt.SizeFDiagCursor
        elif self.get_separator_rect().contains(pos):
            return Qt.SizeVerCursor
        elif self.layout_manager.get_output_port_rect().contains(pos):
            return Qt.PointingHandCursor
        elif self.get_model_label_rect().contains(pos):
            return Qt.PointingHandCursor
        elif self.get_input_port_at(pos):
            return Qt.PointingHandCursor
        return Qt.ArrowCursor

    def get_model_label_rect(self):
        return self.layout_manager.get_model_label_rect()

    def check_input_drop(self, scene_pos):
        """Check if a scene position is over the input port area of this node."""
        local_pos = self.mapFromScene(scene_pos)
        # Input ports are on the left side
        # Accept drops on the entire left third of the node, below the header
        input_width = self.width / 3
        input_area = QRectF(0, Sizing.HEADER_HEIGHT, input_width, self.height - Sizing.HEADER_HEIGHT)
        return input_area.contains(local_pos)

    def check_output_drop(self, scene_pos):
        """Check if a scene position is over the output port area of this node."""
        local_pos = self.mapFromScene(scene_pos)
        # Output port is on the right side
        # Accept drops on the entire right third of the node, below the header
        output_width = self.width / 3
        output_area = QRectF(self.width - output_width, Sizing.HEADER_HEIGHT, output_width, self.height - Sizing.HEADER_HEIGHT)
        return output_area.contains(local_pos)

    def get_input_port_at(self, pos):
        """Check if position is over an input port and return the link_id if so."""
        # Input ports are drawn at y = HEADER_HEIGHT + index * 24
        idx = 0
        for idx, link_id in enumerate(self.node.input_links):
            y_offset = Sizing.HEADER_HEIGHT + idx * 24
            # Make the hitbox a bit wider and taller for easier clicking
            port_rect = QRectF(0, y_offset, 30, 24)
            if port_rect.contains(pos):
                return link_id
        
        # Also check the "Empty/Add Port" slot at the bottom
        num_existing = len(self.node.input_links)
        y_offset = Sizing.HEADER_HEIGHT + num_existing * 24
        new_port_rect = QRectF(0, y_offset, 30, 24)
        if new_port_rect.contains(pos):
            return "NEW_PORT"
            
        return None

    # --- Helpers ---
    def resolve_provider_model_text(self):
        config_provider = self.node.config.provider
        config_model = self.node.config.model
        return ProviderManager.resolve_display_text(config_provider, config_model)

    def resolve_effective_provider(self):
        """Helper to determine the actual provider in use (resolving Default)."""
        config_provider = self.node.config.provider
        config_model = self.node.config.model
        return ProviderManager.resolve_effective_provider(config_provider, config_model)

    def on_provider_status_changed(self, provider, is_active):
        # Check if this node uses the updated provider
        effective = self.resolve_effective_provider()
        if effective == provider:
            self.update()

    def on_settings_changed(self, key, value):
        """Handle global settings changes."""
        # If default provider or models change, update display
        if key in ["default_provider", "openai_model", "gemini_model", "ollama_model", "openrouter_model"]:
            self.update()

    # --- Metrics ---
    
    # ... (existing methods) ...

    def paint(self, painter: QPainter, option, widget):
        NodePainter.paint(painter, self, option, widget)
        
    def calculate_context_usage(self):
        prompt_len = len(self.node.prompt)
        return prompt_len 
        
    def set_metrics(self, payload_val, max_val):
        self._payload_chars = payload_val
        self._max_chars = max_val
        self.update()

    def on_run_btn_clicked(self):
        if self.execution_state == "IDLE":
             self.runClicked.emit(self.node.id)
        else:
             self.cancelClicked.emit(self.node.id)

    def set_execution_state(self, state):
        self.execution_state = state
        
        if state == "RUNNING":
            self.status_overlay.show()
            self.run_start_time = QTime.currentTime()
            self.elapsed_ms = 0
            self.run_timer.start(50) # Faster update for smooth spinner
            self.run_btn.setText("CANCEL")
            self.run_btn.setStyleSheet(Styles.BUTTON_CANCEL)
            self.output_edit.setPlaceholderText("Running...")
        elif state == "QUEUED":
            self.status_overlay.show()
            self.run_timer.start(50) # Animate spinner even if queued (e.g. slow pulse or rotate)
            self.elapsed_ms = 0
            self.run_btn.setText("CANCEL") # allow cancel from queue
            self.run_btn.setStyleSheet(Styles.BUTTON_CANCEL)
            self.output_edit.setPlaceholderText("Queued...")
        else: # IDLE
            self.status_overlay.hide()
            self.run_timer.stop()

            self.run_btn.setText("RUN")
            self.run_btn.setStyleSheet(Styles.BUTTON_RUN)
            # Placeholder updated by externally setting output or cleared
            
        self.update()
        if hasattr(self, 'status_overlay'):
             self.status_overlay.update()

    def on_timer_tick(self):
        if not hasattr(self, 'spinner_angle'):
             self.spinner_angle = 0
             
        if self.execution_state == "RUNNING" or self.execution_state == "QUEUED":
            self.spinner_angle = (self.spinner_angle + Timing.SPINNER_ROTATION_DEGREES) % 360
            if self.execution_state == "RUNNING" and self.run_start_time:
                self.elapsed_ms = self.run_start_time.msecsTo(QTime.currentTime())
            self.update() # trigger paint
            self.status_overlay.update() # Update overlay specifically

    def contextMenuEvent(self, event):
        from PySide6.QtWidgets import QMenu, QApplication
        from PySide6.QtGui import QAction
        
        view = self.scene().views()[0]
        window = view.window()
        
        menu = QMenu()
        run_act = QAction("Run Node", menu)
        run_act.triggered.connect(lambda: self.runClicked.emit(self.node.id))
        menu.addAction(run_act)
        
        rename_act = QAction("Rename", menu)
        rename_act.triggered.connect(self.edit_name)
        menu.addAction(rename_act)
        
        menu.addSeparator()
        
        copy_act = QAction("Copy", menu)
        copy_act.triggered.connect(window.copy_selection)
        menu.addAction(copy_act)
        
        cut_act = QAction("Cut", menu)
        cut_act.triggered.connect(window.cut_selection)
        menu.addAction(cut_act)
        
        del_act = QAction("Delete", menu)
        del_act.triggered.connect(window.delete_selection)
        menu.addAction(del_act)
        
        menu.exec(event.screenPos())
        event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.pos().y() < 36: # Header area
            self.edit_name()
            event.accept()
        else:
            QGraphicsObject.mouseDoubleClickEvent(self, event)

    def hoverMoveEvent(self, event):
        self.setCursor(self.get_cursor_for_position(event.pos()))
        super().hoverMoveEvent(event)
        
    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        pos = event.pos()
        
        # Check for resize handle
        if self.get_resize_handle_rect().contains(pos):
            self.is_resizing = True
            self.resize_start_pos = event.scenePos()
            self.resize_start_size = QPointF(self.width, self.height)
            event.accept()
            return

        # Check for separator resize
        if self.get_separator_rect().contains(pos):
            self.is_resizing_separator = True
            self.resize_start_pos = event.scenePos()
            self.resize_start_heights = (self.node.prompt_height, self.node.output_height)
            event.accept()
            return

        # Check for input port click (to disconnect/reconnect)
        input_link_id = self.get_input_port_at(pos)
        if input_link_id:
            # User clicked on an input port - initiate drag from input
            self.is_wiring = True
            self.is_wiring_from_input = True
            
            # Get the center of the input port for visual feedback
            if input_link_id == "NEW_PORT":
                num_existing = len(self.node.input_links)
                y_offset = Sizing.HEADER_HEIGHT + num_existing * 24 + 12
                # For NEW_PORT, we pass link_id as None to signal reverse wiring without deletion
                link_to_pass = None
            else:
                idx = self.node.input_links.index(input_link_id)
                y_offset = Sizing.HEADER_HEIGHT + idx * 24 + 12
                link_to_pass = input_link_id
                
            port_center = self.mapToScene(QPointF(0, y_offset))
            self.inputWireDragStarted.emit(self.node.id, link_to_pass, port_center)
            event.accept()
            return

        # Check for output port click (Wiring)
        if self.layout_manager.get_output_port_rect().contains(pos):
             self.is_wiring = True
             self.is_wiring_from_input = False
             center = self.layout_manager.get_output_port_rect().center()
             self.wireDragStarted.emit(self.node.id, self.mapToScene(center))
             event.accept()
             return

        # Check for provider label click (Settings)
        if self.get_model_label_rect().contains(pos):
             views = self.scene().views()
             parent_widget = views[0] if views else None
             
             dialog = NodeSettingsDialog(
                 current_provider=self.node.config.provider,
                 current_model=self.node.config.model,
                 parent=parent_widget
             )
             if dialog.exec():
                 # Update node config with selected values
                 self.node.config.provider = dialog.selected_provider
                 self.node.config.model = dialog.selected_model
                 # Settings updated, trigger repaint and mark dirty
                 self.update()
                 # Emit signal to trigger dirty state in EditorTab
                 self.promptChanged.emit(self.node.id, self.node.prompt)
                 
             event.accept()
             return
            
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_resizing:
            delta = event.scenePos() - self.resize_start_pos
            new_width = max(self.resize_start_size.x() + delta.x(), self.MIN_WIDTH)
            new_height = max(self.resize_start_size.y() + delta.y(), self.MIN_HEIGHT)
            
            self.width = new_width
            self.height = new_height
            
            self.prepareGeometryChange()
            self.update_layout()
            self.positionChanged.emit(self.node.id)
            event.accept()
            return
            
        if self.is_resizing_separator:
            delta_y = event.scenePos().y() - self.resize_start_pos.y()
            # If delta_y is positive, separator moves down (prompt gets bigger)
            
            start_prompt_h, start_output_h = self.resize_start_heights
            
            new_prompt_h = max(self.MIN_PROMPT_HEIGHT, start_prompt_h + delta_y)
            
            # Check if output gets too small
            # We don't change total node height here, just distribution
            # calculate available text height
            total_text_h = start_prompt_h + start_output_h
            if new_prompt_h > total_text_h - self.MIN_OUTPUT_HEIGHT:
                new_prompt_h = total_text_h - self.MIN_OUTPUT_HEIGHT
                
            self.node.prompt_height = new_prompt_h
            # output height is recalculated in update_layout based on remaining space
            
            self.update_layout()
            event.accept()
            return

        if self.is_wiring:
            self.wireDragMoved.emit(event.scenePos())
            event.accept()
            return

        super().mouseMoveEvent(event)
        if self.isSelected():
            self.positionChanged.emit(self.node.id)

    def mouseReleaseEvent(self, event):
        if self.is_resizing or self.is_resizing_separator:
            self.is_resizing = False
            self.is_resizing_separator = False
            self.update_layout()
            self.positionChanged.emit(self.node.id)
            event.accept()
        elif self.is_wiring:
            self.is_wiring = False
            self.is_wiring_from_input = False
            self.wireDragReleased.emit(event.scenePos())
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
             # Snap to grid?
             pass
        elif change == QGraphicsItem.ItemPositionHasChanged:
             self.node.pos_x = self.x()
             self.node.pos_y = self.y()
             self.moveFinished.emit(self.node.id, QPointF(self.x(), self.y()), QPointF(self.x(), self.y())) # Keep it simple for now, command manager handles true old pos
        return super().itemChange(change, value)
