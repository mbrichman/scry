#!/usr/bin/env python3
import json

path = '/Users/markrichman/Library/CloudStorage/ProtonDrive-dovrichman@proton.me-folder/AI Exports/ChatGPT Export - May 2, 2025/conversations.json'

with open(path, 'r') as f:
    data = json.load(f)
    conv = data[0]
    
    mapping = conv.get('mapping', {})
    
    # Find first node with a message
    for node_id, node in list(mapping.items())[:20]:
        msg = node.get('message', {})
        if msg and msg.get('author', {}).get('role') in ('user', 'assistant'):
            print(f'Message ({msg.get("author", {}).get("role")}):')
            print(f'  message.create_time: {msg.get("create_time")} (type: {type(msg.get("create_time")).__name__})')
            print(f'  message.update_time: {msg.get("update_time")}')
            print(f'  node.create_time: {node.get("create_time")}')
            break
