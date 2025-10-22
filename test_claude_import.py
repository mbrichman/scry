#!/usr/bin/env python3
import os
import sys
import json
sys.path.insert(0, '/Users/markrichman/projects/dovos')
os.environ['USE_POSTGRES'] = 'true'

from controllers.postgres_controller import PostgresController
from db.repositories.unit_of_work import get_unit_of_work

controller = PostgresController()

# Import Claude conversations
json_path = '/Users/markrichman/Library/CloudStorage/ProtonDrive-dovrichman@proton.me-folder/AI Exports/Claude Oct 21 2025/conversations.json'
print(f"Importing Claude export: {json_path}\n")

with open(json_path, 'r') as f:
    data = json.load(f)

# Take only first 10 for testing
test_data = data[:10]
result = controller._import_conversations_json(test_data)
print(result)

# Verify
print("\nVerifying Claude conversation timestamps...")
with get_unit_of_work() as uow:
    convs = uow.conversations.get_all(limit=5)
    for conv in convs:
        print(f"  • {conv.title[:50]}: {conv.created_at}")
        msgs = uow.messages.get_by_conversation(conv.id, limit=1)
        if msgs:
            print(f"    Message: {msgs[0].created_at}")
