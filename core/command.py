"""
Commands - Action implementations for the Command Pattern (Undo/Redo).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from core.graph import Graph
from core.node import Node, Link

class Command(ABC):
    """Base abstract class for all commands."""
    
    @abstractmethod
    def execute(self) -> None:
        """Perform the operation."""
        pass
    
    @abstractmethod
    def undo(self) -> None:
        """Reverse the operation."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return a human-readable description of the command."""
        pass

class AddNodeCommand(Command):
    """Command to add a node to the graph."""
    
    def __init__(self, graph: Graph, node: Node):
        """
        Initialize command.
        
        Args:
            graph (Graph): The graph instance.
            node (Node): The node to add.
        """
        self.graph = graph
        self.node = node
        
    def execute(self) -> None:
        """Execute the command."""
        self.graph.add_node(self.node)
        
    def undo(self) -> None:
        """Undo the command."""
        self.graph.remove_node(self.node.id)
        
    def get_description(self) -> str:
        """Get command description."""
        return f"Add node {self.node.id}"

class DeleteNodesCommand(Command):
    """Command to delete one or more nodes and their associated links."""
    
    def __init__(self, graph: Graph, nodes: List[Node], links: List[Link]):
        """
        Initialize command.
        
        Args:
            graph (Graph): The graph instance.
            nodes (List[Node]): Nodes to delete.
            links (List[Link]): Links connected to these nodes (to restore on undo).
        """
        self.graph = graph
        self.nodes = nodes
        self.links = links
        
    def execute(self) -> None:
        """Execute the command."""
        for node in self.nodes:
            self.graph.remove_node(node.id)
        # Note: Graph.remove_node already removes links, but for redo reliability
        # we might want to ensure links are cleared if execute is called multiple times.
        
    def undo(self) -> None:
        """Undo the command."""
        # Restore nodes
        for node in self.nodes:
            self.graph.add_node(node)
        # Restore links
        for link in self.links:
            self.graph.links[link.id] = link
            if link.target_id in self.graph.nodes:
                target_node = self.graph.nodes[link.target_id]
                if link.id not in target_node.input_links:
                    target_node.input_links.append(link.id)
        
    def get_description(self) -> str:
        """Get command description."""
        if len(self.nodes) == 1:
            return f"Delete node {self.nodes[0].id}"
        return f"Delete {len(self.nodes)} nodes"

class MoveNodesCommand(Command):
    """Command to move one or more nodes."""
    
    def __init__(self, graph: Graph, move_data: List[Tuple[str, float, float, float, float]]):
        """
        Initialize command.
        
        Args:
            graph (Graph): The graph instance.
            move_data: List of (node_id, old_x, old_y, new_x, new_y).
        """
        self.graph = graph
        self.move_data = move_data
        
    def execute(self) -> None:
        """Execute the command."""
        for node_id, _, _, new_x, new_y in self.move_data:
            if node_id in self.graph.nodes:
                node = self.graph.nodes[node_id]
                node.pos_x = new_x
                node.pos_y = new_y
                
    def undo(self) -> None:
        """Undo the command."""
        for node_id, old_x, old_y, _, _ in self.move_data:
            if node_id in self.graph.nodes:
                node = self.graph.nodes[node_id]
                node.pos_x = old_x
                node.pos_y = old_y
                
    def get_description(self) -> str:
        """Get command description."""
        if len(self.move_data) == 1:
            return f"Move node {self.move_data[0][0]}"
        return f"Move {len(self.move_data)} nodes"

class AddLinkCommand(Command):
    """Command to add a link between two nodes."""
    
    def __init__(self, graph: Graph, link: Link):
        """
        Initialize command.
        
        Args:
            graph (Graph): The graph instance.
            link (Link): The link to add.
        """
        self.graph = graph
        self.link = link
        
    def execute(self) -> None:
        """Execute the command."""
        self.graph.links[self.link.id] = self.link
        if self.link.target_id in self.graph.nodes:
            target_node = self.graph.nodes[self.link.target_id]
            if self.link.id not in target_node.input_links:
                target_node.input_links.append(self.link.id)
            self.graph.mark_dirty(self.link.target_id)
            
    def undo(self) -> None:
        """Undo the command."""
        self.graph.remove_link(self.link.id)
        
    def get_description(self) -> str:
        """Get command description."""
        return f"Connect {self.link.source_id} to {self.link.target_id}"

