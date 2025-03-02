#!/usr/bin/env python3
"""
Simple test script to run the visual design loop with a directly provided API key.
This avoids environment variable issues by putting the key directly in the script execution.
"""

import sys
import os
from pathlib import Path

# Test SVG path
DEFAULT_SVG_PATH = Path(__file__).parent.parent / "static/icons/metaSVGs/design_build_test_learn_final.svg"

def main():
    """Main function to handle command line arguments and run the test."""
    # Get API key from command line
    if len(sys.argv) < 2:
        print("Usage: python test_with_key.py YOUR_API_KEY [path_to_svg]")
        return 1
    
    api_key = sys.argv[1]
    
    # Get SVG path (use default if not provided)
    svg_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SVG_PATH
    
    # Ensure SVG file exists
    if not os.path.isfile(svg_path):
        print(f"Error: SVG file not found at {svg_path}")
        return 1
    
    print(f"Testing with API key: {api_key[:5]}...{api_key[-5:]}")
    print(f"Using SVG file: {svg_path}")
    
    # Import needed modules
    from visual_design_loop_with_api import VisualDesignLoopWithAPI
    
    # Run the design loop
    try:
        output_dir = "api_key_test_output"
        design_loop = VisualDesignLoopWithAPI(
            svg_path,
            api_key=api_key,
            output_dir=output_dir,
            max_iterations=2,  # Just do 2 iterations for testing
            satisfaction_threshold=95
        )
        
        final_svg, final_feedback = design_loop.run()
        
        print("\n--- Final Results ---")
        print(f"Final SVG: {final_svg}")
        print(f"Final Score: {final_feedback.get('overall_score', '(not available)')}/100")
        print(f"Progress Report: {os.path.join(design_loop.output_dir, 'progress_report.html')}")
        
        return 0
    
    except Exception as e:
        print(f"Error running design loop: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())