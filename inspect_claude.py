#!/usr/bin/env python3
import json

path = '/Users/markrichman/Library/CloudStorage/ProtonDrive-dovrichman@proton.me-folder/AI Exports/Claude Oct 21 2025/conversations.json'

with open(path, 'r') as f:
    data = json.load(f)
    print(f'Total conversations: {len(data)}')
    
    if data:
        conv = data[0]
        print(f'\nFirst conversation:')
        print(f'  name: {conv.get("name")}')
        print(f'  uuid: {conv.get("uuid")}')
        print(f'  Keys: {list(conv.keys())}')
        
        # Check for conversation-level timestamps
        for key in conv.keys():
            if 'time' in key.lower() or 'date' in key.lower() or 'created' in key.lower():
                print(f'  {key}: {conv.get(key)}')
        
        # Check chat_messages
        chat_messages = conv.get('chat_messages', [])
        print(f'\nChat messages: {len(chat_messages)}')
        
        if chat_messages:
            msg = chat_messages[0]
            print(f'\nFirst message:')
            print(f'  sender: {msg.get("sender")}')
            print(f'  text length: {len(msg.get("text", ""))}')
            print(f'  Keys: {list(msg.keys())}')
            for key in msg.keys():
                if 'time' in key.lower() or 'date' in key.lower() or 'created' in key.lower():
                    print(f'  {key}: {msg.get(key)}')
