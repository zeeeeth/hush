#!/bin/bash
# Quick Start Script for MTA Sensory-Safe Router

echo "🚇 MTA Sensory-Safe Router - Quick Start"
echo "========================================"
echo ""

# Check if virtual environment exists
venv_created=false
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    venv_created=true
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies only if venv was just created or requirements.txt is newer than install marker
install_marker="venv/.dependencies_installed"
if [ "$venv_created" = true ] || [ ! -f "$install_marker" ] || [ "requirements.txt" -nt "$install_marker" ]; then
    echo "📥 Installing dependencies..."
    while IFS= read -r package || [[ -n "$package" ]]; do
        # Skip empty lines and comments
        if [[ -n "$package" && ! "$package" =~ ^[[:space:]]*# ]]; then
            # Remove any inline comments and whitespace
            package_name=$(echo "$package" | sed 's/#.*//' | xargs)
            if [[ -n "$package_name" ]]; then
                echo "   Installing $package_name..."
                pip install -q "$package_name"
            fi
        fi
    done < requirements.txt
    # Create marker file to indicate dependencies are installed
    touch "$install_marker"
else
    echo "✅ Dependencies already installed (use 'rm venv/.dependencies_installed' to force reinstall)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting Streamlit app..."
echo ""

# Run the app
streamlit run src/app.py