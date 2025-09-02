#!/bin/bash
# start_api.sh - Fixed version
# Script to start the Name Validation API server with better error handling

echo "🚀 Starting Name Validation API Server..."

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "📋 Python version: $PYTHON_VERSION"

# Set environment variables
export PYTHONPATH=$(pwd)
export DICTIONARY_PATH=$(pwd)/name_dictionaries

# Check if dictionaries exist
if [ ! -d "name_dictionaries" ]; then
    echo "⚠️  Warning: name_dictionaries folder not found"
    echo "   Name validation may not work properly"
fi

# Install/upgrade dependencies with better error handling
echo "📦 Installing API dependencies..."

# Try to install with pip, fallback if pandas fails
if ! pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 python-multipart==0.0.6 pydantic==2.5.0 requests==2.31.0 python-dotenv==1.0.0 aiofiles==23.2.1; then
    echo "❌ Some packages failed to install, trying alternative approach..."
    
    # Install without pandas first
    echo "📦 Installing core packages without pandas..."
    pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 python-multipart==0.0.6 pydantic==2.5.0 requests==2.31.0 python-dotenv==1.0.0 aiofiles==23.2.1
    
    # Try to install pandas separately with fallback versions
    echo "📦 Installing pandas..."
    if ! pip install "pandas>=2.2.0"; then
        echo "⚠️  Installing older pandas version for compatibility..."
        if ! pip install "pandas>=2.0.0,<2.2.0"; then
            echo "⚠️  Using existing pandas or installing basic version..."
            pip install pandas || echo "❌ Could not install pandas - API will work with reduced functionality"
        fi
    fi
fi

# Check if uvicorn is available
if ! command -v uvicorn &> /dev/null; then
    echo "❌ uvicorn not found, trying to install again..."
    pip install uvicorn[standard]==0.24.0
    
    # Check again
    if ! command -v uvicorn &> /dev/null; then
        echo "❌ uvicorn still not found, trying alternative installation..."
        pip install uvicorn
        
        # Final check
        if ! command -v uvicorn &> /dev/null; then
            echo "❌ Cannot find uvicorn. Trying to run with python -m uvicorn..."
            echo "✅ Starting API server on http://localhost:8000"
            echo "📖 API Documentation: http://localhost:8000/docs"
            echo "🔍 Health Check: http://localhost:8000/health"
            echo ""
            python -m uvicorn src.name_address_validator.api.main:app --reload --host 0.0.0.0 --port 8000
            exit $?
        fi
    fi
fi

# Start the API server
echo "✅ Starting API server on http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo ""

uvicorn src.name_address_validator.api.main:app --reload --host 0.0.0.0 --port 8000