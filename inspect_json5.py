#!/usr/bin/env python3
import json

path = '/Users/markrichman/Library/CloudStorage/ProtonDrive-dovrichman@proton.me-folder/AI Exports/ChatGPT Export - May 2, 2025/conversations.json'

with open(path, 'r') as f:
    data = json.load(f)
    conv = data[0]
    
    mapping = conv.get('mapping', {})
    
    # Look at the FIRST 3 items to understand the structure
    print(f"Mapping has {len(mapping)} nodes\n")
    for i, (node_id, node) in enumerate(list(mapping.items())[:3]):
        print(f"Node {i} ({node_id[:8]}...):")
        print(f"  Type: {type(node)}")
        print(f"  Keys: {list(node.keys())}")
        print(f"  node.get('create_time'): {node.get('create_time')}")
        
        msg = node.get('message')
        if msg:
            print(f"  message type: {type(msg)}")
            print(f"  message keys: {list(msg.keys())}")
            print(f"  message.get('create_time'): {msg.get('create_time')}")
        else:
            print(f"  message: None")
        print()
