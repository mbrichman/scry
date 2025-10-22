#!/usr/bin/env python3
import json

path = '/Users/markrichman/Library/CloudStorage/ProtonDrive-dovrichman@proton.me-folder/AI Exports/ChatGPT Export - May 2, 2025/conversations.json'

with open(path, 'r') as f:
    data = json.load(f)
    print(f'Total conversations: {len(data)}')
    conv = data[0]
    print(f'First conversation: {conv.get("title")}')
    print(f'Keys: {conv.keys()}')
    mapping = conv.get('mapping', {})
    nodes = list(mapping.items())[:5]
    print(f'\nFirst 5 messages:')
    for node_id, node in nodes:
        msg = node.get('message', {})
        if msg:
            ct = node.get('create_time')
            print(f'  create_time: {ct} (type: {type(ct).__name__})')
        else:
            print(f'  [no message content]')
