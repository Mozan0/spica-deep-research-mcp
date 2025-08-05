#!/bin/bash

# Spica Deep Research MCP Server Startup Script
# This script activates the virtual environment and starts the MCP server

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found at $SCRIPT_DIR/venv"
    echo "Please create a virtual environment by running: python3 -m venv venv"
    exit 1
fi

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "Error: main.py not found in $SCRIPT_DIR"
    exit 1
fi

# Activate virtual environment and start the server
source venv/bin/activate

# Check if required packages are installed
if ! python3 -c "import fastmcp, openai, dotenv" 2>/dev/null; then
    echo "Error: Required packages not installed. Installing from requirements.txt..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        echo "Error: requirements.txt not found"
        exit 1
    fi
fi

# Start the MCP server
exec python3 main.py
