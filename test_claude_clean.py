#!/usr/bin/env python3
import os
import sys
import json
sys.path.insert(0, '/Users/markrichman/projects/dovos')
os.environ['USE_POSTGRES'] = 'true'

from db.adapters.legacy_api_adapter import get_legacy_adapter
from controllers.postgres_controller import PostgresController
from db.repositories.unit_of_work import get_unit_of_work

adapter = get_legacy_adapter()
controller = PostgresController()

# Clear
print("Clearing database...")
result = adapter.clear_database()
print(result['message'])

# Import Claude conversations (first 20)
json_path = '/Users/markrichman/Library/CloudStorage/ProtonDrive-dovrichman@proton.me-folder/AI Exports/Claude Oct 21 2025/conversations.json'
print(f"\nImporting Claude export: {json_path}\n")

with open(json_path, 'r') as f:
    data = json.load(f)

# Take first 20 for testing
test_data = data[:20]
result = controller._import_conversations_json(test_data)
print(result)

# Verify
print("\nVerifying Claude conversation timestamps (should be Nov 2024 and earlier)...")
with get_unit_of_work() as uow:
    convs = uow.conversations.get_all(limit=10)
    for conv in convs:
        print(f"  • {conv.title[:60]}: {conv.created_at}")
