#!/usr/bin/env python3
"""
Script to find your Render service ID automatically.
"""

import os
import requests
import sys

def get_service_id(api_key: str, service_name: str = "adcp-demo") -> str:
    """Find service ID by name."""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    url = "https://api.render.com/v1/services"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        services = response.json()
        
        # Find service by name
        for service in services:
            if service['service']['name'] == service_name:
                return service['service']['id']
        
        # If not found by exact name, show all services
        print(f"❌ Service '{service_name}' not found")
        print("\n📋 Available services:")
        for service in services:
            print(f"  - {service['service']['name']} (ID: {service['service']['id']})")
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching services: {e}")
        return None

def main():
    """Main function to find service ID."""
    print("🔍 Finding your Render service ID...")
    
    # Get API key
    api_key = os.environ.get('RENDER_API_KEY')
    if not api_key:
        print("❌ Error: RENDER_API_KEY environment variable not set")
        print("Please set your Render API key:")
        print("export RENDER_API_KEY=your_api_key_here")
        sys.exit(1)
    
    # Try to find the service
    service_id = get_service_id(api_key)
    
    if service_id:
        print(f"✅ Found service ID: {service_id}")
        print(f"🔗 Service URL: https://render.com/dashboard/services/{service_id}")
        print("")
        print("🚀 Now you can run the setup script:")
        print(f"./scripts/setup_render.sh {service_id}")
    else:
        print("❌ No service found. Please deploy your application first.")
        print("")
        print("📋 To deploy:")
        print("1. Go to https://render.com")
        print("2. Click 'New' → 'Web Service'")
        print("3. Connect your GitHub repository")
        print("4. Render will use the render.yaml configuration")

if __name__ == "__main__":
    main()
