#!/bin/bash
set -e

echo "🚀 Render Environment Setup Script"
echo "=================================="

# Check if service ID is provided
if [ $# -eq 0 ]; then
    echo "❌ Error: Service ID is required"
    echo "Usage: ./scripts/setup_render.sh <service_id>"
    echo ""
    echo "To find your service ID:"
    echo "1. Go to your Render dashboard"
    echo "2. Click on your service"
    echo "3. Copy the service ID from the URL or settings"
    exit 1
fi

SERVICE_ID=$1

echo "📋 Service ID: $SERVICE_ID"
echo ""

# Check if RENDER_API_KEY is set
if [ -z "$RENDER_API_KEY" ]; then
    echo "❌ Error: RENDER_API_KEY environment variable not set"
    echo ""
    echo "Please set your Render API key:"
    echo "export RENDER_API_KEY=your_api_key_here"
    echo ""
    echo "To get your API key:"
    echo "1. Go to https://render.com/docs/api"
    echo "2. Click 'Get API Key'"
    echo "3. Copy the key and set it as an environment variable"
    exit 1
fi

echo "✅ RENDER_API_KEY is set"
echo ""

# Run the Python script
echo "🔧 Running environment setup..."
python3 scripts/setup_render_env.py "$SERVICE_ID"

echo ""
echo "🎉 Setup complete!"
