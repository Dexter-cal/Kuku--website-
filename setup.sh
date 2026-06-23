#!/bin/bash

echo "🍗 Setting up Hope Kuku Shop..."

# Check for python
if ! command -v python3 &> /dev/null
then
    echo "python3 could not be found. Please install it."
    exit
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p instance

echo "✅ Setup complete! Run 'source venv/bin/activate && python app.py' to start the server."
