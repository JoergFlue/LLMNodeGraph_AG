"""
Test script to verify ID collision detection in Graph.from_dict()
"""
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup basic logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(name)s - %(message)s')

from core.graph import Graph

def test_collision_detection():
    """Test that Graph.from_dict() properly detects and handles ID collisions."""
    
    print("=" * 70)
    print("Testing ID Collision Detection in Graph.from_dict()")
    print("=" * 70)
    
    # Load the test file with duplicate IDs
    test_file = Path(__file__).parent / "test_collision.json"
    
    if not test_file.exists():
        print(f"ERROR: Test file not found: {test_file}")
        return False
    
    print(f"\nLoading test file: {test_file}")
    print("\nExpected behavior:")
    print("  - Warning for duplicate node ID 'duplicate-id-1'")
    print("  - Warning for duplicate link ID 'link-1'")
    print("  - All nodes should be loaded with unique IDs")
    print("  - All links should be loaded with unique IDs")
    print("\n" + "-" * 70)
    
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    # Load the graph
    graph = Graph.from_dict(data)
    
    print("\n" + "-" * 70)
    print("\nResults:")
    print(f"  Nodes loaded: {len(graph.nodes)}")
    print(f"  Links loaded: {len(graph.links)}")
    
    # Verify all node IDs are unique
    node_ids = list(graph.nodes.keys())
    unique_node_ids = set(node_ids)
    
    print(f"\n  Node IDs are unique: {len(node_ids) == len(unique_node_ids)}")
    
    assert len(node_ids) == len(unique_node_ids), "Duplicate node IDs found!"
    print("  ✓ All node IDs are unique")
    
    # Verify all link IDs are unique
    link_ids = list(graph.links.keys())
    unique_link_ids = set(link_ids)
    
    print(f"  Link IDs are unique: {len(link_ids) == len(unique_link_ids)}")
    
    assert len(link_ids) == len(unique_link_ids), "Duplicate link IDs found!"
    print("  ✓ All link IDs are unique")
    
    # Verify expected number of nodes and links
    expected_nodes = 3
    expected_links = 2  # Two links with same ID should both be loaded with unique IDs
    
    assert len(graph.nodes) == expected_nodes, f"Expected {expected_nodes} nodes, got {len(graph.nodes)}"
    print(f"  ✓ Correct number of nodes: {expected_nodes}")
    
    assert len(graph.links) == expected_links, f"Expected {expected_links} links, got {len(graph.links)}"
    print(f"  ✓ Correct number of links: {expected_links}")
    
    # Verify all links reference valid nodes
    for link_id, link in graph.links.items():
        assert link.source_id in graph.nodes, f"Link {link_id} references invalid source: {link.source_id}"
        assert link.target_id in graph.nodes, f"Link {link_id} references invalid target: {link.target_id}"
    
    print("  ✓ All links reference valid nodes")
    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED - ID collision detection working correctly!")
    print("=" * 70)

def test_valid_file():
    """Test that valid files still load correctly (no regression)."""
    print("\n\n" + "=" * 70)
    print("Testing Valid File Loading (Regression Test)")
    print("=" * 70)
    
    # Create a simple valid graph
    valid_data = {
        "version": "2.0",
        "app_settings": {"global_token_limit": 16384},
        "nodes": [
            {
                "id": "node-1",
                "type": "LLM_Node",
                "pos": [0, 0],
                "size": [300, 450],
                "text_heights": [100, 160],
                "config": {
                    "model": "gpt-4o",
                    "provider": "Default",
                    "max_tokens": 16000,
                    "trace_depth": 2
                },
                "prompt": "Test prompt",
                "cached_output": "",
                "is_dirty": False,
                "name": "Test_Node",
                "inputs": []
            }
        ],
        "links": []
    }
    
    graph = Graph.from_dict(valid_data)
    
    assert len(graph.nodes) == 1, "Valid file not loaded correctly: wrong node count"
    assert "node-1" in graph.nodes, "Valid file not loaded correctly: node-1 missing"
    
    print("  ✓ Valid file loaded correctly")
    print("=" * 70)

if __name__ == "__main__":
    test1_passed = test_collision_detection()
    test2_passed = test_valid_file()
    
    if test1_passed and test2_passed:
        print("\n✓ All tests passed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed!")
        sys.exit(1)
