"""
Node - Data structures for nodes and links.
"""

import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class NodeConfig:
    """
    Configuration for an LLM Node.
    
    Attributes:
        model (str): The LLM model name (e.g., "gpt-4o").
        provider (str): The LLM provider (e.g., "OpenAI", "Ollama").
        max_tokens (int): Maximum tokens for context + generation.
        trace_depth (int): How many levels of history to include.
    """
    model: str = "gpt-4o"
    provider: str = "Default"  # Default, Ollama, OpenAI, Gemini
    max_tokens: int = 16000
    trace_depth: int = 2

@dataclass
class Link:
    """
    Represents a connection between two nodes.
    
    Attributes:
        source_id (str): ID of the source node (output).
        target_id (str): ID of the target node (input).
        id (str): Unique identifier for the link.
    """
    source_id: str
    target_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class Node:
    """
    Represents a Node in the flow graph.
    
    Attributes:
        id (str): Unique identifier.
        config (NodeConfig): LLM configuration.
        prompt (str): User prompt text.
        cached_output (str): Last generated output.
        is_dirty (bool): Whether the node needs re-computation.
        name (str): Display name.
        input_links (List[str]): List of incoming Link IDs.
        pos_x (float): X position in UI.
        pos_y (float): Y position in UI.
        width (float): Node width.
        height (float): Node height.
        prompt_height (int): Height of prompt text area.
        output_height (int): Height of output text area.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config: NodeConfig = field(default_factory=NodeConfig)
    prompt: str = ""
    cached_output: str = ""
    is_dirty: bool = False
    name: str = ""
    
    # List of input connections (Links)
    # We might store just IDs, but storing Link objects or having a Graph manages them is better.
    # For a DAG, a node knowing its inputs is useful for context assembly.
    input_links: List[str] = field(default_factory=list) # List of Link IDs
    
    # UI Position
    pos_x: float = 0.0
    pos_y: float = 0.0
    
    # UI Size (for resizable nodes)
    width: float = 300.0
    height: float = 450.0
    prompt_height: int = 100
    output_height: int = 160

    def to_dict(self):
        """
        Serialize the node to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the node.
        """
        return {
            "id": self.id,
            "type": "LLM_Node",
            "pos": [self.pos_x, self.pos_y],
            "size": [self.width, self.height],
            "text_heights": [self.prompt_height, self.output_height],
            "config": {
                "model": self.config.model,
                "provider": self.config.provider,
                "max_tokens": self.config.max_tokens,
                "trace_depth": self.config.trace_depth
            },
            "prompt": self.prompt,
            "cached_output": self.cached_output,
            "is_dirty": self.is_dirty,
            "name": self.name,
            "inputs": self.input_links
        }

    @classmethod
    def from_dict(cls, data):
        """
        Deserialize a node from a dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary containing node data.
            
        Returns:
            Node: A new Node instance.
        """
        size = data.get("size", [300.0, 450.0])
        text_heights = data.get("text_heights", [100, 160])
        
        node = cls(
            id=data.get("id", str(uuid.uuid4())),
            pos_x=data.get("pos", [0, 0])[0],
            pos_y=data.get("pos", [0, 0])[1],
            width=size[0],
            height=size[1],
            prompt_height=text_heights[0],
            output_height=text_heights[1],
            prompt=data.get("prompt", ""),
            cached_output=data.get("cached_output", ""),
            is_dirty=data.get("is_dirty", False),
            name=data.get("name", ""),
            input_links=data.get("inputs", [])
        )
        conf = data.get("config", {})
        node.config = NodeConfig(
            model=conf.get("model", "gpt-4o"),
            provider=conf.get("provider", "Default"),
            max_tokens=conf.get("max_tokens", 16000),
            trace_depth=conf.get("trace_depth", 2)
        )
        return node
