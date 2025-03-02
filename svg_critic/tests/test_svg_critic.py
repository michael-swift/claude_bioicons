#!/usr/bin/env python3
"""
Test script for SVG Critic using the Design-Build-Test-Deep Learn cycle diagram.

This script runs the SVG Critic on our standard test case and displays the results.
"""

import os
import sys
import argparse
from svg_critic import SVGCritic, generate_human_readable_report
from svg_design_loop import SVGDesignLoop

# Define standard test case path
DEFAULT_TEST_SVG = "/Users/michaelswift/Kerna/personal_repos/claude_bioicons/static/icons/metaSVGs/design_build_test_learn_final.svg"
DEFAULT_OUTPUT_DIR = "test_results"

def analyze_svg(svg_path):
    """
    Run SVG Critic on a single SVG and display results.
    
    Args:
        svg_path: Path to the SVG file to analyze
    """
    print(f"Analyzing SVG: {svg_path}")
    
    # Create critic and evaluate
    critic = SVGCritic(svg_path)
    evaluation = critic.evaluate()
    
    # Generate and print report
    report = generate_human_readable_report(evaluation)
    print("\n" + "="*80)
    print(report)
    print("="*80)
    
    return evaluation

def run_design_loop(svg_path, output_dir=DEFAULT_OUTPUT_DIR, iterations=3):
    """
    Run the full SVG Design Loop on a test SVG.
    
    Args:
        svg_path: Path to the SVG file to improve
        output_dir: Directory to store results
        iterations: Number of improvement iterations
    """
    print(f"Running SVG Design Loop on: {svg_path}")
    print(f"Output directory: {output_dir}")
    print(f"Iterations: {iterations}")
    
    # Create and run design loop
    design_loop = SVGDesignLoop(
        svg_path,
        output_dir=output_dir,
        max_iterations=iterations
    )
    
    final_svg, final_evaluation = design_loop.run()
    
    print("\n" + "="*80)
    print(f"Design Loop Complete!")
    print(f"Final SVG: {final_svg}")
    print(f"Final Score: {final_evaluation['overall_score']}/100")
    print(f"Progress Report: {os.path.join(design_loop.output_dir, 'progress_report.html')}")
    print("="*80)
    
    return final_svg, final_evaluation

def main():
    """Main function to parse args and run tests."""
    parser = argparse.ArgumentParser(description="Test SVG Critic with standard test case")
    parser.add_argument("--svg", "-s", default=DEFAULT_TEST_SVG,
                       help=f"Path to test SVG (default: {DEFAULT_TEST_SVG})")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT_DIR,
                       help=f"Output directory for design loop (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--iterations", "-i", type=int, default=3,
                       help="Number of design loop iterations (default: 3)")
    parser.add_argument("--analyze-only", "-a", action="store_true",
                       help="Only run analysis, skip design loop")
    args = parser.parse_args()
    
    try:
        # Verify the SVG exists
        if not os.path.isfile(args.svg):
            print(f"Error: Test SVG not found at {args.svg}")
            return 1
        
        # Run analysis
        evaluation = analyze_svg(args.svg)
        
        # Run design loop if requested
        if not args.analyze_only:
            final_svg, final_evaluation = run_design_loop(
                args.svg, 
                output_dir=args.output,
                iterations=args.iterations
            )
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())