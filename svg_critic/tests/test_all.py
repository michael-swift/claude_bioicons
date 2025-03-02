#!/usr/bin/env python3
"""
Test all components of the SVG Critic system.

This script runs tests for each major component of the SVG Critic system
to ensure everything is working correctly.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Test SVG path
DEFAULT_TEST_SVG = "/Users/michaelswift/Kerna/personal_repos/claude_bioicons/static/icons/metaSVGs/design_build_test_learn_final.svg"

def run_command(command, description):
    """Run a command and print the result."""
    print(f"\n{'='*80}")
    print(f"Testing: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("SUCCESS!")
        
        # Print truncated output if it's too long
        output = result.stdout
        if len(output) > 1000:
            print(f"Output (truncated):\n{output[:500]}\n...\n{output[-500:]}")
        else:
            print(f"Output:\n{output}")
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"FAILED: {str(e)}")
        print(f"Error output:\n{e.stderr}")
        return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_svg_critic(svg_path):
    """Test the original SVG Critic module."""
    return run_command(
        ["python", "svg_critic.py", svg_path],
        "Original SVG Critic"
    )

def test_visual_svg_critic(svg_path):
    """Test the Visual SVG Critic module."""
    return run_command(
        ["python", "visual_svg_critic.py", svg_path, "--improve"],
        "Visual SVG Critic"
    )

def test_design_loop(svg_path):
    """Test the Design Loop module."""
    # Create a temporary output directory
    output_dir = "test_loop_output"
    os.makedirs(output_dir, exist_ok=True)
    
    return run_command(
        ["python", "visual_design_loop.py", svg_path, "--output-dir", output_dir, "--iterations", "1"],
        "Design Loop"
    )

def test_svg_to_png(svg_path):
    """Test the SVG to PNG conversion."""
    return run_command(
        ["python", "test_claude_api.py", "--convert", svg_path],
        "SVG to PNG Conversion"
    )

def test_claude_api(svg_path):
    """Test the Claude API integration if API key is available."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n⚠️ ANTHROPIC_API_KEY not set, skipping Claude API tests.")
        return False
    
    # First test conversion
    png_path = str(Path(svg_path).with_suffix('.png'))
    conversion_success = test_svg_to_png(svg_path)
    
    if not conversion_success or not os.path.exists(png_path):
        print(f"Could not convert SVG to PNG, skipping API analysis test.")
        return False
    
    # Test analysis
    return run_command(
        ["python", "test_claude_api.py", "--analyze", png_path],
        "Claude API Analysis"
    )

def test_all(svg_path):
    """Run all tests."""
    results = {}
    
    # Test each component
    results["SVG Critic"] = test_svg_critic(svg_path)
    results["Visual SVG Critic"] = test_visual_svg_critic(svg_path)
    results["Design Loop"] = test_design_loop(svg_path)
    results["SVG to PNG"] = test_svg_to_png(svg_path)
    
    # Test Claude API if key is available
    if os.environ.get("ANTHROPIC_API_KEY"):
        results["Claude API"] = test_claude_api(svg_path)
    
    # Print summary
    print("\n\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print("="*50)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
        all_passed = all_passed and passed
    
    print("\nOverall status:", "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED")
    
    return all_passed

def main():
    parser = argparse.ArgumentParser(description="Test all SVG Critic components")
    parser.add_argument("--svg-path", default=DEFAULT_TEST_SVG, 
                       help=f"Path to test SVG file (default: {DEFAULT_TEST_SVG})")
    parser.add_argument("--component", choices=["svg-critic", "visual-critic", "design-loop", 
                                               "svg-to-png", "claude-api", "all"],
                       default="all", help="Which component to test (default: all)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.svg_path):
        print(f"Error: SVG file not found at {args.svg_path}")
        return 1
    
    # Run the selected test
    if args.component == "svg-critic":
        success = test_svg_critic(args.svg_path)
    elif args.component == "visual-critic":
        success = test_visual_svg_critic(args.svg_path)
    elif args.component == "design-loop":
        success = test_design_loop(args.svg_path)
    elif args.component == "svg-to-png":
        success = test_svg_to_png(args.svg_path)
    elif args.component == "claude-api":
        success = test_claude_api(args.svg_path)
    else:  # "all"
        success = test_all(args.svg_path)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())