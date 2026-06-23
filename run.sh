#!/bin/bash

# Define colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🍗 Welcome to Hope Kuku Shop Auto-Launcher${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed.${NC}"
    exit 1
fi

# Create Virtual Environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate Virtual Environment
source venv/bin/activate

# Install/Update dependencies
echo -e "${GREEN}Syncing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${BLUE}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${RED}Warning: Default development settings loaded. Please update .env for production.${NC}"
fi

# Ensure instance directory exists
mkdir -p instance

# Launch the application
echo -e "${GREEN}🚀 Launching Hope Kuku Shop...${NC}"
python app.py
