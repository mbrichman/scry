#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/Users/markrichman/projects/dovos')
os.environ['USE_POSTGRES'] = 'true'

from db.repositories.unit_of_work import get_unit_of_work

try:
    with get_unit_of_work() as uow:
        convs = uow.conversations.get_all(limit=3)
        for conv in convs:
            print(f"Conversation: {conv.title}")
            print(f"  created_at: {conv.created_at}")
            print(f"  updated_at: {conv.updated_at}")
            messages = uow.messages.get_by_conversation(conv.id, limit=3)
            for msg in messages[:2]:
                print(f"  Message ({msg.role}): created_at={msg.created_at}")
            print()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
