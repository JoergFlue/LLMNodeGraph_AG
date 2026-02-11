"""
Graph - Data structure representing the flow graph.
"""

from typing import Dict, List, Optional
import json
from .node import Node, Link

class Graph:
    """
    Manages the directed graph of Nodes and Links.
    """
    def __init__(self):
        """Initialize an empty graph."""
        self.nodes: Dict[str, Node] = {}
        self.links: Dict[str, Link] = {}
        self.global_token_limit: int = 16384

    def generate_new_node_name(self, base: str = "Chat") -> str:
        """Find the next available Name in the format Base_####."""
        import re
        pattern = re.compile(rf"^{base}_(\d{{4}})$")
        max_idx = 0
        
        for node in self.nodes.values():
            if node.name:
                match = pattern.match(node.name)
                if match:
                    max_idx = max(max_idx, int(match.group(1)))
        
        while True:
            max_idx += 1
            new_name = f"{base}_{max_idx:04d}"
            if self.is_name_unique(new_name):
                return new_name

    def generate_copy_id(self, original_id: str) -> str:
        """Generate a unique UUID copy ID (wrapper for consistency/identity)."""
        import uuid
        return str(uuid.uuid4())

    def add_node(self, node: Node):
        """
        Add a node to the graph.
        
        Args:
            node (Node): The node to add.
        """
        self.nodes[node.id] = node

    def remove_node(self, node_id: str):
        """
        Remove a node and all connected links from the graph.
        
        Args:
            node_id (str): ID of the node to remove.
        """
        if node_id in self.nodes:
            del self.nodes[node_id]
        
        # Remove links connected to this node
        links_to_remove = [
            l_id for l_id, l in self.links.items()
            if l.source_id == node_id or l.target_id == node_id
        ]
        for l_id in links_to_remove:
            self.remove_link(l_id)

    def add_link(self, source_id: str, target_id: str, trigger_dirty: bool = True) -> Link:
        """
        Create and add a link between two nodes.
        
        Args:
            source_id (str): ID of the source node.
            target_id (str): ID of the target node.
            trigger_dirty (bool): Whether to mark the target node as dirty.
            
        Returns:
            Link: The created link.
        """
        # Check for cycles or duplicate links if needed (omitted for MVP speed, but good to have)
        link = Link(source_id=source_id, target_id=target_id)
        self.links[link.id] = link
        
        if target_id in self.nodes:
            self.nodes[target_id].input_links.append(link.id)
            # Mark target as dirty because its inputs changed
            if trigger_dirty:
                self.mark_dirty(target_id)
            
        return link

    def remove_link(self, link_id: str):
        """
        Remove a link from the graph.
        
        Args:
            link_id (str): ID of the link to remove.
        """
        if link_id in self.links:
            link = self.links[link_id]
            target_id = link.target_id
            del self.links[link_id]
            
            if target_id in self.nodes:
                if link_id in self.nodes[target_id].input_links:
                    self.nodes[target_id].input_links.remove(link_id)
                self.mark_dirty(target_id)

    def mark_dirty(self, node_id: str):
        """
        Mark node and its descendants as dirty (needing re-execution).
        
        Args:
            node_id (str): ID of the node starting the dirty chain.
        """
        if node_id not in self.nodes:
            return
            
        node = self.nodes[node_id]
        if node.is_dirty:
            return # Already marked
        
        node.is_dirty = True
        
        # Find children
        children = [
            l.target_id for l in self.links.values()
            if l.source_id == node_id
        ]
        for child_id in children:
            self.mark_dirty(child_id)

    def get_input_nodes(self, node_id: str) -> List[Node]:
        """
        Get the list of nodes connected to the inputs of a given node.
        
        Args:
            node_id (str): ID of the node.
            
        Returns:
            List[Node]: List of input node instances.
        """
        if node_id not in self.nodes:
            return []
        
        input_links_ids = self.nodes[node_id].input_links
        input_nodes = []
        for l_id in input_links_ids:
            if l_id in self.links:
                source_id = self.links[l_id].source_id
                if source_id in self.nodes:
                    input_nodes.append(self.nodes[source_id])
        return input_nodes

    def is_name_unique(self, name: str, exclude_node_id: Optional[str] = None) -> bool:
        """Check if a node name is unique within the graph."""
        if not name:
            return True
        for node in self.nodes.values():
            if node.id == exclude_node_id:
                continue
            if node.name == name:
                return False
        return True

    def merge_graph(self, data: dict, filename: str):
        """Merge another graph into the current one, handling ID and name collisions.
        
        Merged nodes are positioned below and left-aligned with existing nodes.
        """
        import uuid
        import re
        
        id_map = {}
        new_nodes: List[Node] = []
        
        # --- Calculate Positioning Offset ---
        offset_x = 0.0
        offset_y = 0.0
        
        if self.nodes:
            # 1. Bounds of Current Graph
            current_min_x = min(n.pos_x for n in self.nodes.values())
            current_max_y = max(n.pos_y + n.height for n in self.nodes.values())
            
            # 2. Bounds of Incoming Graph
            incoming_nodes_data = data.get("nodes", [])
            if incoming_nodes_data:
                # Need to parse positions first or do it on fly. 
                # Let's peek at them. Default to 0,0 if missing.
                incoming_min_x = min(n.get("pos", [0, 0])[0] for n in incoming_nodes_data)
                incoming_min_y = min(n.get("pos", [0, 0])[1] for n in incoming_nodes_data)
                
                # 3. Calculate Offset
                # Goal: Left align (match min_x) and place below (max_y + padding)
                PADDING = 50.0
                offset_x = current_min_x - incoming_min_x
                offset_y = current_max_y + PADDING - incoming_min_y
        
        # 1. Process Nodes
        for node_data in data.get("nodes", []):
            original_id = node_data.get("id")
            node = Node.from_dict(node_data)
            
            # Apply Position Offset
            node.pos_x += offset_x
            node.pos_y += offset_y
            
            # ID Collision Handling
            if node.id in self.nodes:
                new_id = str(uuid.uuid4())
                id_map[original_id] = new_id
                node.id = new_id
            else:
                id_map[original_id] = node.id
            
            # Name Collision Handling
            if node.name and not self.is_name_unique(node.name):
                base_name = node.name
                # Rule: handle collisions by appending "_[filename]"
                suggested_name = f"{base_name}_{filename}"
                
                # If name already reaches character length limit or still collides
                if len(suggested_name) > 32 or not self.is_name_unique(suggested_name):
                    # Use "_####" schema for the last 5 characters
                    # If name already ends with _####, we increment it.
                    match = re.search(r'_(\d{4})$', base_name)
                    if match:
                        prefix = base_name[:-5]
                        idx = int(match.group(1))
                    else:
                        # Truncate to fit _####
                        prefix = base_name[:27]
                        idx = 0
                    
                    while True:
                        idx += 1
                        test_name = f"{prefix}_{idx:04d}"
                        if self.is_name_unique(test_name):
                            node.name = test_name
                            break
                else:
                    node.name = suggested_name
            
            new_nodes.append(node)
            
        # 2. Add Nodes to Graph (Temporarily hold to avoid partial links)
        for node in new_nodes:
            # We must clear input_links before adding, then rebuild them from remapped links
            node.input_links = []
            self.add_node(node)
            
        # 3. Process Links
        for link_data in data.get("links", []):
            old_source = link_data.get("source")
            old_target = link_data.get("target")
            
            new_source = id_map.get(old_source)
            new_target = id_map.get(old_target)
            
            if new_source and new_target:
                # add_link handles input_links list and dirty marking
                # Suppress dirty marking on merge as per user request
                self.add_link(new_source, new_target, trigger_dirty=False)

    def to_dict(self):
        """
        Serialize the graph to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the graph.
        """
        return {
            "version": "2.0",
            "app_settings": {"global_token_limit": self.global_token_limit},
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "links": [{"id": l.id, "source": l.source_id, "target": l.target_id} for l in self.links.values()]
        }

    @classmethod
    def from_dict(cls, data):
        """Load a graph from dictionary data with ID collision detection and validation.
        
        If duplicate node or link IDs are detected, they will be automatically remapped
        to new UUIDs and warnings will be logged.
        """
        import uuid
        import logging
        
        logger = logging.getLogger("Graph")
        graph = cls()
        graph.global_token_limit = data.get("app_settings", {}).get("global_token_limit", 16384)
        
        # Track ID mappings for collision detection
        node_id_map = {}  # Maps original_id -> final_id
        seen_node_ids = set()
        
        # Process nodes with collision detection
        for node_data in data.get("nodes", []):
            node = Node.from_dict(node_data)
            original_id = node.id
            
            # Check for node ID collision
            if node.id in seen_node_ids:
                new_id = str(uuid.uuid4())
                logger.warning(
                    f"ID collision detected for node '{node.id}'. "
                    f"Remapping to new ID '{new_id}'. "
                    f"This may indicate a corrupted or manually edited file."
                )
                node.id = new_id
                node_id_map[original_id] = new_id
            else:
                seen_node_ids.add(node.id)
                node_id_map[original_id] = node.id
            
            # Clear input_links - they will be rebuilt from links
            node.input_links = []
            graph.add_node(node)
        
        # Track link IDs for collision detection
        seen_link_ids = set()
        link_id_map = {}  # Maps original_link_id -> final_link_id
        
        # Process links with collision detection and node ID remapping
        for link_data in data.get("links", []):
            original_link_id = link_data.get("id")
            original_source = link_data.get("source")
            original_target = link_data.get("target")
            
            # Remap node IDs if they were changed due to collisions
            remapped_source = node_id_map.get(original_source, original_source)
            remapped_target = node_id_map.get(original_target, original_target)
            
            # Validate that both nodes exist
            if remapped_source not in graph.nodes:
                logger.warning(
                    f"Link references non-existent source node '{original_source}'. Skipping link."
                )
                continue
                
            if remapped_target not in graph.nodes:
                logger.warning(
                    f"Link references non-existent target node '{original_target}'. Skipping link."
                )
                continue
            
            # Create link with remapped node IDs
            l = Link(
                id=original_link_id,
                source_id=remapped_source,
                target_id=remapped_target
            )
            
            # Generate UUID if missing
            if not l.id:
                l.id = str(uuid.uuid4())
                logger.info(f"Generated missing link ID: {l.id}")
            
            # Check for link ID collision
            if l.id in seen_link_ids:
                new_link_id = str(uuid.uuid4())
                logger.warning(
                    f"Link ID collision detected for '{l.id}'. "
                    f"Remapping to new ID '{new_link_id}'."
                )
                link_id_map[l.id] = new_link_id
                l.id = new_link_id
            else:
                seen_link_ids.add(l.id)
                link_id_map[l.id] = l.id
            
            graph.links[l.id] = l
            
            # Update node's input_links list
            if l.target_id in graph.nodes:
                if l.id not in graph.nodes[l.target_id].input_links:
                    graph.nodes[l.target_id].input_links.append(l.id)

        return graph
