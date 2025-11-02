#!/bin/bash
# install.sh - First-time setup for FlexDeploy

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              FlexDeploy Installation                     ║"
echo "║       First-time setup for all dependencies              ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Check Python
echo -e "${BLUE}[1/6] Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
else
    echo -e "${RED}❌ Python 3.11+ is required${NC}"
    echo "Install from: https://www.python.org/downloads/"
    exit 1
fi

# Check Node.js
echo ""
echo -e "${BLUE}[2/6] Checking Node.js...${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js $NODE_VERSION found${NC}"
else
    echo -e "${RED}❌ Node.js 18+ is required${NC}"
    echo "Install from: https://nodejs.org/"
    exit 1
fi

# Check/Install uv
echo ""
echo -e "${BLUE}[3/6] Checking uv package manager...${NC}"
if command -v uv &> /dev/null; then
    echo -e "${GREEN}✓ uv already installed${NC}"
else
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo -e "${GREEN}✓ uv installed${NC}"
fi

# Install Python packages
echo ""
echo -e "${BLUE}[4/6] Installing Python packages...${NC}"
if command -v uv &> /dev/null; then
    uv pip install -e .
else
    pip install -e .
fi
echo -e "${GREEN}✓ Python packages installed${NC}"
echo "  - fastapi, uvicorn"
echo "  - boto3, botocore"
echo "  - strands-agents"
echo "  - aiohttp, asyncio"

# Install npm packages
echo ""
echo -e "${BLUE}[5/6] Installing npm packages...${NC}"
cd ui
npm install
cd ..
echo -e "${GREEN}✓ npm packages installed${NC}"
echo "  - react, react-router-dom"
echo "  - @mui/material, @mui/icons-material"
echo "  - recharts"
echo "  - vite"

# Setup configuration
echo ""
echo -e "${BLUE}[6/6] Setting up configuration...${NC}"
if [ ! -f "config.ini" ]; then
    echo "Running configuration setup..."
    ./setup_config.sh
else
    echo -e "${YELLOW}config.ini already exists, skipping setup${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ✓ Installation completed successfully!         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}What was installed:${NC}"
echo -e "  ${GREEN}✓${NC} Python packages (backend dependencies)"
echo -e "  ${GREEN}✓${NC} npm packages (frontend dependencies)"
echo -e "  ${GREEN}✓${NC} uv package manager"
echo -e "  ${GREEN}✓${NC} Configuration files"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "1. Configure AWS credentials:"
echo -e "   ${YELLOW}nano ~/.aws/credentials${NC}"
echo ""
echo "   Add your AWS credentials:"
echo "   [default]"
echo "   aws_access_key_id = YOUR_KEY"
echo "   aws_secret_access_key = YOUR_SECRET"
echo "   aws_session_token = YOUR_TOKEN  # If using SSO"
echo ""
echo "2. Enable AWS Bedrock model access:"
echo "   - Login to AWS Console"
echo "   - Go to AWS Bedrock → Model access"
echo "   - Request access to Amazon Nova Pro & Lite"
echo ""
echo "3. Test Bedrock connection:"
echo -e "   ${YELLOW}python test_bedrock_agents.py${NC}"
echo ""
echo "4. Start the application:"
echo -e "   ${YELLOW}./run_app.sh${NC}"
echo ""
echo "5. Open in browser:"
echo -e "   ${YELLOW}http://localhost:5173${NC}"
echo ""
echo -e "${GREEN}For more details, see: README.md${NC}"
echo ""
