#!/bin/bash

set -e

echo "Setting up Crime Radar development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
echo "Dependencies installed"

# Copy environment file
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ".env file created from template"
fi

echo "Setup complete!"
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "To run the API:"
echo "  uvicorn crime_radar.api.routes:app --reload"
echo ""
echo "To run the CLI:"
echo "  python -m crime_radar"
