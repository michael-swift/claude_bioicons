#!/usr/bin/env python3
"""
Simple script to test loading the API key from environment variables or .env file.
"""

import os
from pathlib import Path
import sys

# Try to use python-dotenv if available
try:
    from dotenv import load_dotenv
    env_file_path = Path(__file__).parent / '.env'
    load_dotenv(env_file_path)
    print(f"Loaded .env file from {env_file_path}")
except ImportError:
    print("python-dotenv not installed, skipping .env file loading")

# Check for API key in environment variables
api_key = os.environ.get("ANTHROPIC_API_KEY")
if api_key:
    # Print first few and last few characters for verification
    if len(api_key) > 10:
        masked_key = f"{api_key[:5]}...{api_key[-5:]}"
    else:
        masked_key = "[too short to be valid]"
    print(f"API key found: {masked_key}")
    
    # Check if key appears to be a placeholder
    if "your_api_key" in api_key.lower():
        print("Warning: API key appears to be a placeholder. Please set your actual API key.")
        sys.exit(1)
else:
    print("API key not found in environment variables.")
    print("Please set the ANTHROPIC_API_KEY environment variable.")
    print("You can do this in your shell with:")
    print("  export ANTHROPIC_API_KEY=your_api_key_here")
    print("Or create a .env file in the svg_critic directory with:")
    print("  ANTHROPIC_API_KEY=your_api_key_here")
    sys.exit(1)

print("API key validation successful!")