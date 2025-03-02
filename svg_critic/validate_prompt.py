#!/usr/bin/env python3
"""
Validate SVG generation prompt structure without making API calls.
"""

import os
import sys
from pathlib import Path
import json

# Import the SVG Generator class
sys.path.append(str(Path(__file__).parent))
from svg_generator import SVGGenerator

def main():
    """
    Generate and display the SVG generation prompt for a given test case.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate SVG generation prompt structure")
    parser.add_argument("prompt", help="Text prompt to use for testing")
    parser.add_argument("--output", "-o", help="Path to save the prompt to (optional)")
    
    args = parser.parse_args()
    
    # Initialize generator without API key validation
    try:
        generator = SVGGenerator(api_key="fake_key_for_validation")
    except ValueError:
        # Override the ValueError for missing API key
        generator = SVGGenerator.__new__(SVGGenerator)
        generator.api_key = "fake_key_for_validation"
    
    # Generate the enhanced prompt
    enhanced_prompt = generator._create_svg_generation_prompt(args.prompt)
    
    # Print the enhanced prompt
    print("\n===== ENHANCED SVG GENERATION PROMPT =====\n")
    print(enhanced_prompt)
    print("\n==========================================\n")
    
    # Save the prompt to a file if requested
    if args.output:
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        with open(args.output, "w") as f:
            f.write(enhanced_prompt)
            
        print(f"Prompt saved to: {args.output}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())