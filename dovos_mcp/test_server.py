#!/usr/bin/env python3
"""
Simple test to validate MCP server structure without running stdio server.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_server_structure():
    """Test that the server structure is valid."""
    print("Testing MCP server structure...")

    # Import MCP SDK to verify it's available
    try:
        from mcp.server import Server
        print("✓ MCP SDK imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import MCP SDK: {e}")
        print("  Run: pip install mcp")
        return False

    # Check DovOS server instance exists
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("dovos_server", "dovos_mcp/dovos_server.py")
        dovos_server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dovos_server)
        print(f"✓ DovOS MCP server loaded: {dovos_server.app.name}")
    except Exception as e:
        print(f"✗ Failed to load DovOS server: {e}")
        return False

    # Verify services can be imported
    try:
        from db.services.search_service import SearchService, SearchConfig
        from db.repositories.conversation_repository import ConversationRepository
        print("✓ DovOS services imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import DovOS services: {e}")
        return False

    print("\n✓ All structural tests passed!")
    print("\nNext steps:")
    print("1. Ensure PostgreSQL is running")
    print("2. Run: python dovos_mcp/dovos_server.py (will run stdio server)")
    print("3. Or use: ./dovos_mcp/run_server.sh")
    print("4. Or configure in OpenWebUI MCP settings")

    return True

if __name__ == "__main__":
    success = test_server_structure()
    sys.exit(0 if success else 1)
