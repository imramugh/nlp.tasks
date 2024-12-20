#!/bin/bash

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Server PID file
PID_FILE=".server.pid"

# Function to display banner
show_banner() {
    echo -e "${BLUE}${BOLD}"
    echo "╔════════════════════════════════════════════╗"
    echo "║     Task Management System Server Tool     ║"
    echo "╚════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Function to check if server is running
is_server_running() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null; then
            return 0 # true, server is running
        fi
    fi
    return 1 # false, server is not running
}

# Function to start the server
start_server() {
    echo -e "${YELLOW}Starting Task Management Server...${NC}"
    
    # Check if server is already running
    if is_server_running; then
        echo -e "${RED}Server is already running with PID $(cat $PID_FILE)${NC}"
        return 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Setting up virtual environment...${NC}"
        python3 -m venv venv
        source venv/bin/activate
        echo -e "${YELLOW}Installing dependencies...${NC}"
        pip install -r requirements.txt
    else
        source venv/bin/activate
    fi
    
    # Start the server
    echo -e "${CYAN}Initializing server...${NC}"
    python main.py &
    pid=$!
    echo $pid > "$PID_FILE"
    
    # Wait a moment to ensure server started properly
    sleep 2
    if is_server_running; then
        echo -e "${GREEN}Server started successfully!${NC}"
        echo -e "${CYAN}Server is running at ${BOLD}http://localhost:8000${NC}"
        echo -e "${CYAN}WebSocket endpoint: ${BOLD}ws://localhost:8000/ws${NC}"
    else
        echo -e "${RED}Failed to start server${NC}"
        rm -f "$PID_FILE"
    fi
}

# Function to stop the server
stop_server() {
    echo -e "${YELLOW}Stopping Task Management Server...${NC}"
    
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null; then
            kill $pid
            rm -f "$PID_FILE"
            echo -e "${GREEN}Server stopped successfully${NC}"
        else
            echo -e "${RED}Server process not found${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${RED}Server is not running${NC}"
    fi
}

# Function to show server status
show_status() {
    if is_server_running; then
        echo -e "${GREEN}Server is running with PID $(cat $PID_FILE)${NC}"
        echo -e "${CYAN}Server URL: ${BOLD}http://localhost:8000${NC}"
        echo -e "${CYAN}WebSocket: ${BOLD}ws://localhost:8000/ws${NC}"
    else
        echo -e "${RED}Server is not running${NC}"
    fi
}

# Main script
show_banner

case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 2
        start_server
        ;;
    status)
        show_status
        ;;
    *)
        echo -e "${YELLOW}Usage: $0 {start|stop|restart|status}${NC}"
        exit 1
        ;;
esac

exit 0 