class DeleteLinkCommand(Command):
    """Command to delete a link."""
    
    def __init__(self, graph: Graph, link: Link):
        """
        Initialize command.
        
        Args:
            graph (Graph): The graph instance.
            link (Link): The link to delete.
        """
        self.graph = graph
        self.link = link
        
    def execute(self) -> None:
        """Execute the command by removing the link from the graph."""
        self.graph.remove_link(self.link.id)
        
    def undo(self) -> None:
        """Undo the command by adding the link back to the graph."""
        self.graph.links[self.link.id] = self.link
        if self.link.target_id in self.graph.nodes:
            target_node = self.graph.nodes[self.link.target_id]
            if self.link.id not in target_node.input_links:
                target_node.input_links.append(self.link.id)
            self.graph.mark_dirty(self.link.target_id)
            
    def get_description(self) -> str:
        """Get human-readable description of the command."""
        return f"Delete link {self.link.id}"

class EditPromptCommand(Command):
    """Command to change a node's prompt text."""
    
    def __init__(self, graph: Graph, node_id: str, old_text: str, new_text: str):
        """
        Initialize command.
        
        Args:
            graph (Graph): The graph instance.
            node_id (str): Target node ID.
            old_text (str): Previous prompt text.
            new_text (str): New prompt text.
        """
        self.graph = graph
        self.node_id = node_id
        self.old_text = old_text
        self.new_text = new_text
        
    def execute(self) -> None:
        """Execute the command."""
        if self.node_id in self.graph.nodes:
            self.graph.nodes[self.node_id].prompt = self.new_text
            self.graph.mark_dirty(self.node_id)
            
    def undo(self) -> None:
        """Undo the command."""
        if self.node_id in self.graph.nodes:
            self.graph.nodes[self.node_id].prompt = self.old_text
            self.graph.mark_dirty(self.node_id)
            
    def get_description(self) -> str:
        """Get command description."""
        return f"Edit prompt of {self.node_id}"

class EditOutputCommand(Command):
    """Command to change a node's output text."""
    
    def __init__(self, graph: Graph, node_id: str, old_text: str, new_text: str):
        """
        Initialize command.
        
        Args:
            graph (Graph): The graph instance.
            node_id (str): Target node ID.
            old_text (str): Previous output text.
            new_text (str): New output text.
        """
        self.graph = graph
        self.node_id = node_id
        self.old_text = old_text
        self.new_text = new_text
        
    def execute(self) -> None:
        """Execute the command."""
        if self.node_id in self.graph.nodes:
            self.graph.nodes[self.node_id].cached_output = self.new_text
            # Manually editing output might not need to mark dirty, 
            # but usually it's tied to some state.
            
    def undo(self) -> None:
        """Undo the command."""
        if self.node_id in self.graph.nodes:
            self.graph.nodes[self.node_id].cached_output = self.old_text
            
    def get_description(self) -> str:
        """Get command description."""
        return f"Edit output of {self.node_id}"

class RenameNodeCommand(Command):
    """Command to rename a node."""
    
    def __init__(self, graph: Graph, node_id: str, old_name: str, new_name: str):
        """
        Initialize command.
        
        Args:
            graph (Graph): The graph instance.
            node_id (str): Target node ID.
            old_name (str): Previous name.
            new_name (str): New name.
        """
        self.graph = graph
        self.node_id = node_id
        self.old_name = old_name
        self.new_name = new_name
        
    def execute(self) -> None:
        """Execute the command."""
        if self.node_id in self.graph.nodes:
            self.graph.nodes[self.node_id].name = self.new_name
            
    def undo(self) -> None:
        """Undo the command."""
        if self.node_id in self.graph.nodes:
            self.graph.nodes[self.node_id].name = self.old_name
            
    def get_description(self) -> str:
        """Get command description."""
        return f"Rename node {self.node_id} to '{self.new_name}'"

class PasteNodesAndLinksCommand(Command):
    """Command to paste a group of nodes and links."""
    
    def __init__(self, graph: Graph, nodes: List[Node], links: List[Link]):
        """
        Initialize command.
        
        Args:
            graph (Graph): The graph instance.
            nodes (List[Node]): Nodes to paste.
            links (List[Link]): Links to paste.
        """
        self.graph = graph
        self.nodes = nodes
        self.links = links
        
    def execute(self) -> None:
        """Execute the command."""
        for node in self.nodes:
            self.graph.add_node(node)
        for link in self.links:
            self.graph.links[link.id] = link
            if link.target_id in self.graph.nodes:
                target_node = self.graph.nodes[link.target_id]
                if link.id not in target_node.input_links:
                    target_node.input_links.append(link.id)
                self.graph.mark_dirty(link.target_id)
                
    def undo(self) -> None:
        """Undo the command."""
        for node in self.nodes:
            self.graph.remove_node(node.id)
            
    def get_description(self) -> str:
        """Get command description."""
        return f"Paste {len(self.nodes)} nodes"
