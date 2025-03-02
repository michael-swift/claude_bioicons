#!/usr/bin/env python3
"""
Simple script to check if the API key is properly configured.
"""
import os
import sys

# Try to load the dotenv file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded .env file if it exists")
except ImportError:
    print("python-dotenv not installed, skipping .env loading")

# Check if API key is in environment
api_key = os.environ.get('ANTHROPIC_API_KEY')

if not api_key:
    print("⚠️ API key not found! Please set up your ANTHROPIC_API_KEY.")
    print("\nTo fix this, edit your credentials file:")
    print("  nano ~/.config/anthropic/credentials")
    print("\nAdd your API key to this file:")
    print("  ANTHROPIC_API_KEY=your_actual_api_key_here")
    print("\nThen restart your terminal or run:")
    print("  source ~/.zshrc")
    sys.exit(1)

if api_key.lower() == 'your_api_key_here':
    print("⚠️ You're using the placeholder API key. Please update with your real key.")
    print("\nTo fix this, edit your credentials file:")
    print("  nano ~/.config/anthropic/credentials")
    print("\nReplace the placeholder with your actual API key:")
    print("  ANTHROPIC_API_KEY=your_actual_api_key_here")
    print("\nThen restart your terminal or run:")
    print("  source ~/.zshrc")
    sys.exit(1)

# Show a masked version of the key for verification
masked_key = f"{api_key[:5]}...{api_key[-5:]}" if len(api_key) > 10 else "[key too short]"
print(f"✅ API key is configured: {masked_key}")
print("Your environment is ready to use the Claude API!")

print("\nTo test the API with your design loop, run:")
print("  cd /Users/michaelswift/Kerna/personal_repos/claude_bioicons/svg_critic")
print("  python visual_design_loop_with_api.py ~/Kerna/personal_repos/claude_bioicons/static/icons/metaSVGs/design_build_test_learn_final.svg")