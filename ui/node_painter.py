"""
NodePainter - Handles the painting logic for NodeItem.
"""

from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont, QFontMetrics
from PySide6.QtCore import Qt, QRectF
from .theme import Colors, Sizing, Spacing, Typography, Styles

class NodePainter:
    """
    Handles all drawing operations for a NodeItem.
    Stateless rendering based on the item's properties.
    """
    
    @staticmethod
    def paint(painter: QPainter, item, option, widget):
        """Main paint method called by NodeItem."""
        rect = item.boundingRect()
        painter.setRenderHint(QPainter.Antialiasing)
        
        NodePainter._draw_background(painter, item, rect)
        NodePainter._draw_header(painter, item)
        NodePainter._draw_footer(painter, item)
        NodePainter._draw_ports(painter, item)
        NodePainter._draw_resize_handle(painter, item)
        
    @staticmethod
    def _draw_background(painter, item, rect):
        # Selection Highlight (Border)
        if item.isSelected():
            painter.setPen(QPen(QColor(Colors.SELECTION), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, 8, 8)
        
        # Border
        if item.node.is_dirty:
            painter.setPen(QPen(QColor(Colors.DIRTY), 2, Qt.DashLine))
        else:
            painter.setPen(QPen(QColor(Colors.BORDER_DEFAULT), 1))
            
        # Fill
        painter.setBrush(QBrush(QColor(Colors.NODE_BG)))
        painter.drawRoundedRect(rect, 8, 8)

    @staticmethod
    def _draw_header(painter, item):
        width = item.width
        
        # Header Background Shape
        header_path = QPainterPath()
        header_split = 36 # Title height
        header_path.moveTo(0, header_split)
        header_path.lineTo(0, 8)
        header_path.quadTo(0, 0, 8, 0)
        header_path.lineTo(width - 8, 0)
        header_path.quadTo(width, 0, width, 8)
        header_path.lineTo(width, header_split)
        
        # Header Color
        if item.isSelected():
            header_color = QColor(Colors.NODE_HEADER_SELECTED)
        else:
            header_color = QColor(Colors.NODE_HEADER_DIRTY) if item.node.is_dirty else QColor(Colors.NODE_HEADER)
            
        painter.fillPath(header_path, header_color)
        
        # Status Dot
        dot_color = QColor(Colors.DIRTY) if item.node.is_dirty else QColor(Colors.SUCCESS)
        painter.setBrush(QBrush(dot_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(15, 12, 12, 12)
        
        # Title (Node Name)
        painter.setPen(QPen(QColor(Colors.TEXT_PRIMARY)))
        painter.setFont(QFont(Typography.FAMILY_PRIMARY, Typography.SIZE_NORMAL, QFont.Bold))
        
        display_name = item.node.name or item.node.id
        header_text_width = width - 60
        max_chars = int(header_text_width / 7) # Approx char width
        if len(display_name) > max_chars:
            display_name = display_name[:max_chars] + "..."
            
        if not item.proxy_name.isVisible():
            painter.drawText(38, 24, display_name)
            
        # Provider Label
        effective_provider = item.resolve_effective_provider()
        status = item.provider_status.get_status(effective_provider)
        
        text_color = QColor(Colors.TEXT_SECONDARY)
        if status is False:
             text_color = QColor(Colors.ERROR)
             
        painter.setPen(QPen(text_color))
        painter.setFont(QFont(Typography.FAMILY_PRIMARY, Typography.SIZE_NORMAL))
        
        model_text = item.resolve_provider_model_text()
        # manual elision
        if len(model_text) > 40: model_text = model_text[:37] + "..."
        
        painter.drawText(15, 50, model_text)
        
        # Trace Depth Label
        painter.setPen(QPen(QColor(Colors.TEXT_TERTIARY)))
        painter.setFont(QFont(Typography.FAMILY_PRIMARY, Typography.SIZE_SMALL))
        painter.drawText(15, 68, f"Trace Depth: {item.node.config.trace_depth} (Auto)")

    @staticmethod
    def _draw_footer(painter, item):
        footer_top = item.height - Sizing.FOOTER_HEIGHT
        
        # Context Payload Meter
        current = getattr(item, '_payload_chars', 0)
        limit = getattr(item, '_max_chars', 16000 * 4) 
        
        ratio = min(current / max(limit, 1), 1.0)
        
        meter_x = 110
        meter_y = footer_top + 10
        meter_w = Sizing.METER_WIDTH
        meter_h = Sizing.METER_HEIGHT
        
        # Meter Background
        painter.setBrush(QBrush(QColor(Colors.METER_BG)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(meter_x, meter_y, meter_w, meter_h, 4, 4)
        
        # Meter Fill
        meter_color = QColor(Colors.METER_LOW)
        if ratio > 0.8: meter_color = QColor(Colors.METER_MEDIUM)
        if ratio > 0.95: meter_color = QColor(Colors.METER_HIGH)
        
        fill_w = int(meter_w * ratio)
        if fill_w > 0:
            painter.setBrush(QBrush(meter_color))
            painter.drawRoundedRect(meter_x, meter_y, fill_w, meter_h, 4, 4)
            
        # Labels
        painter.setPen(QPen(QColor(Colors.TEXT_DISABLED)))
        painter.setFont(QFont(Typography.FAMILY_PRIMARY, Typography.SIZE_SMALL))
        painter.drawText(meter_x, meter_y - 3, "Context Payload")
        
        # Numbers
        tok_curr = current // 4
        tok_limit = limit // 4
        def fmt_k(v): return f"{v/1000:.1f}k" if v > 1000 else str(v)
        payload_text = f"{fmt_k(tok_curr)} / {fmt_k(tok_limit)}"
        
        painter.setPen(QPen(QColor(Colors.TEXT_TERTIARY)))
        painter.drawText(meter_x, meter_y + 18, payload_text)
        
        # Output Tokens estimate
        tokens_x = meter_x + meter_w + 20
        out_len = len(item.node.cached_output or "") if item.node.cached_output else 0
        est_tokens = out_len // 4
        
        painter.setPen(QPen(QColor(Colors.TEXT_DISABLED)))
        painter.drawText(tokens_x, meter_y - 3, "Output Tokens")
        
        painter.setPen(QPen(QColor(Colors.TEXT_TERTIARY)))
        painter.drawText(tokens_x, meter_y + 18, f"{est_tokens}")

    @staticmethod
    def _draw_ports(painter, item):
        out_port_y = Sizing.HEADER_HEIGHT
        size = Sizing.PORT_SIZE
        h = Sizing.PORT_HEIGHT
        
        # Output Port (Right)
        painter.setBrush(QBrush(QColor(Colors.PORT_DEFAULT)))
        painter.setPen(QPen(QColor(Colors.PORT_BORDER)))
        painter.drawRect(item.width - size, out_port_y, size, h)
        
        # Input Ports (Left)
        y_offset = Sizing.HEADER_HEIGHT
        for _ in item.node.input_links:
            painter.setBrush(QBrush(QColor(Colors.PORT_ACTIVE))) 
            painter.drawRect(0, y_offset, size, h)
            y_offset += 24
            
            
        # Add Port Button area (also acts as the empty input slot for dragging)
        painter.setBrush(QBrush(QColor(Colors.PORT_ADD)))
        painter.drawRect(0, y_offset, size, h)
        painter.setPen(QPen(QColor(Colors.TEXT_SECONDARY)))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(-12, y_offset + 12, "+")

    @staticmethod
    def _draw_resize_handle(painter, item):
        handle_rect = item.get_resize_handle_rect()
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
