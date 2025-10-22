#!/usr/bin/env python3
import os
import sys
import json
sys.path.insert(0, '/Users/markrichman/projects/dovos')
os.environ['USE_POSTGRES'] = 'true'

from controllers.postgres_controller import PostgresController

controller = PostgresController()

# Load a sample conversation JSON
json_files = [f for f in os.listdir('/Users/markrichman/projects/dovos') if f.endswith('.json') and 'conv' in f.lower()]
if not json_files:
    print("No JSON files found")
    sys.exit(1)

json_file = json_files[0]
print(f"Testing with: {json_file}")

with open(json_file, 'r') as f:
    data = json.load(f)

conversations, format_type = controller._detect_json_format(data)
print(f"Format: {format_type}")
print(f"Conversations: {len(conversations)}")

if conversations:
    conv = conversations[0]
    print(f"\nFirst conversation: {conv.get('title', conv.get('name', 'Unknown'))}")
    
    # Extract messages
    if 'mapping' in conv:
        messages = controller._extract_chatgpt_messages(conv['mapping'])
        print(f"Extracted {len(messages)} ChatGPT messages")
    elif 'chat_messages' in conv:
        messages = controller._extract_claude_messages(conv['chat_messages'])
        print(f"Extracted {len(messages)} Claude messages")
    else:
        messages = []
    
    # Check timestamps
    print(f"\nMessage timestamps:")
    for i, msg in enumerate(messages[:3]):
        ts = msg.get('created_at')
        print(f"  Message {i}: created_at={ts} (type: {type(ts).__name__})")
    
    # Calculate earliest/latest
    timestamps = [msg.get('created_at') for msg in messages if msg.get('created_at')]
    if timestamps:
        earliest_ts = min(timestamps)
        latest_ts = max(timestamps)
        print(f"\nEarliest: {earliest_ts} (type: {type(earliest_ts).__name__})")
        print(f"Latest: {latest_ts} (type: {type(latest_ts).__name__})")
