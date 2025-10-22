#!/usr/bin/env python3
import json

path = '/Users/markrichman/Library/CloudStorage/ProtonDrive-dovrichman@proton.me-folder/AI Exports/Claude Oct 21 2025/conversations.json'

with open(path, 'r') as f:
    data = json.load(f)
    
    # Find one with messages
    for i, conv in enumerate(data[:20]):
        chat_messages = conv.get('chat_messages', [])
        if chat_messages:
            print(f'Conversation {i}: {conv.get("name")}')
            print(f'  created_at: {conv.get("created_at")}')
            print(f'  updated_at: {conv.get("updated_at")}')
            print(f'  Messages: {len(chat_messages)}')
            
            # Check first message
            msg = chat_messages[0]
            print(f'\n  First message:')
            print(f'    sender: {msg.get("sender")}')
            print(f'    Keys: {list(msg.keys())}')
            for key in msg.keys():
                if 'time' in key.lower() or 'date' in key.lower() or 'created' in key.lower():
                    print(f'    {key}: {msg.get(key)}')
            break
