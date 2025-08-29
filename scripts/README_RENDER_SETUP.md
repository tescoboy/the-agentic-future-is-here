# Render Environment Setup

This directory contains scripts to automatically set up environment variables in Render via their API.

## 🚀 Quick Setup

### Prerequisites

1. **Render API Key**: Get your API key from [Render API Documentation](https://render.com/docs/api)
2. **Service ID**: Find your service ID in the Render dashboard

### Step 1: Get Your Render API Key

1. Go to https://render.com/docs/api
2. Click "Get API Key"
3. Copy the API key

### Step 2: Find Your Service ID

1. Go to your Render dashboard
2. Click on your service (adcp-demo)
3. Copy the service ID from the URL or settings page

### Step 3: Run the Setup Script

```bash
# Set your API key
export RENDER_API_KEY=your_api_key_here

# Run the setup script
./scripts/setup_render.sh your_service_id_here
```

## 🔧 Manual Setup (Alternative)

If you prefer to set environment variables manually:

1. Go to your Render service dashboard
2. Click "Environment" tab
3. Add these variables:

```
GEMINI_API_KEY = AIzaSyCW9W2WkqX64ZO0Mc9s1S9Fteyr0QH-gfc
EMBEDDINGS_PROVIDER = gemini
```

## 📋 What the Script Does

The setup script will:

1. ✅ Verify your API key and service ID
2. 📥 Fetch current environment variables
3. 🔧 Set the required environment variables:
   - `GEMINI_API_KEY`: Your Gemini API key
   - `EMBEDDINGS_PROVIDER`: Set to "gemini"
4. 🔄 Trigger a service restart
5. ⏳ Wait for changes to take effect

## 🎯 Environment Variables Set

| Variable | Value | Purpose |
|----------|-------|---------|
| `GEMINI_API_KEY` | Your API key | Enables AI embeddings and ranking |
| `EMBEDDINGS_PROVIDER` | `gemini` | Enables the embedding system |

## 🔍 Troubleshooting

### "Service ID not found"
- Double-check your service ID in the Render dashboard
- Make sure you're using the correct service

### "API key invalid"
- Verify your Render API key is correct
- Make sure you have the necessary permissions

### "Permission denied"
- Ensure your API key has access to the service
- Check that you own the service or have admin access

## 📞 Support

If you encounter issues:

1. Check the Render API documentation
2. Verify your service is deployed and running
3. Check the Render service logs for errors

## 🎉 Success

After running the script successfully:

1. Your service will restart automatically
2. Wait 2-3 minutes for the changes to take effect
3. Test your application to ensure embeddings are working
4. Check the `/preflight/status` endpoint to verify configuration
