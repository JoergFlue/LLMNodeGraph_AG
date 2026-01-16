"""
Test script to verify Smart Merge Positioning in Graph.merge_graph()
"""
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent))

# Setup basic logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(name)s - %(message)s')

from core.graph import Graph, Node

def test_merge_positioning():
    print("=" * 70)
    print("Testing Smart Merge Positioning")
    print("=" * 70)
    
    # 1. create Base Graph
    # Node A at (0,0), w=300, h=450 (default in Node)
    graph = Graph()
    node_a = Node(id="node-a", pos_x=0, pos_y=0, width=300, height=450)
    graph.add_node(node_a)
    
    # Current Bounds:
    # Min X: 0
    # Max Y: 0 + 450 = 450
    
    print(f"Base Graph Node: ({node_a.pos_x}, {node_a.pos_y}) Height: {node_a.height}")
    print(f"Base Bottom-Left Target: X=0, Y=450")
    
    # 2. Create Incoming Data
    # Node B at (100, 100)
    incoming_data = {
        "nodes": [
            {
                "id": "node-b",
                "type": "LLM_Node",
                "pos": [100, 100], 
                "size": [300, 450],
                "text_heights": [100, 160],
                "config": {}, 
                "inputs": []
            }
        ],
        "links": []
    }
    
    # Expected Logic:
    # Incoming Min X: 100
    # Incoming Min Y: 100
    # Offset X = Current Min X (0) - Incoming Min X (100) = -100
    # Offset Y = Current Max Y (450) + Padding (50) - Incoming Min Y (100) = 400
    # Result Pos X = 100 + (-100) = 0
    # Result Pos Y = 100 + 400 = 500
    
    print("\nMerging graph...")
    graph.merge_graph(incoming_data, "merged_file")
    
    node_b = graph.nodes.get("node-b")
    if not node_b:
        print("✗ FAILED: Node B not found after merge")
        return False
        
    print(f"Merged Node Pos: ({node_b.pos_x}, {node_b.pos_y})")
    
    expected_x = 0.0
    expected_y = 500.0
    
    margin = 0.1
    match_x = abs(node_b.pos_x - expected_x) < margin
    match_y = abs(node_b.pos_y - expected_y) < margin
    
    if match_x and match_y:
        print(f"✓ Position matches expected ({expected_x}, {expected_y})")
        print("=" * 70)
        return True
    else:
        print(f"✗ FAILED: Position mismatch! Expected ({expected_x}, {expected_y})")
        return False

if __name__ == "__main__":
    if test_merge_positioning():
        sys.exit(0)
    else:
        sys.exit(1)
