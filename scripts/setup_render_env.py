#!/usr/bin/env python3
"""
Script to set up environment variables in Render via API.
"""

import os
import requests
import json
import sys
from typing import Dict, Any

# Render API configuration
RENDER_API_BASE = "https://api.render.com/v1"
SERVICE_ID = None  # Will be set from command line or environment

def get_render_api_key() -> str:
    """Get Render API key from environment variable."""
    api_key = os.environ.get('RENDER_API_KEY')
    if not api_key:
        print("❌ Error: RENDER_API_KEY environment variable not set")
        print("Please set your Render API key:")
        print("export RENDER_API_KEY=your_api_key_here")
        sys.exit(1)
    return api_key

def get_service_id() -> str:
    """Get service ID from command line or environment."""
    global SERVICE_ID
    if SERVICE_ID:
        return SERVICE_ID
    
    # Try command line argument
    if len(sys.argv) > 1:
        SERVICE_ID = sys.argv[1]
        return SERVICE_ID
    
    # Try environment variable
    SERVICE_ID = os.environ.get('RENDER_SERVICE_ID')
    if SERVICE_ID:
        return SERVICE_ID
    
    print("❌ Error: Service ID not provided")
    print("Usage: python setup_render_env.py <service_id>")
    print("Or set RENDER_SERVICE_ID environment variable")
    sys.exit(1)

def get_current_env_vars(api_key: str, service_id: str) -> Dict[str, Any]:
    """Get current environment variables from Render."""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    url = f"{RENDER_API_BASE}/services/{service_id}/env-vars"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching current environment variables: {e}")
        sys.exit(1)

def update_env_vars(api_key: str, service_id: str, env_vars: Dict[str, str]) -> bool:
    """Update environment variables in Render."""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    url = f"{RENDER_API_BASE}/services/{service_id}/env-vars"
    
    # Prepare the environment variables
    env_vars_data = []
    for key, value in env_vars.items():
        env_vars_data.append({
            'key': key,
            'value': value
        })
    
    try:
        response = requests.put(url, headers=headers, json=env_vars_data)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error updating environment variables: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return False

def main():
    """Main function to set up Render environment variables."""
    print("🚀 Setting up Render environment variables...")
    
    # Get API key and service ID
    api_key = get_render_api_key()
    service_id = get_service_id()
    
    print(f"📋 Service ID: {service_id}")
    
    # Get current environment variables
    print("📥 Fetching current environment variables...")
    current_env = get_current_env_vars(api_key, service_id)
    
    # Define the environment variables to set
    env_vars = {
        'GEMINI_API_KEY': 'AIzaSyCW9W2WkqX64ZO0Mc9s1S9Fteyr0QH-gfc',
        'EMBEDDINGS_PROVIDER': 'gemini'
    }
    
    print("🔧 Environment variables to set:")
    for key, value in env_vars.items():
        # Mask the API key for display
        display_value = value if key != 'GEMINI_API_KEY' else f"{value[:10]}..."
        print(f"  {key} = {display_value}")
    
    # Check if variables already exist
    existing_vars = {var['key']: var['value'] for var in current_env}
    
    print("\n📊 Current environment variables:")
    for var in current_env:
        display_value = var['value'] if var['key'] != 'GEMINI_API_KEY' else f"{var['value'][:10]}..."
        print(f"  {var['key']} = {display_value}")
    
    # Ask for confirmation
    print("\n❓ Do you want to update the environment variables? (y/N): ", end="")
    response = input().strip().lower()
    
    if response not in ['y', 'yes']:
        print("❌ Cancelled")
        return
    
    # Update environment variables
    print("📤 Updating environment variables...")
    success = update_env_vars(api_key, service_id, env_vars)
    
    if success:
        print("✅ Environment variables updated successfully!")
        print("🔄 Your Render service will restart automatically")
        print("⏳ Please wait a few minutes for the changes to take effect")
    else:
        print("❌ Failed to update environment variables")

if __name__ == "__main__":
    main()
