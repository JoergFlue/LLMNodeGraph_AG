"""
Test script to verify Dirty State Suppression in Graph.merge_graph()
"""
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent))

# Setup basic logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(name)s - %(message)s')

from core.graph import Graph, Node, Link

def test_merge_dirty_suppression():
    print("=" * 70)
    print("Testing Dirty State Suppression on Merge")
    print("=" * 70)
    
    # 1. Prepare Incoming Data with Clean Nodes
    # A -> B
    # Both are NOT dirty in the file.
    incoming_data = {
        "nodes": [
            {
                "id": "node-a",
                "type": "LLM_Node",
                "pos": [0, 0],
                "is_dirty": False,
                "name": "Node_A",
                "inputs": []
            },
            {
                "id": "node-b",
                "type": "LLM_Node",
                "pos": [200, 0],
                "is_dirty": False, # Crucial: Starts clean
                "name": "Node_B",
                "inputs": []
            }
        ],
        "links": [
            {
                "id": "link-1",
                "source": "node-a",
                "target": "node-b"
            }
        ]
    }
    
    # 2. Merge into empty graph
    graph = Graph()
    print("Merging graph with clean linked nodes...")
    graph.merge_graph(incoming_data, "merged_file")
    
    # 3. Verify IDs (collision logic isn't the focus, but we need IDs)
    # Since graph was empty, IDs should be preserved or mapped.
    # Actually, merge_graph always remaps if ID exists, or keeps if not.
    # Empty graph -> keep IDs.
    
    node_b = graph.nodes.get("node-b")
    if not node_b:
        print("✗ FAILED: Node B not found")
        return False
        
    print(f"Node B is_dirty state: {node_b.is_dirty}")
    
    if node_b.is_dirty == False:
        print("✓ SUCCESS: Node B remained clean after merge/rewiring.")
        print("=" * 70)
        return True
    else:
        print("✗ FAILED: Node B became dirty! Suppression failed.")
        print("=" * 70)
        return False

if __name__ == "__main__":
    if test_merge_dirty_suppression():
        sys.exit(0)
    else:
        sys.exit(1)
