#!/bin/bash
# start_api.sh
# Script to start the Name Validation API server

echo "🚀 Starting Name Validation API Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing API dependencies..."
pip install -r requirements-api.txt

# Set environment variables
export PYTHONPATH=$(pwd)
export DICTIONARY_PATH=$(pwd)/name_dictionaries

# Check if dictionaries exist
if [ ! -d "name_dictionaries" ]; then
    echo "⚠️  Warning: name_dictionaries folder not found"
    echo "   Name validation may not work properly"
fi

# Start the API server
echo "✅ Starting API server on http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo ""

uvicorn src.name_address_validator.api.main:app --reload --host 0.0.0.0 --port 8000