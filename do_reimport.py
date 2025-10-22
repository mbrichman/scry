#!/usr/bin/env python3
import os
import sys
import json
sys.path.insert(0, '/Users/markrichman/projects/dovos')
os.environ['USE_POSTGRES'] = 'true'

from db.adapters.legacy_api_adapter import get_legacy_adapter
from controllers.postgres_controller import PostgresController

adapter = get_legacy_adapter()
controller = PostgresController()

# Clear
print("Clearing database...")
result = adapter.clear_database()
print(result['message'])

# Import
json_path = '/Users/markrichman/Library/CloudStorage/ProtonDrive-dovrichman@proton.me-folder/AI Exports/ChatGPT Export - May 2, 2025/conversations.json'
print(f"\nImporting {json_path}...")
with open(json_path, 'r') as f:
    data = json.load(f)

result = controller._import_conversations_json(data)
print(result)

# Verify
print("\nVerifying timestamps...")
from db.repositories.unit_of_work import get_unit_of_work
with get_unit_of_work() as uow:
    convs = uow.conversations.get_all(limit=5)
    for conv in convs:
        print(f"  • {conv.title}: {conv.created_at}")
