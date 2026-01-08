
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView
from PySide6.QtCore import Qt, QRectF, QLineF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

class CanvasScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QBrush(QColor("#161616")))
        self.setSceneRect(-5000, -5000, 10000, 10000)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """
        Draws a grid background.
        """
        super().drawBackground(painter, rect)
        
        # Grid settings
        grid_size = 40
        grid_color = QColor("#333")
        grid_pen = QPen(grid_color)
        grid_pen.setWidth(1)
        
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        
        # Draw vertical lines
        lines = []
        x = left
        while x < rect.right():
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
            x += grid_size
            
        # Draw horizontal lines
        y = top
        while y < rect.bottom():
            lines.append(QLineF(rect.left(), y, rect.right(), y))
            y += grid_size
            
        painter.setPen(grid_pen)
        painter.drawLines(lines)

class CanvasView(QGraphicsView):
    def __init__(self, scene: CanvasScene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.RubberBandDrag) 
        # RubberBandDrag allows selection. To Pan, we might need a modifier or explicit mode.
        # Common pattern: Middle click pan, or Space+Drag.
        # For simplicity MVP: Right click pan implemented in events?
        # Or standard ScrollHandDrag if selection isn't primary interaction mode yet.
        # Let's use RubberBandDrag by default (Selection) and Ctrl+Drag or Middle Drag for Pan.

    def wheelEvent(self, event):
        """Zoom with mouse wheel."""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
            
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            original_event = event.pos() # Dummy logic, ScrollHandDrag handles subsequent moves
            # But we need to forward/synthesize the press for the drag to start?
            # Actually, switching mode usually requires a fresh press.
            # Custom logic:
            self._pan_start = event.pos()
            self._panning = True
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if hasattr(self, '_panning') and self._panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if hasattr(self, '_panning') and self._panning:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            self.setDragMode(QGraphicsView.RubberBandDrag)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    def contextMenuEvent(self, event):
        # We only show the canvas menu if we didn't hit an item
        if self.itemAt(event.pos()):
            super().contextMenuEvent(event)
            return
            
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        window = self.window()
        menu = QMenu()
        
        add_act = QAction("Add Node", menu)
        # mapToScene to get correct placement
        scene_pos = self.mapToScene(event.pos())
        add_act.triggered.connect(lambda: window.add_node_at(scene_pos))
        menu.addAction(add_act)
        
        paste_act = QAction("Paste", menu)
        paste_act.setEnabled(bool(window.clipboard))
        paste_act.triggered.connect(window.paste_selection)
        menu.addAction(paste_act)
        
        menu.exec(event.globalPos())
        event.accept()
