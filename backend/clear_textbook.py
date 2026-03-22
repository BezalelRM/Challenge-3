#!/usr/bin/env python3
"""Clear all textbook chunks from the database"""

import json
import os

# Path to the textbook chunks file
chunks_file = os.path.join(os.path.dirname(__file__), 'data', 'textbook_chunks.json')

# Clear the file
with open(chunks_file, 'w') as f:
    json.dump([], f, indent=2)

print("✅ Cleared all textbook chunks from database")
print(f"File: {chunks_file}")
