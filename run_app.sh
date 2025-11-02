#!/bin/bash
# run_app.sh - Start FlexDeploy UI and Server simultaneously

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    FlexDeploy Launcher                   ║"
echo "║          AI-Powered Deployment Orchestrator              ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Cleanup function to kill processes on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down FlexDeploy...${NC}"
    
    if [ ! -z "$SERVER_PID" ]; then
        echo "Stopping server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$UI_PID" ]; then
        echo "Stopping UI (PID: $UI_PID)..."
        kill $UI_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✓ FlexDeploy stopped${NC}"
    exit 0
}

# Register cleanup on script exit
trap cleanup EXIT INT TERM

# Check if config.ini exists
if [ ! -f "config.ini" ]; then
    echo -e "${RED}❌ config.ini not found!${NC}"
    echo ""
    echo "Please run setup first:"
    echo -e "  ${YELLOW}./setup_config.sh${NC}"
    exit 1
fi

# Check if ~/.aws/credentials exists
if [ ! -f "$HOME/.aws/credentials" ]; then
    echo -e "${YELLOW}⚠️  AWS credentials not found at ~/.aws/credentials${NC}"
    echo "AI features will be disabled."
    echo ""
fi

# Check if database exists in root directory
if [ ! -f "flexdeploy.db" ]; then
    echo -e "${YELLOW}⚠️  Database not found. Creating new database...${NC}"
fi

# Start Backend Server
echo -e "${BLUE}[1/2] Starting Backend Server...${NC}"
echo "--------------------------------------"

python -m server.main > server.log 2>&1 &
SERVER_PID=$!

echo -e "${GREEN}✓ Server started (PID: $SERVER_PID)${NC}"
echo "  Logs: server.log"
echo "  URL: http://localhost:8000"
echo ""

# Wait for server to be ready
echo "Waiting for server to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Server is ready!${NC}"
        break
    fi
    
    if ! ps -p $SERVER_PID > /dev/null 2>&1; then
        echo -e "${RED}❌ Server failed to start. Check server.log for errors.${NC}"
        tail -20 server.log
        exit 1
    fi
    
    echo -n "."
    sleep 1
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Server failed to start within 30 seconds${NC}"
    tail -20 server.log
    exit 1
fi

echo ""

# Start Frontend UI
echo -e "${BLUE}[2/2] Starting Frontend UI...${NC}"
echo "--------------------------------------"

cd ui
npm run dev > ../ui.log 2>&1 &
UI_PID=$!
cd ..

echo -e "${GREEN}✓ UI started (PID: $UI_PID)${NC}"
echo "  Logs: ui.log"
echo "  URL: http://localhost:5173"
echo ""

# Wait for UI to be ready
echo "Waiting for UI to be ready..."
sleep 3

if ps -p $UI_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ UI is ready!${NC}"
else
    echo -e "${RED}❌ UI failed to start. Check ui.log for errors.${NC}"
    tail -20 ui.log
    exit 1
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ✓ FlexDeploy is running successfully!          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Services:${NC}"
echo -e "  ${GREEN}✓${NC} Backend:  http://localhost:8000"
echo -e "  ${GREEN}✓${NC} Frontend: http://localhost:5173"
echo -e "  ${GREEN}✓${NC} API Docs: http://localhost:8000/docs"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo "  Server: tail -f server.log"
echo "  UI:     tail -f ui.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both services${NC}"
echo ""

# Keep script running and monitor processes
while true; do
    # Check if server is still running
    if ! ps -p $SERVER_PID > /dev/null 2>&1; then
        echo -e "${RED}❌ Server process died unexpectedly${NC}"
        echo "Check server.log for errors:"
        tail -20 server.log
        exit 1
    fi
    
    # Check if UI is still running
    if ! ps -p $UI_PID > /dev/null 2>&1; then
        echo -e "${RED}❌ UI process died unexpectedly${NC}"
        echo "Check ui.log for errors:"
        tail -20 ui.log
        exit 1
    fi
    
    sleep 2
done
