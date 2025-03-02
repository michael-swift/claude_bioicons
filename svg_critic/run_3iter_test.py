#!/usr/bin/env python3
"""
Custom script to run a 3-iteration test of the visual design loop
with reliable error handling between iterations.
"""

import os
import sys
import json
import time
from pathlib import Path
import shutil
from claude_api import ClaudeAPI, svg_to_png

# Output directory
OUTPUT_DIR = "/Users/michaelswift/Kerna/personal_repos/claude_bioicons/svg_critic/test_output/fresh_fresh_3iter"
INITIAL_SVG = os.path.join(OUTPUT_DIR, "crispr_workflow.svg")

def load_api_key():
    """Load API key from .env file or environment variable."""
    try:
        from dotenv import load_dotenv
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            print(f"Loaded .env file")
    except ImportError:
        pass
        
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("API key not found. Set ANTHROPIC_API_KEY environment variable.")
    return api_key

def analyze_svg(svg_path, api_key, iteration):
    """Analyze SVG with Claude Vision API."""
    print(f"\n=== Running iteration {iteration} ===")
    
    # Initialize API
    api = ClaudeAPI(api_key)
    
    # Convert SVG to PNG
    png_path = os.path.join(OUTPUT_DIR, f"crispr_workflow_iter{iteration-1}_render.png")
    print(f"Converting SVG to PNG...")
    svg_to_png(svg_path, png_path)
    print(f"PNG saved to: {png_path}")
    
    # Prepare prompt
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
    
    # Call API
    print(f"Sending PNG to Claude API for analysis...")
    result = api.analyze_image(png_path, prompt)
    
    if not result.get('success', False):
        raise Exception(f"Analysis failed: {result.get('error', 'Unknown error')}")
    
    # Save analysis
    analysis = result["analysis"]
    analysis_path = os.path.join(OUTPUT_DIR, f"analysis_iter{iteration}.md")
    with open(analysis_path, "w") as f:
        f.write(analysis)
    
    # Extract score
    score = 50  # Default
    import re
    match = re.search(r'OVERALL SCORE:\s*(\d+)/100', analysis)
    if match:
        score = int(match.group(1))
    
    print(f"Analysis saved to: {analysis_path}")
    print(f"Score: {score}/100")
    
    return {
        "analysis": analysis,
        "score": score,
        "analysis_path": analysis_path
    }

def improve_svg(svg_path, feedback, api_key, iteration):
    """Improve SVG with Claude API."""
    # Initialize API
    api = ClaudeAPI(api_key)
    
    # Read SVG
    with open(svg_path, "r") as f:
        svg_code = f.read()
    
    print(f"Asking Claude to improve the SVG...")
    
    # Call API
    result = api.improve_svg(svg_code, feedback)
    
    if not result.get('success', False):
        raise Exception(f"Improvement failed: {result.get('error', 'Unknown error')}")
    
    # Save improved SVG
    improved_svg = result["improved_svg"]
    improved_path = os.path.join(OUTPUT_DIR, f"crispr_workflow_iter{iteration}.svg")
    with open(improved_path, "w") as f:
        f.write(improved_svg)
    
    print(f"Improved SVG saved to: {improved_path}")
    
    return {
        "svg_path": improved_path
    }

def create_summary(results):
    """Create summary of the iterations."""
    summary = {
        "iterations": len(results),
        "scores": [result["score"] for result in results],
        "svg_paths": [result.get("svg_path", "") for result in results],
        "analysis_paths": [result["analysis_path"] for result in results]
    }
    
    summary_path = os.path.join(OUTPUT_DIR, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    report = ["# 3-Iteration SVG Improvement Test\n"]
    report.append(f"Initial SVG: {INITIAL_SVG}\n")
    
    for i, result in enumerate(results):
        report.append(f"## Iteration {i+1}")
        report.append(f"Score: {result['score']}/100")
        report.append(f"Analysis: {result.get('analysis_path', 'N/A')}")
        report.append(f"SVG: {result.get('svg_path', 'N/A')}\n")
    
    report_path = os.path.join(OUTPUT_DIR, "report.md")
    with open(report_path, "w") as f:
        f.write("\n".join(report))
    
    print(f"Summary saved to: {summary_path}")
    print(f"Report saved to: {report_path}")
    
    return {
        "summary_path": summary_path,
        "report_path": report_path
    }

def main():
    """Run the 3-iteration test."""
    try:
        # Load API key
        api_key = load_api_key()
        print(f"API key loaded")
        
        # Verify initial SVG exists
        if not os.path.exists(INITIAL_SVG):
            raise FileNotFoundError(f"Initial SVG not found: {INITIAL_SVG}")
        
        results = []
        
        # Iteration 1
        svg_path = INITIAL_SVG
        feedback = analyze_svg(svg_path, api_key, 1)
        results.append(feedback)
        improved = improve_svg(svg_path, feedback, api_key, 1)
        results[0].update(improved)
        
        # Iteration 2
        svg_path = results[0]["svg_path"]
        feedback = analyze_svg(svg_path, api_key, 2)
        results.append(feedback)
        improved = improve_svg(svg_path, feedback, api_key, 2)
        results[1].update(improved)
        
        # Iteration 3
        svg_path = results[1]["svg_path"]
        feedback = analyze_svg(svg_path, api_key, 3)
        results.append(feedback)
        improved = improve_svg(svg_path, feedback, api_key, 3)
        results[2].update(improved)
        
        # Create summary
        create_summary(results)
        
        print("\n=== Test completed successfully ===")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())