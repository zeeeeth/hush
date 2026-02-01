#!/bin/bash
# Quick Start Script for MTA Sensory-Safe Router

echo "🚇 MTA Sensory-Safe Router - Quick Start"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting Streamlit app..."
echo ""
echo "   Local URL: http://localhost:8501"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""

# Run the app
streamlit run app.py
