#!/usr/bin/env python3
"""
Extract small sample conversations from Claude and ChatGPT exports for testing.
"""
import json
import sys

def extract_claude_sample():
    """Extract a small Claude conversation sample."""
    claude_path = '/Users/markrichman/Library/CloudStorage/ProtonDrive-dovrichman@proton.me-folder/AI Exports/Claude Oct 21 2025/conversations.json'
    
    with open(claude_path) as f:
        claude_data = json.load(f)
    
    # Find a conversation with 3-6 messages
    for conv in claude_data[:100]:
        if 'chat_messages' in conv and 3 <= len(conv['chat_messages']) <= 6:
            print(f"Found Claude conversation: '{conv.get('name', 'Untitled')}'")
            print(f"  UUID: {conv.get('uuid')}")
            print(f"  Messages: {len(conv['chat_messages'])}")
            print(f"  Created: {conv.get('created_at')}")
            
            # Save sample
            sample = [conv]
            with open('claude/sample_conversation.json', 'w') as out:
                json.dump(sample, out, indent=2)
            print("  ✓ Saved to claude/sample_conversation.json\n")
            return True
    
    print("  ✗ No suitable Claude conversation found\n")
    return False


def extract_chatgpt_sample():
    """Extract a small ChatGPT conversation sample."""
    chatgpt_path = '/Users/markrichman/Library/CloudStorage/ProtonDrive-dovrichman@proton.me-folder/AI Exports/ChatGPT Setp 29 2025/conversations.json'
    
    with open(chatgpt_path) as f:
        chatgpt_data = json.load(f)
    
    # Find a conversation with reasonable message count
    for conv in chatgpt_data[:100]:
        if 'mapping' not in conv:
            continue
        
        # Count actual messages (not empty nodes)
        messages = [
            node for node in conv['mapping'].values()
            if node.get('message') and node['message'].get('content', {}).get('parts')
        ]
        
        if 3 <= len(messages) <= 6:
            print(f"Found ChatGPT conversation: '{conv.get('title', 'Untitled')}'")
            print(f"  ID: {conv.get('id')}")
            print(f"  Messages: {len(messages)}")
            print(f"  Created: {conv.get('create_time')}")
            
            # Save sample
            sample = [conv]
            with open('chatgpt/sample_conversation.json', 'w') as out:
                json.dump(sample, out, indent=2)
            print("  ✓ Saved to chatgpt/sample_conversation.json\n")
            return True
    
    print("  ✗ No suitable ChatGPT conversation found\n")
    return False


if __name__ == '__main__':
    print("Extracting sample conversations for testing...\n")
    
    claude_ok = extract_claude_sample()
    chatgpt_ok = extract_chatgpt_sample()
    
    if claude_ok and chatgpt_ok:
        print("✓ Successfully extracted both samples!")
        sys.exit(0)
    else:
        print("✗ Failed to extract some samples")
        sys.exit(1)
