#!/usr/bin/env python3
"""
Simple test script to verify Claude API key is properly configured.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment variables from {env_file}")
    else:
        print(f"Warning: .env file not found at {env_file}")
except ImportError:
    print("Warning: python-dotenv not installed, skipping .env loading")

# Check for API key
api_key = os.environ.get("ANTHROPIC_API_KEY")
if api_key:
    masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    print(f"API key found in environment: {masked_key}")
else:
    print("ERROR: ANTHROPIC_API_KEY not found in environment variables")
    sys.exit(1)

# Test API key with a simple request (optional)
try:
    import requests
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    print("Testing API key with Claude API...")
    
    # Simple test request to user info endpoint (doesn't consume tokens)
    response = requests.get(
        "https://api.anthropic.com/v1/users/me", 
        headers=headers
    )
    
    if response.status_code == 200:
        print("API key validation successful!")
        print(f"Response: {response.json()}")
    else:
        print(f"API key validation failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)
        
except ImportError:
    print("Warning: requests package not installed, skipping API validation")
except Exception as e:
    print(f"Error testing API key: {str(e)}")
    sys.exit(1)

print("\nSetup looks good! API key is properly configured.")