#!/bin/bash
# Script to run the design loop with proper configuration

# 1. Check if API key is properly configured
python check_api_key.py
if [ $? -ne 0 ]; then
    echo "API key check failed. Please configure your API key as instructed above."
    exit 1
fi

# 2. Set default SVG path or use provided one
SVG_PATH="${1:-../static/icons/metaSVGs/design_build_test_learn_final.svg}"

# 3. Make sure SVG file exists
if [ ! -f "$SVG_PATH" ]; then
    echo "Error: SVG file not found at $SVG_PATH"
    exit 1
fi

echo "Running design loop on: $SVG_PATH"
echo "================================================"

# 4. Run the design loop with API integration
python visual_design_loop_with_api.py "$SVG_PATH" --iterations=2

# Check if the run was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "Design loop completed successfully!"
    echo "Check the output directory for the improved SVG and progress report."
else
    echo ""
    echo "Design loop encountered an error."
    echo "Please check the error messages above for troubleshooting."
fi