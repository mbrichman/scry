#!/bin/bash
# DovOS MCP Server Launcher
#
# This script launches the DovOS MCP server with proper environment setup.
# Can be used directly or referenced in OpenWebUI MCP configuration.

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Add project root to PYTHONPATH so imports work
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Load environment from .env if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
fi

# Run the MCP server
exec python "$SCRIPT_DIR/dovos_server.py" "$@"
