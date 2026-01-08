
from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPainterPath, QPen, QColor, QPainter
from PySide6.QtCore import Qt, QPointF

class WireItem(QGraphicsPathItem):
    def __init__(self, source_pos: QPointF, target_pos: QPointF):
        super().__init__()
        self.source_pos = source_pos
        self.target_pos = target_pos
        self.setZValue(-1) # Behind nodes
        
        pen = QPen(QColor("#888"), 2)
        self.setPen(pen)
        self.update_path()

    def update_positions(self, source_pos, target_pos):
        self.source_pos = source_pos
        self.target_pos = target_pos
        self.update_path()

    def update_path(self):
        path = QPainterPath()
        path.moveTo(self.source_pos)
        
        dx = self.target_pos.x() - self.source_pos.x()
        
        # Bezier control points logic
        # Improve visual curve
        ctrl_dist = abs(dx) * 0.5 
        ctrl_dist = max(ctrl_dist, 50)
        
        ctrl1 = QPointF(self.source_pos.x() + ctrl_dist, self.source_pos.y())
        ctrl2 = QPointF(self.target_pos.x() - ctrl_dist, self.target_pos.y())
        
        path.cubicTo(ctrl1, ctrl2, self.target_pos)
        self.setPath(path)
        
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        super().paint(painter, option, widget)
