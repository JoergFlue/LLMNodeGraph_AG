"""
NodeLayoutManager - Handles the layout calculations for NodeItem.
"""

from PySide6.QtCore import QRectF
from .theme import Sizing, Spacing

class NodeLayoutManager:
    """
    Manages the layout and positioning of elements within a NodeItem.
    """
    
    def __init__(self, node_item):
        self.item = node_item
        
    def get_min_width(self) -> int:
        """Calculate minimum width based on footer content."""
        # Footer components approx width: 
        # Run(80) + Gap(15) + Meter(120) + Gap(15) + Tokens(70) + Margin(15)*2 = ~345
        # Enforce theme minimum
        return max(Sizing.NODE_MIN_WIDTH, 380)

    def update_structure(self):
        """Update widget positions and sizes based on current node dimensions."""
        
        # 1. Constrain Width
        min_w = self.get_min_width()
        if self.item.width < min_w:
            self.item.width = min_w
            
        header_h = Sizing.HEADER_HEIGHT
        footer_h = Sizing.FOOTER_HEIGHT
        margin = Spacing.MARGIN_LARGE
        gap = Spacing.GAP_MEDIUM
        
        # 2. Calculate Heights
        available_text_height = self.item.height - header_h - footer_h - margin
        
        min_total_text = Sizing.MIN_PROMPT_HEIGHT + Sizing.MIN_OUTPUT_HEIGHT + gap
        
        # Enforce minimum height
        if available_text_height < min_total_text:
            self.item.height = header_h + footer_h + margin + min_total_text
            available_text_height = min_total_text
            
        # Distribute height between Prompt and Output
        prompt_h = max(Sizing.MIN_PROMPT_HEIGHT, self.item.node.prompt_height)
        max_prompt_h = available_text_height - Sizing.MIN_OUTPUT_HEIGHT - gap
        
        if prompt_h > max_prompt_h:
            prompt_h = max_prompt_h
            
        output_h = available_text_height - prompt_h - gap
        
        # 3. Position Widgets (Proxies)
        
        # Prompt Editor
        self.item.proxy_prompt.setPos(margin, header_h)
        self.item.proxy_prompt.resize(self.item.width - 2 * margin, prompt_h)
        
        # Output Editor
        output_y = header_h + prompt_h + gap
        self.item.proxy_output.setPos(margin, output_y)
        self.item.proxy_output.resize(self.item.width - 2 * margin, output_h)
        
        # Run Button (Footer Left)
        btn_y = self.item.height - footer_h + Spacing.MARGIN_MEDIUM
        self.item.proxy_btn.setPos(margin, btn_y)
        self.item.proxy_btn.resize(Sizing.BUTTON_WIDTH, Sizing.BUTTON_HEIGHT)

        # Name Editor (Header)
        # Using theme constants for header text position
        from .theme import Sizing as Sz # Re-import to ensure fresh values if needed
        name_x = Sz.HEADER_TEXT_X
        # Name edit is slightly higher than text draw position for alignment
        name_y = 5 
        
        self.item.proxy_name.setPos(name_x, name_y)
        self.item.proxy_name.resize(self.item.width - 50, 26)
        
        # 4. Update Node Data
        self.item.node.width = self.item.width
        self.item.node.height = self.item.height
        self.item.node.prompt_height = prompt_h
        self.item.node.output_height = output_h
        
    def get_resize_handle_rect(self) -> QRectF:
        """Get the rectangle for the corner resize handle."""
        size = Sizing.RESIZE_HANDLE_SIZE
        return QRectF(
            self.item.width - size,
            self.item.height - size,
            size,
            size
        )
    
    def get_separator_rect(self) -> QRectF:
        """Get the rectangle for the text field separator."""
        # Header + Prompt Height
        separator_y = Sizing.HEADER_HEIGHT + self.item.node.prompt_height
        return QRectF(15, separator_y, self.item.width - 30, Spacing.GAP_MEDIUM)
    
    def get_model_label_rect(self) -> QRectF:
        """Get the rectangle for the provider/model label."""
        # This allows for hit-testing if we want to make the label clickable
        # Using roughly the area where text is drawn
        return QRectF(Sizing.PROVIDER_LABEL_X, 38, self.item.width - 30, 20)

    def get_output_port_rect(self) -> QRectF:
        """Get the rectangle for the output port."""
        size = Sizing.PORT_SIZE
        h = Sizing.PORT_HEIGHT
        return QRectF(self.item.width - size, Sizing.HEADER_HEIGHT, size, h)
