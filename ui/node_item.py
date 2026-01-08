
from PySide6.QtWidgets import QGraphicsObject, QGraphicsProxyWidget, QTextEdit, QPushButton, QGraphicsItem, QLineEdit
from PySide6.QtCore import QRectF, Qt, Signal, QPointF, QRegularExpression
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont, QRegularExpressionValidator

from core.node import Node
from core.graph import Graph

class NodeItem(QGraphicsObject):
    # Signals
    promptChanged = Signal(str, str) # node_id, new_prompt
    runClicked = Signal(str) # node_id
    
    # Undo/Redo Support Signals
    moveFinished = Signal(str, QPointF, QPointF) # node_id, old_pos, new_pos
    promptEditFinished = Signal(str, str, str) # node_id, old_text, new_text
    outputEditFinished = Signal(str, str, str) # node_id, old_text, new_text
    nameEditFinished = Signal(str, str, str) # node_id, old_name, new_name
    
    # Wiring Signals
    wireDragStarted = Signal(str, QPointF) 
    wireDragMoved = Signal(QPointF)
    wireDragReleased = Signal(QPointF)
    positionChanged = Signal(str)
    
    # Resize constants
    RESIZE_HANDLE_SIZE = 12
    MIN_WIDTH = 200
    MAX_WIDTH = 800
    MIN_HEIGHT = 300
    MAX_HEIGHT = 1200
    MIN_PROMPT_HEIGHT = 60
    MIN_OUTPUT_HEIGHT = 60

    def __init__(self, node: Node, graph: Graph):
        super().__init__()
        self.node = node
        self.graph = graph
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # Read size from node
        self.width = node.width
        self.height = node.height
        self.setPos(node.pos_x, node.pos_y)
        
        # Resize state
        self.is_resizing = False
        self.is_resizing_separator = False
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
                    self.parent_item.runClicked.emit(self.parent_item.node.id)
                    return
                super().keyPressEvent(event)

        self.prompt_edit = PromptEdit(self)
        self.prompt_edit.setPlaceholderText("System: Enter prompt here...")
        self.prompt_edit.setPlainText(node.prompt)
        self.prompt_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e; 
                color: #e0e0e0; 
                border: 1px solid #444; 
                border-radius: 4px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """)
        self.proxy_prompt = QGraphicsProxyWidget(self)
        self.proxy_prompt.setWidget(self.prompt_edit)
        self.prompt_edit.textChanged.connect(self.on_text_changed)
        
        # 2. Output Display (ReadOnly)
        self.output_edit = QTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("Output (Cached): Waiting for run...")
        self.output_edit.setPlainText(node.cached_output or "")
        self.output_edit.setStyleSheet("""
            QTextEdit {
                background-color: #151515; 
                color: #aaf; 
                border: 1px solid #333; 
                border-radius: 4px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """)
        self.proxy_output = QGraphicsProxyWidget(self)
        self.proxy_output.setWidget(self.output_edit)
        
        # 3. Run Button
        self.run_btn = QPushButton("RUN")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d5a37; 
                color: white; 
                border-radius: 4px; 
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #3d7a47; }
            QPushButton:pressed { background-color: #1d3a27; }
        """)
        self.proxy_btn = QGraphicsProxyWidget(self)
        self.proxy_btn.setWidget(self.run_btn)
        self.run_btn.clicked.connect(lambda: self.runClicked.emit(self.node.id))
        
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
                        # We don't emit finished if we reset to old_text to avoid redundant command
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
        
        self.name_edit.setStyleSheet("""
            QLineEdit {
                background-color: #1a4d7a;
                color: white;
                border: 1px solid #00aaff;
                border-radius: 2px;
                font-family: 'Segoe UI';
                font-size: 13px;
                font-weight: bold;
                padding: 0px 4px;
            }
        """)
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

    def update_layout(self):
        """Update widget positions and sizes based on current node dimensions."""
        # Calculate available space
        header_height = 60
        footer_height = 50
        margin = 15
        available_height = self.height - header_height - footer_height
        
        # Use stored heights or distribute proportionally
        prompt_h = self.node.prompt_height
        output_h = self.node.output_height
        
        # Ensure they fit within available space
        total_text_height = prompt_h + output_h + 20  # 20px gap
        if total_text_height > available_height:
            # Scale down proportionally
            scale = available_height / total_text_height
            prompt_h = int(prompt_h * scale)
            output_h = int(output_h * scale)
        
        # Position prompt editor
        self.proxy_prompt.setPos(margin, header_height)
        self.proxy_prompt.resize(self.width - 2 * margin, prompt_h)
        
        # Position output editor
        output_y = header_height + prompt_h + 10
        self.proxy_output.setPos(margin, output_y)
        self.proxy_output.resize(self.width - 2 * margin, output_h)
        
        # Position run button
        btn_y = self.height - footer_height + 10
        self.proxy_btn.setPos(margin, btn_y)
        self.proxy_btn.resize(80, 30)

        # Position name edit
        self.proxy_name.setPos(38, 5)
        self.proxy_name.resize(self.width - 50, 26)
        
        # Update node stored values
        self.node.width = self.width
        self.node.height = self.height
        self.node.prompt_height = prompt_h
        self.node.output_height = output_h
        
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
            self.name_edit.setStyleSheet("QLineEdit { background-color: #4a1a1a; color: white; border: 1px solid red; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }")
        else:
            self.name_edit.setStyleSheet("QLineEdit { background-color: #1a4d7a; color: white; border: 1px solid #00aaff; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }")

    def on_name_edit_finished(self, new_name):
        # Validation already handled in NameEdit.complete_editing
        self.nameEditFinished.emit(self.node.id, self.node.name, new_name)
        self.set_name_tooltip()
        self.update()
        
    def update_output(self, text: str):
        self.node.cached_output = text
        self.output_edit.setPlainText(text)
        self.update() # Redraw for token/status updates

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)
    
    def get_resize_handle_rect(self):
        """Get the rectangle for the corner resize handle."""
        return QRectF(
            self.width - self.RESIZE_HANDLE_SIZE,
            self.height - self.RESIZE_HANDLE_SIZE,
            self.RESIZE_HANDLE_SIZE,
            self.RESIZE_HANDLE_SIZE
        )
    
    def get_separator_rect(self):
        """Get the rectangle for the text field separator."""
        separator_y = 60 + self.node.prompt_height + 5
        return QRectF(15, separator_y, self.width - 30, 10)
    
    def get_cursor_for_position(self, pos):
        """Get appropriate cursor for position."""
        if self.get_resize_handle_rect().contains(pos):
            return Qt.SizeFDiagCursor
        elif self.get_separator_rect().contains(pos):
            return Qt.SizeVerCursor
        return Qt.ArrowCursor

    # --- Metrics ---
    def calculate_context_usage(self):
        """Estimate token usage: History + Inputs + Prompt"""
        # 1. Prompt
        prompt_len = len(self.node.prompt)
        
        # 2. Inputs (Shallow check for this node's direct context scope)
        # Note: True context is recursive (history), but for UI we estimate roughly
        # or we should try to simulate the assembler.
        # Simulating assembler is safer if we want accuracy, but let's do sum of inputs for speed.
        inputs_len = 0
        
        # Find input nodes
        # We need access to graph or search items. 
        # Since NodeItem doesn't hold Graph ref directly (only Node), we might need to rely
        # on MainWindow to push this? Or we can traverse if we had links.
        # But Node has input_links (IDs). We don't have the node objects.
        # actually self.node is independent.
        # Workaround: MainWindow calls 'update_metrics' 
        return prompt_len # Placeholder if standalone
        
    def set_metrics(self, payload_val, max_val):
        self._payload_chars = payload_val
        self._max_chars = max_val
        self.update()

    def paint(self, painter: QPainter, option, widget):
        rect = self.boundingRect()
        painter.setRenderHint(QPainter.Antialiasing)
        
        # --- 1. Background & Selection Highlight ---
        # Selection border (Primary focus)
        if self.isSelected():
            # Glowing Blue Border for Selection
            painter.setPen(QPen(QColor("#00aaff"), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, 8, 8)
        
        # Now draw the main node background
        if self.node.is_dirty:
            # Dashed yellow border if dirty
            painter.setPen(QPen(QColor("#e6c60d"), 2, Qt.DashLine))
        else:
            # Standard border
            painter.setPen(QPen(QColor("#444"), 1))
            
        painter.setBrush(QBrush(QColor("#2b2b2b")))
        painter.drawRoundedRect(rect, 8, 8)
        
        # --- 2. Header ---
        header_path = QPainterPath()
        header_path.moveTo(0, 36)
        header_path.lineTo(0, 8)
        header_path.quadTo(0, 0, 8, 0)
        header_path.lineTo(self.width - 8, 0)
        header_path.quadTo(self.width, 0, self.width, 8)
        header_path.lineTo(self.width, 36)
        header_path.closeSubpath()
        
        # Highlight header if active/selected
        if self.isSelected():
            header_color = QColor("#1a4d7a") # Deeper blue for selected header
        else:
            header_color = QColor("#4d4418") if self.node.is_dirty else QColor("#383838")
            
        painter.fillPath(header_path, header_color)
        
        # Status Dot
        dot_color = QColor("#e6c60d") if self.node.is_dirty else QColor("#4caf50")
        painter.setBrush(QBrush(dot_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(15, 12, 12, 12)
        
        # Title (Node Name)
        painter.setPen(QPen(QColor("#fff")))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        
        display_name = self.node.name or self.node.id
        header_text_width = self.width - 60
        metrics = painter.fontMetrics()
        elided_name = metrics.elidedText(display_name, Qt.ElideRight, header_text_width)
        
        # Draw the name if not editing
        if not self.proxy_name.isVisible():
            painter.drawText(38, 24, elided_name)
        
        # 3. Labels
        painter.setPen(QPen(QColor("#888")))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(15, 52, f"Trace Depth: {self.node.config.trace_depth} (Auto)")
        
        # Model (Moved down to the right of Trace Depth)
        painter.setPen(QPen(QColor("#aaa")))
        painter.setFont(QFont("Segoe UI", 9))
        model_text = self.node.config.model or "Default"
        metrics_model = painter.fontMetrics()
        model_w = metrics_model.horizontalAdvance(model_text)
        painter.drawText(self.width - model_w - 15, 52, model_text)

        painter.setPen(QPen(QColor("#888")))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(15, 192, "Output (Cached):")
        
        # 4. Context Meter
        # Use stored metrics
        current = getattr(self, '_payload_chars', 0)
        limit = getattr(self, '_max_chars', 16000 * 4) # Default 16k tokens -> 64k chars
        
        ratio = min(current / max(limit, 1), 1.0)
        
        painter.setBrush(QBrush(QColor("#222")))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(120, 375, 165, 8, 4, 4)
        
        # Color based on usage
        meter_color = QColor("#2d8a4e")
        if ratio > 0.8: meter_color = QColor("#e6c60d")
        if ratio > 0.95: meter_color = QColor("#d32f2f")
        
        fill_width = int(165 * ratio)
        if fill_width > 0:
            painter.setBrush(QBrush(meter_color))
            painter.drawRoundedRect(120, 375, fill_width, 8, 4, 4)
        
        painter.setPen(QPen(QColor("#666")))
        painter.drawText(120, 370, "Context Payload:")
        
        # Convert chars to tokens usually /4
        tok_curr = current // 4
        tok_limit = limit // 4
        
        # Format k
        def fmt_k(v): return f"{v/1000:.1f}k" if v > 1000 else str(v)
        
        painter.drawText(220, 370, f"{fmt_k(tok_curr)} / {fmt_k(tok_limit)}")
        
        # 5. Output Tokens
        out_len = len(self.node.cached_output or "") if self.node.cached_output else 0
        est_tokens = out_len // 4
        painter.setPen(QPen(QColor("#aaa")))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(200, 420, f"Tokens: {est_tokens}")

        # 6. Ports
        out_port_y = 60
        painter.setBrush(QBrush(QColor("#777")))
        painter.setPen(QPen(QColor("#333")))
        painter.drawRect(self.width - 8, out_port_y, 8, 16)
        
        y_offset = 60
        for _ in self.node.input_links:
            painter.setBrush(QBrush(QColor("#fff"))) 
            painter.drawRect(0, y_offset, 8, 16)
            y_offset += 24
        painter.setBrush(QBrush(QColor("#555")))
        painter.drawRect(0, y_offset, 8, 16)
        painter.setPen(QPen(QColor("#aaa")))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(-12, y_offset + 12, "+")
        
        # 7. Resize Handle
        handle_rect = self.get_resize_handle_rect()
        painter.setPen(QPen(QColor("#666"), 1))
        painter.setBrush(Qt.NoBrush)
        # Draw grip lines
        for i in range(3):
            offset = i * 4
            painter.drawLine(
                int(handle_rect.left() + offset + 2),
                int(handle_rect.bottom() - 2),
                int(handle_rect.right() - 2),
                int(handle_rect.top() + offset + 2)
            )

    def contextMenuEvent(self, event):
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        # We need to reach the MainWindow for some actions, or emit signals
        # For simplicity, let's look for the scene's views[0].window()
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
            super().mouseDoubleClickEvent(event)

    def hoverMoveEvent(self, event):
        """Update cursor based on hover position."""
        cursor = self.get_cursor_for_position(event.pos())
        self.setCursor(cursor)
        super().hoverMoveEvent(event)
    
    def mousePressEvent(self, event):
        pos = event.pos()
        
        # Check for resize handle
        if self.get_resize_handle_rect().contains(pos):
            self.is_resizing = True
            self.resize_start_pos = event.pos()
            self.resize_start_size = (self.width, self.height)
            event.accept()
            return
        
        # Store start position for undo
        self.move_start_scene_pos = self.scenePos()
        
        # Check for separator resize
        if self.get_separator_rect().contains(pos):
            self.is_resizing_separator = True
            self.resize_start_pos = event.pos()
            self.resize_start_heights = (self.node.prompt_height, self.node.output_height)
            event.accept()
            return
        
        # Hit detection for Output Port
        out_port_rect = QRectF(self.width - 25, 45, 40, 40)
        if out_port_rect.contains(pos):
            self.is_wiring = True
            port_center = QPointF(self.width - 4, 68)
            scene_pos = self.mapToScene(port_center)
            self.wireDragStarted.emit(self.node.id, scene_pos)
            event.accept()
        else:
            self.is_wiring = False
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_resizing:
            # Corner resize
            delta = event.pos() - self.resize_start_pos
            new_width = max(self.MIN_WIDTH, min(self.MAX_WIDTH, self.resize_start_size[0] + delta.x()))
            new_height = max(self.MIN_HEIGHT, min(self.MAX_HEIGHT, self.resize_start_size[1] + delta.y()))
            
            self.width = new_width
            self.height = new_height
            self.update_layout()
            
            # Notify that position/size changed (for wire updates)
            self.positionChanged.emit(self.node.id)
            event.accept()
            return
        
        if self.is_resizing_separator:
            # Separator resize
            delta_y = event.pos().y() - self.resize_start_pos.y()
            new_prompt_h = max(self.MIN_PROMPT_HEIGHT, self.resize_start_heights[0] + delta_y)
            new_output_h = max(self.MIN_OUTPUT_HEIGHT, self.resize_start_heights[1] - delta_y)
            
            # Ensure both meet minimums
            if new_prompt_h >= self.MIN_PROMPT_HEIGHT and new_output_h >= self.MIN_OUTPUT_HEIGHT:
                self.node.prompt_height = int(new_prompt_h)
                self.node.output_height = int(new_output_h)
                self.update_layout()
            
            event.accept()
            return
        
        if hasattr(self, 'is_wiring') and self.is_wiring:
            scene_pos = self.mapToScene(event.pos())
            self.wireDragMoved.emit(scene_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_resizing:
            self.is_resizing = False
            self.resize_start_pos = None
            self.resize_start_size = None
            event.accept()
            return
        
        if self.is_resizing_separator:
            self.is_resizing_separator = False
            self.resize_start_pos = None
            self.resize_start_heights = None
            event.accept()
            return
        
        if hasattr(self, 'is_wiring') and self.is_wiring:
            self.is_wiring = False
            scene_pos = self.mapToScene(event.pos())
            self.wireDragReleased.emit(scene_pos)
            event.accept()
        else:
            old_pos = getattr(self, 'move_start_scene_pos', self.pos())
            super().mouseReleaseEvent(event)
            new_pos = self.scenePos()
            
            if old_pos != new_pos:
                self.moveFinished.emit(self.node.id, old_pos, new_pos)
            
            # Force full scene redraw to clear any drag artifacts
            if self.scene():
                self.scene().update()

    def check_input_drop(self, scene_pos: QPointF) -> bool:
        local_pos = self.mapFromScene(scene_pos)
        y_offset = 60 + len(self.node.input_links) * 24
        placeholder_rect = QRectF(-25, y_offset - 10, 50, 40)
        return placeholder_rect.contains(local_pos)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.node.pos_x = value.x()
            self.node.pos_y = value.y()
            self.positionChanged.emit(self.node.id)
        return super().itemChange(change, value)
