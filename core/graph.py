
from typing import Dict, List, Optional
import json
from .node import Node, Link

class Graph:
    def __init__(self):
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
        self.nodes[node.id] = node

    def remove_node(self, node_id: str):
        if node_id in self.nodes:
            del self.nodes[node_id]
        
        # Remove links connected to this node
        links_to_remove = [
            l_id for l_id, l in self.links.items()
            if l.source_id == node_id or l.target_id == node_id
        ]
        for l_id in links_to_remove:
            self.remove_link(l_id)

    def add_link(self, source_id: str, target_id: str) -> Link:
        # Check for cycles or duplicate links if needed (omitted for MVP speed, but good to have)
        link = Link(source_id=source_id, target_id=target_id)
        self.links[link.id] = link
        
        if target_id in self.nodes:
            self.nodes[target_id].input_links.append(link.id)
            # Mark target as dirty because its inputs changed
            self.mark_dirty(target_id)
            
        return link

    def remove_link(self, link_id: str):
        if link_id in self.links:
            link = self.links[link_id]
            target_id = link.target_id
            del self.links[link_id]
            
            if target_id in self.nodes:
                if link_id in self.nodes[target_id].input_links:
                    self.nodes[target_id].input_links.remove(link_id)
                self.mark_dirty(target_id)

    def mark_dirty(self, node_id: str):
        """Mark node and its descendants as dirty."""
        if node_id not in self.nodes:
            return
            
        node = self.nodes[node_id]
        if node.is_dirty:
            return # Already marked, prevent infinite recursion in valid DAG, but technically we should propagate still?
            # In a DAG, simple recursion works.
        
        node.is_dirty = True
        
        # Find children
        children = [
            l.target_id for l in self.links.values()
            if l.source_id == node_id
        ]
        for child_id in children:
            self.mark_dirty(child_id)

    def get_input_nodes(self, node_id: str) -> List[Node]:
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
        """Merge another graph into the current one, handling ID and name collisions."""
        import uuid
        import re
        
        id_map = {}
        new_nodes: List[Node] = []
        
        # 1. Process Nodes
        for node_data in data.get("nodes", []):
            original_id = node_data.get("id")
            node = Node.from_dict(node_data)
            
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
                self.add_link(new_source, new_target)

    def to_dict(self):
        return {
            "version": "2.0",
            "app_settings": {"global_token_limit": self.global_token_limit},
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "links": [{"id": l.id, "source": l.source_id, "target": l.target_id} for l in self.links.values()]
        }

    @classmethod
    def from_dict(cls, data):
        graph = cls()
        graph.global_token_limit = data.get("app_settings", {}).get("global_token_limit", 16384)
        
        for node_data in data.get("nodes", []):
            node = Node.from_dict(node_data)
            graph.add_node(node)
            
        # For MVP, assume links are stored in the top-level 'links' list for simplicity
        # If we need to support the exact nested structure from the spec example later, we can adapt.
        for link_data in data.get("links", []):
            l = Link(
                id=link_data.get("id"),
                source_id=link_data.get("source"),
                target_id=link_data.get("target")
            )
            # Re-generate UUID if missing
            if not l.id:
                import uuid
                l.id = str(uuid.uuid4())
                
            graph.links[l.id] = l
            # Ensure the node knows about this link (redundancy check vs serialized state)
            if l.target_id in graph.nodes:
                if l.id not in graph.nodes[l.target_id].input_links:
                     graph.nodes[l.target_id].input_links.append(l.id)

        return graph
