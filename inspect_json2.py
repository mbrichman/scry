#!/usr/bin/env python3
import json

path = '/Users/markrichman/Library/CloudStorage/ProtonDrive-dovrichman@proton.me-folder/AI Exports/ChatGPT Export - May 2, 2025/conversations.json'

with open(path, 'r') as f:
    data = json.load(f)
    conv = data[0]
    print(f'Conversation: {conv.get("title")}')
    print(f'Conversation create_time: {conv.get("create_time")}')
    print(f'Conversation update_time: {conv.get("update_time")}')
    
    mapping = conv.get('mapping', {})
    print(f'\nTotal nodes in mapping: {len(mapping)}')
    
    # Find first node with a message
    for node_id, node in list(mapping.items())[:20]:
        msg = node.get('message', {})
        if msg:
            print(f'\nFound message in node {node_id}:')
            print(f'  Node keys: {node.keys()}')
            print(f'  Message keys: {msg.keys()}')
            author = msg.get('author', {})
            print(f'  Author role: {author.get("role")}')
            content = msg.get('content', {})
            print(f'  Content keys: {content.keys()}')
            print(f'  create_time in node: {node.get("create_time")}')
            break
