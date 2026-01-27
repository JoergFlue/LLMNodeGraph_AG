
from PySide6.QtWidgets import QGraphicsObject, QGraphicsProxyWidget, QTextEdit, QPushButton, QGraphicsItem, QLineEdit
from PySide6.QtCore import QRectF, Qt, Signal, QPointF, QRegularExpression, QTimer, QTime
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont, QRegularExpressionValidator, QFontMetrics

from core.node import Node
from core.graph import Graph
from core.settings_manager import SettingsManager
from core.provider_status import ProviderStatusManager
from .node_settings_dialog import NodeSettingsDialog
from .theme import Colors, Sizing, Spacing, Typography, Timing, Styles

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
    wireDragStarted = Signal(str, QPointF) 
    wireDragMoved = Signal(QPointF)
    wireDragReleased = Signal(QPointF)
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
        
        # Execution State
        self.execution_state = "IDLE" # IDLE, QUEUED, RUNNING
        self.run_timer = QTimer()
        self.run_timer.timeout.connect(self.on_timer_tick)
        self.run_start_time = None
        self.elapsed_ms = 0
        self.spinner_angle = 0
        
        self.provider_status = ProviderStatusManager.instance()
        self.provider_status.status_changed.connect(self.on_provider_status_changed)
        
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
        """Calculate minimum width based on footer content."""
        # Footer contains: [Margin] [Run Button] [Gap] [Context Payload] [Gap] [Tokens] [Margin]
        # Run Button: 80px
        # Margin: 15px
        # Gap: 20px
        
        # Estimates for text:
        # Context Payload: approx 150-180px including label and meter
        # Tokens: approx 80px
        
        # Run(80) + Gap(15) + Payload(160) + Gap(15) + Tokens(70) + Margin(15) * 2 = ~370
        return 380

    def update_layout(self):
        """Update widget positions and sizes based on current node dimensions."""
        # Constrain width
        min_w = self.get_min_width()
        if self.width < min_w:
            self.width = min_w
            
        header_height = 75
        footer_height = 50 
        margin = 15
        gap = 10
        
        # Available vertical space for text fields
        available_text_height = self.height - header_height - footer_height - margin
        
        # Enforce minimums for prompt and output
        # If available < min_prompt + min_output, resize node height
        min_total_text = self.MIN_PROMPT_HEIGHT + self.MIN_OUTPUT_HEIGHT + gap
        if available_text_height < min_total_text:
            self.height = header_height + footer_height + margin + min_total_text
            available_text_height = min_total_text
            
        # 1. Prompt
        # Use stored prompt height, constrained
        prompt_h = max(self.MIN_PROMPT_HEIGHT, self.node.prompt_height)
        
        # If prompt takes too much space, cap it so output has at least min height
        max_prompt_h = available_text_height - self.MIN_OUTPUT_HEIGHT - gap
        if prompt_h > max_prompt_h:
            prompt_h = max_prompt_h
            
        # 2. Output
        # Takes all remaining space
        output_h = available_text_height - prompt_h - gap
        
        # Position prompt editor
        self.proxy_prompt.setPos(margin, header_height)
        self.proxy_prompt.resize(self.width - 2 * margin, prompt_h)
        
        # Position output editor
        output_y = header_height + prompt_h + gap
        self.proxy_output.setPos(margin, output_y)
        self.proxy_output.resize(self.width - 2 * margin, output_h)
        
        # Position run button (Footer Left)
        btn_y = self.height - footer_height + 10 # 10px padding within footer
        self.proxy_btn.setPos(margin, btn_y)
        self.proxy_btn.resize(Sizing.BUTTON_WIDTH, Sizing.BUTTON_HEIGHT)

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
        """Get the rectangle for the corner resize handle."""
        return QRectF(
            self.width - self.RESIZE_HANDLE_SIZE,
            self.height - self.RESIZE_HANDLE_SIZE,
            self.RESIZE_HANDLE_SIZE,
            self.RESIZE_HANDLE_SIZE
        )
    
    def get_separator_rect(self):
        """Get the rectangle for the text field separator."""
        separator_y = 75 + self.node.prompt_height # Header + Prompt
        # Add half of gap (gap is 10)
        return QRectF(15, separator_y, self.width - 30, 10)
    
    def get_cursor_for_position(self, pos):
        """Get appropriate cursor for position."""
        if self.get_resize_handle_rect().contains(pos):
            return Qt.SizeFDiagCursor
        elif self.get_separator_rect().contains(pos):
            return Qt.SizeVerCursor
        return Qt.ArrowCursor

    def get_model_label_rect(self):
        font = QFont("Segoe UI", 9)
        metrics = QFontMetrics(font)
        
        model_text = self.resolve_provider_model_text()

        w = metrics.horizontalAdvance(model_text)
        h = metrics.height()
        return QRectF(15, 38, self.width - 30, h)

    # --- Helpers ---
    def resolve_provider_model_text(self):
        config_provider = self.node.config.provider or "Default"
        config_model = self.node.config.model or ""
        
        display_provider = config_provider
        display_model = config_model
        
        if config_provider == "Default":
            settings = SettingsManager()
            if not config_model:
                display_provider = settings.value("default_provider", "Ollama")
                if display_provider == "OpenAI":
                    display_model = settings.value("openai_model", "gpt-4o")
                elif display_provider == "Gemini":
                    display_model = settings.value("gemini_model", "gemini-1.5-flash")
                else:
                    display_model = settings.value("ollama_model", "llama3")
            else:
                if config_model.startswith("gpt") or config_model.startswith("o1"):
                    display_provider = "OpenAI"
                elif config_model.startswith("gemini"):
                    display_provider = "Gemini"
                else:
                    display_provider = "Ollama"
                display_model = config_model
        
        return f"{display_provider}/{display_model}" if display_model else display_provider

    def resolve_effective_provider(self):
        """Helper to determine the actual provider in use (resolving Default)."""
        config_provider = self.node.config.provider or "Default"
        if config_provider != "Default":
            return config_provider
            
        settings = SettingsManager()
        # Heuristic resolution based on global default or model prefix
        # This mirrors resolve_provider_model_text logic but returns jus provider name
        config_model = self.node.config.model or ""
        if not config_model:
             return settings.value("default_provider", "Ollama")
             
        if config_model.startswith("gpt") or config_model.startswith("o1"):
            return "OpenAI"
        elif config_model.startswith("gemini"):
            return "Gemini"
        else:
            return "Ollama"

    def on_provider_status_changed(self, provider, is_active):
        # Check if this node uses the updated provider
        effective = self.resolve_effective_provider()
        if effective == provider:
            self.update()

    # --- Metrics ---
    
    # ... (existing methods) ...

    def paint(self, painter: QPainter, option, widget):
        # ... (lines 1-597)
        
        painter.drawText(15, 50, elided_model)
        
        # 3.b Status Check (Red Text Overlay if failed)
        effective = self.resolve_effective_provider()
        status = self.provider_status.get_status(effective)
        if status is False: # Explicitly False means checked and failed
             painter.setPen(QPen(QColor(Colors.ERROR)))
             painter.drawText(15, 50, elided_model) # Redraw over with red? Or just draw red initially
             # Better: Reset pen before drawing text above if status is False
             
        painter.setPen(QPen(QColor(Colors.TEXT_TERTIARY)))
        # ...
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

    def paint(self, painter: QPainter, option, widget):
        rect = self.boundingRect()
        painter.setRenderHint(QPainter.Antialiasing)
        
        # --- 1. Background & Selection Highlight ---
        if self.isSelected():
            painter.setPen(QPen(QColor(Colors.SELECTION), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, 8, 8)
        
        if self.node.is_dirty:
            painter.setPen(QPen(QColor(Colors.DIRTY), 2, Qt.DashLine))
        else:
            painter.setPen(QPen(QColor(Colors.BORDER_DEFAULT), 1))
            
        painter.setBrush(QBrush(QColor(Colors.NODE_BG)))
        painter.drawRoundedRect(rect, 8, 8)
        
        # --- 2. Header ---
        header_path = QPainterPath()
        # Header top part height is roughly half the total header height (75)
        header_split = 36 # height for the title part
        header_path.moveTo(0, header_split)
        header_path.lineTo(0, 8)
        header_path.quadTo(0, 0, 8, 0)
        header_path.lineTo(self.width - 8, 0)
        header_path.quadTo(self.width, 0, self.width, 8)
        header_path.lineTo(self.width, header_split)
        header_path.closeSubpath()
        
        # Highlight header if active/selected
        if self.isSelected():
            header_color = QColor(Colors.NODE_HEADER_SELECTED) 
        else:
            header_color = QColor(Colors.NODE_HEADER_DIRTY) if self.node.is_dirty else QColor(Colors.NODE_HEADER)
            
        painter.fillPath(header_path, header_color)
        
        # Status Dot
        dot_color = QColor(Colors.DIRTY) if self.node.is_dirty else QColor(Colors.SUCCESS)
        painter.setBrush(QBrush(dot_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(15, 12, 12, 12)
        
        # Title (Node Name)
        painter.setPen(QPen(QColor(Colors.TEXT_PRIMARY)))
        painter.setFont(QFont(Typography.FAMILY_PRIMARY, Typography.SIZE_NORMAL, QFont.Bold))
        
        display_name = self.node.name or self.node.id
        header_text_width = self.width - 60
        metrics = painter.fontMetrics()
        elided_name = metrics.elidedText(display_name, Qt.ElideRight, header_text_width)
        
        if not self.proxy_name.isVisible():
            painter.drawText(38, 24, elided_name)
        
        # 3. Header Info Labels
        
        # Check Status
        effective = self.resolve_effective_provider()
        status = self.provider_status.get_status(effective)
        
        text_color = QColor(Colors.TEXT_SECONDARY)
        if status is False:
             text_color = QColor(Colors.ERROR)
             
        painter.setPen(QPen(text_color))
        painter.setFont(QFont(Typography.FAMILY_PRIMARY, Typography.SIZE_NORMAL))
        
        model_text = self.resolve_provider_model_text()
        metrics_model = painter.fontMetrics()
        text_width = self.width - 30
        elided_model = metrics_model.elidedText(model_text, Qt.ElideRight, text_width)
        
        painter.drawText(15, 50, elided_model)

        painter.setPen(QPen(QColor(Colors.TEXT_TERTIARY)))
        painter.setFont(QFont(Typography.FAMILY_PRIMARY, Typography.SIZE_SMALL))
        painter.drawText(15, 68, f"Trace Depth: {self.node.config.trace_depth} (Auto)")

        # 4. Footer Metrics (New Layout)
        footer_top = self.height - Sizing.FOOTER_HEIGHT
        
        # 4.a Context Payload Meter
        current = getattr(self, '_payload_chars', 0)
        limit = getattr(self, '_max_chars', 16000 * 4) 
        
        ratio = min(current / max(limit, 1), 1.0)
        
        meter_x = 110
        meter_y = footer_top + 10
        meter_width = Sizing.METER_WIDTH
        meter_height = Sizing.METER_HEIGHT
        
        # Background
        painter.setBrush(QBrush(QColor(Colors.METER_BG)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(meter_x, meter_y, meter_width, meter_height, 4, 4)
        
        # Fill
        meter_color = QColor(Colors.METER_LOW)
        if ratio > 0.8: meter_color = QColor(Colors.METER_MEDIUM)
        if ratio > 0.95: meter_color = QColor(Colors.METER_HIGH)
        
        fill_width = int(meter_width * ratio)
        if fill_width > 0:
            painter.setBrush(QBrush(meter_color))
            painter.drawRoundedRect(meter_x, meter_y, fill_width, meter_height, 4, 4)
            
        # Label above meter
        painter.setPen(QPen(QColor(Colors.TEXT_DISABLED)))
        painter.setFont(QFont(Typography.FAMILY_PRIMARY, Typography.SIZE_SMALL))
        painter.drawText(meter_x, meter_y - 3, "Context Payload")
        
        # Numbers below meter
        tok_curr = current // 4
        tok_limit = limit // 4
        def fmt_k(v): return f"{v/1000:.1f}k" if v > 1000 else str(v)
        payload_text = f"{fmt_k(tok_curr)} / {fmt_k(tok_limit)}"
        
        painter.setPen(QPen(QColor(Colors.TEXT_TERTIARY)))
        painter.setFont(QFont(Typography.FAMILY_PRIMARY, Typography.SIZE_SMALL))
        painter.drawText(meter_x, meter_y + 18, payload_text)
        
        # 4.a1 Execution Status (Next to Run Button) - REMOVED (Moved to Center Overlay)

        # 4.b Tokens
        tokens_x = meter_x + meter_width + 20
        
        out_len = len(self.node.cached_output or "") if self.node.cached_output else 0
        est_tokens = out_len // 4
        
        painter.setPen(QPen(QColor(Colors.TEXT_DISABLED)))
        painter.setFont(QFont(Typography.FAMILY_PRIMARY, Typography.SIZE_SMALL))
        painter.drawText(tokens_x, meter_y - 3, "Output Tokens")
        
        painter.setPen(QPen(QColor(Colors.TEXT_TERTIARY)))
        painter.setFont(QFont(Typography.FAMILY_PRIMARY, Typography.SIZE_SMALL))
        painter.drawText(tokens_x, meter_y + 18, f"{est_tokens}")

        # 5. Ports
        out_port_y = Sizing.HEADER_HEIGHT
        port_size = Sizing.PORT_SIZE
        port_height = Sizing.PORT_HEIGHT
        
        painter.setBrush(QBrush(QColor(Colors.PORT_DEFAULT)))
        painter.setPen(QPen(QColor(Colors.PORT_BORDER)))
        painter.drawRect(self.width - port_size, out_port_y, port_size, port_height)
        
        y_offset = Sizing.HEADER_HEIGHT
        for _ in self.node.input_links:
            painter.setBrush(QBrush(QColor(Colors.PORT_ACTIVE))) 
            painter.drawRect(0, y_offset, port_size, port_height)
            y_offset += 24
        painter.setBrush(QBrush(QColor(Colors.PORT_ADD)))
        painter.drawRect(0, y_offset, port_size, port_height)
        painter.setPen(QPen(QColor(Colors.TEXT_SECONDARY)))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(-12, y_offset + 12, "+")
        
        # 6. Resize Handle
        handle_rect = self.get_resize_handle_rect()
        painter.setPen(QPen(QColor(Colors.TEXT_DISABLED), 1))
        painter.setBrush(Qt.NoBrush)
        for i in range(3):
            offset = i * 4
            painter.drawLine(
                int(handle_rect.left() + offset + 2),
                int(handle_rect.bottom() - 2),
                int(handle_rect.right() - 2),
                int(handle_rect.top() + offset + 2)
            )

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
            super().mouseDoubleClickEvent(event)

    def hoverMoveEvent(self, event):
        pos = event.pos()
        if self.get_resize_handle_rect().contains(pos):
            self.setCursor(Qt.SizeFDiagCursor)
        elif self.get_separator_rect().contains(pos):
            self.setCursor(Qt.SizeVerCursor)
        elif self.get_model_label_rect().contains(pos):
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)
    
    def mousePressEvent(self, event):
        pos = event.pos()
        
        if self.get_resize_handle_rect().contains(pos):
            self.is_resizing = True
            self.resize_start_pos = event.pos()
            self.resize_start_size = (self.width, self.height)
            event.accept()
            return
        
        self.move_start_scene_pos = self.scenePos()
        
        if self.get_separator_rect().contains(pos):
            self.is_resizing_separator = True
            self.resize_start_pos = event.pos()
            # store start height of prompt
            self.resize_start_heights = (self.node.prompt_height, 0) 
            event.accept()
            return

        if self.get_model_label_rect().contains(pos):
            current_provider = self.node.config.provider or "Default"
            current_model = self.node.config.model or ""
            
            view = self.scene().views()[0] if self.scene() and self.scene().views() else None
            
            dlg = NodeSettingsDialog(current_provider, current_model, parent=view)
            if dlg.exec():
                self.node.config.provider = dlg.selected_provider
                self.node.config.model = dlg.selected_model
                self.node.is_dirty = True
                self.update() 
            
            event.accept()
            return
        
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
            delta = event.pos() - self.resize_start_pos
            min_w = self.get_min_width()
            new_width = max(min_w, min(self.MAX_WIDTH, self.resize_start_size[0] + delta.x()))
            new_height = max(self.MIN_HEIGHT, min(self.MAX_HEIGHT, self.resize_start_size[1] + delta.y()))
            
            self.width = new_width
            self.height = new_height
            self.update_layout()
            
            self.positionChanged.emit(self.node.id)
            event.accept()
            return
        
        if self.is_resizing_separator:
            delta_y = event.pos().y() - self.resize_start_pos.y()
            # Resizing separator changes prompt height
            # But must ensure prompt_height >= min
            # AND output_height >= min 
            
            new_prompt_h = self.resize_start_heights[0] + delta_y
            
            # Check Constraints
            header_height = 75
            footer_height = 50
            margin = 15
            gap = 10
            
            available_text_height = self.height - header_height - footer_height - margin
            
            # 1. Min Prompt
            new_prompt_h = max(self.MIN_PROMPT_HEIGHT, new_prompt_h)
            
            # 2. Min Output (Prompt can't grow so big that output < min)
            max_prompt_h = available_text_height - self.MIN_OUTPUT_HEIGHT - gap
            new_prompt_h = min(new_prompt_h, max_prompt_h)
            
            self.node.prompt_height = int(new_prompt_h)
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
            
            if self.scene():
                self.scene().update()

    def check_input_drop(self, scene_pos: QPointF) -> bool:
        local_pos = self.mapFromScene(scene_pos)
        y_offset = 75 + len(self.node.input_links) * 24
        placeholder_rect = QRectF(-25, y_offset - 10, 50, 40)
        return placeholder_rect.contains(local_pos)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.node.pos_x = value.x()
            self.node.pos_y = value.y()
            self.positionChanged.emit(self.node.id)
        return super().itemChange(change, value)
