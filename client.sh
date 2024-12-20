#!/bin/bash

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if server is running
check_server() {
    if ! curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${RED}Error: Server is not running${NC}"
        echo -e "${YELLOW}Please start the server first using: ./server.sh start${NC}"
        exit 1
    fi
}

# Function to start the CLI
start_cli() {
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Setting up virtual environment...${NC}"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt > /dev/null 2>&1
    else
        source venv/bin/activate > /dev/null 2>&1
    fi
    
    # Start the CLI in interactive mode with reduced logging
    export PYTHONWARNINGS="ignore"
    if [ -n "$1" ]; then
        # If input is provided, use it as a command
        echo "$1" | python -W ignore cli.py interactive 2>/dev/null
    else
        # Otherwise, start interactive mode
        python -W ignore cli.py interactive 2>/dev/null
    fi
}

# Main script
check_server
if [ -n "$1" ]; then
    start_cli "$1"
else
    start_cli
fi 