#!/usr/bin/env python3
import json

path = '/Users/markrichman/Library/CloudStorage/ProtonDrive-dovrichman@proton.me-folder/AI Exports/ChatGPT Export - May 2, 2025/conversations.json'

with open(path, 'r') as f:
    data = json.load(f)
    conv = data[0]
    
    print(f'Conversation: {conv.get("title")}')
    print(f'Conversation-level timestamps:')
    print(f'  create_time: {conv.get("create_time")}')
    print(f'  update_time: {conv.get("update_time")}')
    
    mapping = conv.get('mapping', {})
    
    # Find first node with a message
    for node_id, node in list(mapping.items())[:20]:
        msg = node.get('message', {})
        if msg and msg.get('author', {}).get('role') in ('user', 'assistant'):
            print(f'\nMessage ({msg.get("author", {}).get("role")}):')
            print(f'  All message fields:')
            for key, val in msg.items():
                if key != 'content':
                    print(f'    {key}: {val}')
            print(f'  metadata: {msg.get("metadata")}')
            break
