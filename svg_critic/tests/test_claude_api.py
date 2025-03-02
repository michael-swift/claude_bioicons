#!/usr/bin/env python3
"""
Test script for Claude API SVG analysis.

This script tests various components of the SVG critic system:
1. SVG to PNG conversion
2. Claude API image analysis
3. Claude API SVG improvement

Usage:
    python test_claude_api.py --convert <svg_file> [--output <png_file>]
    python test_claude_api.py --analyze <png_file> [--api-key <key>]
    python test_claude_api.py --improve <svg_file> --feedback <feedback_file> [--api-key <key>]
"""

import os
import sys
import json
import argparse
from claude_api import ClaudeAPI, svg_to_png
from pathlib import Path


def test_svg_conversion(svg_path, output_path=None, width=1200):
    """
    Test SVG to PNG conversion functionality.
    
    Args:
        svg_path: Path to SVG file
        output_path: Path to output PNG file (optional)
        width: Width of output PNG in pixels
    """
    print(f"Testing SVG to PNG conversion for: {svg_path}")
    
    try:
        if not output_path:
            output_path = str(Path(svg_path).with_suffix('.png'))
            
        png_path = svg_to_png(svg_path, output_path, width)
        print(f"Conversion successful! PNG saved to: {png_path}")
        print(f"PNG file size: {os.path.getsize(png_path) / 1024:.2f} KB")
        
        return png_path
    except Exception as e:
        print(f"Conversion failed: {str(e)}")
        return None


def test_claude_analysis(image_path, api_key=None):
    """
    Test Claude API image analysis functionality.
    
    Args:
        image_path: Path to image file
        api_key: Claude API key (optional)
    """
    print(f"Testing Claude API analysis for: {image_path}")
    
    try:
        api = ClaudeAPI(api_key)
        
        prompt = """
        You are a professional graphic designer and visual design critic specializing in 
        scientific and technical diagrams. Analyze this SVG diagram in detail, focusing on:

        1. Visual Balance: Are elements distributed effectively across the diagram?
        2. Color Harmony: Are colors consistent, harmonious, and following the Bioicons palette?
        3. Visual Hierarchy: Is it clear what elements are most important?
        4. Readability: Are text elements appropriately sized and positioned?
        5. Flow: Does the diagram guide the viewer through a logical sequence?
        
        First provide a detailed visual design critique with specific issues you notice.
        Then include an OVERALL SCORE from 0-100 on the line "OVERALL SCORE: [score]/100"
        where [score] is a number based on the quality of the design.
        
        Finally list specific, numbered action items for improvement under the heading 
        "IMPROVEMENT SUGGESTIONS:"
        
        Use technical design language and be thorough in your assessment.
        """
        
        result = api.analyze_image(image_path, prompt)
        
        if result.get('success', False):
            # Save analysis to file
            output_path = str(Path(image_path).with_suffix('.analysis.md'))
            with open(output_path, 'w') as f:
                f.write("# Claude API Image Analysis\n\n")
                f.write(result['analysis'])
            
            print(f"Analysis successful! Results saved to: {output_path}")
            
            # Print brief summary
            print("\nBrief summary of analysis:")
            lines = result['analysis'].split('\n')
            for i, line in enumerate(lines):
                if "OVERALL SCORE:" in line:
                    print(f"  {line.strip()}")
                if "IMPROVEMENT SUGGESTIONS:" in line:
                    for j in range(i+1, min(i+6, len(lines))):
                        if lines[j].strip() and not lines[j].startswith('#'):
                            print(f"  {lines[j].strip()}")
            
            return result
        else:
            print(f"Analysis failed: {result.get('error', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Analysis failed: {str(e)}")
        return None


def test_claude_improvement(svg_path, feedback_path, api_key=None, output_path=None):
    """
    Test Claude API SVG improvement functionality.
    
    Args:
        svg_path: Path to SVG file
        feedback_path: Path to feedback file (can be JSON or markdown)
        api_key: Claude API key (optional)
        output_path: Path to output improved SVG file (optional)
    """
    print(f"Testing Claude API SVG improvement for: {svg_path}")
    print(f"Using feedback from: {feedback_path}")
    
    try:
        # Read SVG file
        with open(svg_path, 'r') as f:
            svg_code = f.read()
        
        # Read feedback file
        with open(feedback_path, 'r') as f:
            feedback_text = f.read()
        
        # Determine if feedback is JSON or markdown
        try:
            feedback = json.loads(feedback_text)
            analysis = feedback.get('analysis', feedback_text)
        except json.JSONDecodeError:
            # Assume it's markdown
            analysis = feedback_text
        
        # Create feedback object
        feedback_obj = {'analysis': analysis}
        
        # Initialize API
        api = ClaudeAPI(api_key)
        
        # Improve SVG
        result = api.improve_svg(svg_code, feedback_obj)
        
        if result.get('success', False):
            # Save improved SVG
            if not output_path:
                output_path = str(Path(svg_path).with_suffix('.improved.svg'))
                
            with open(output_path, 'w') as f:
                f.write(result['improved_svg'])
            
            print(f"Improvement successful! Improved SVG saved to: {output_path}")
            return output_path
        else:
            print(f"Improvement failed: {result.get('error', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Improvement failed: {str(e)}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Test Claude API SVG analysis and improvement")
    
    # Create argument groups for different test modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--convert", help="Test SVG to PNG conversion")
    group.add_argument("--analyze", help="Test Claude API image analysis")
    group.add_argument("--improve", help="Test Claude API SVG improvement")
    
    # Add common arguments
    parser.add_argument("--api-key", "-k", help="Claude API key (defaults to ANTHROPIC_API_KEY env var)")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--width", "-w", type=int, default=1200, help="Width for PNG conversion")
    
    # Add arguments specific to improvement
    parser.add_argument("--feedback", "-f", help="Path to feedback file for improvement")
    
    args = parser.parse_args()
    
    # Test SVG conversion
    if args.convert:
        test_svg_conversion(args.convert, args.output, args.width)
    
    # Test Claude analysis
    elif args.analyze:
        test_claude_analysis(args.analyze, args.api_key)
    
    # Test Claude improvement
    elif args.improve:
        if not args.feedback:
            print("Error: --feedback parameter is required for improvement testing")
            return 1
        
        test_claude_improvement(args.improve, args.feedback, args.api_key, args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())