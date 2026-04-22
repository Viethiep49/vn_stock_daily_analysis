#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up VN Stock Daily Analysis (Backend + Next.js Frontend) for macOS M1/Intel...${NC}"

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo -e "${BLUE}📦 Homebrew not found. Installing...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Check for Python 3.11+
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
REQUIRED_VERSION="3.11"

if [[ $(echo -e "$PYTHON_VERSION\n$REQUIRED_VERSION" | sort -V | head -n1) != "$REQUIRED_VERSION" ]]; then
    echo -e "${BLUE}🐍 Python 3.11+ not found (Found $PYTHON_VERSION). Installing via Homebrew...${NC}"
    brew install python@3.11
    PYTHON_CMD="python3.11"
else
    echo -e "${GREEN}✅ Python $PYTHON_VERSION found.${NC}"
    PYTHON_CMD="python3"
fi

# Create Virtual Environment
if [ ! -d "venv" ]; then
    echo -e "${BLUE}🏗️ Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv venv
else
    echo -e "${GREEN}✅ Virtual environment already exists.${NC}"
fi

# Activate Virtual Environment
source venv/bin/activate

# Upgrade pip
echo -e "${BLUE}⬆️ Upgrading pip...${NC}"
pip install --upgrade pip

# Install Dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt

# --- Frontend Setup ---
echo -e "${BLUE}🌐 Setting up Frontend (Next.js)...${NC}"

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo -e "${BLUE}📦 Node.js not found. Installing via Homebrew...${NC}"
    brew install node
else
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}✅ Node.js $NODE_VERSION found.${NC}"
fi

# Install Frontend Dependencies
if [ -d "frontend" ]; then
    echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
    cd frontend
    npm install
    cd ..
else
    echo -e "${RED}❌ Frontend directory not found.${NC}"
fi

# Setup .env if not exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${BLUE}📝 Creating .env from .env.example...${NC}"
        cp .env.example .env
        echo -e "${RED}⚠️ Please edit .env and add your API keys!${NC}"
    else
        echo -e "${RED}❌ .env.example not found. Please create .env manually.${NC}"
    fi
else
    echo -e "${GREEN}✅ .env file exists.${NC}"
fi

echo -e "${GREEN}✨ Setup complete!${NC}"
echo -e "${BLUE}💡 To start analyzing, run: ./run.sh --symbol VNM${NC}"
