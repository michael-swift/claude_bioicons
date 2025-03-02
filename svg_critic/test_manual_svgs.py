#!/usr/bin/env python3
"""
Test script for running the improvement loop on manually created SVGs.
This skips the initial generation step and focuses on improving existing SVGs.
"""

import os
import sys
import json
import argparse
import time
import datetime
import shutil
from pathlib import Path

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

from visual_design_loop_with_api import VisualDesignLoopWithAPI

def run_improvement_only(input_svg, experiment_name=None, output_dir=None, max_iterations=3, satisfaction_threshold=85, api_key=None):
    """
    Run only the improvement part of the workflow using a pre-existing SVG.
    
    Args:
        input_svg: Path to the SVG file to improve
        experiment_name: Name of the experiment (default: derived from SVG filename)
        output_dir: Directory to save outputs (default: creates timestamped directory)
        max_iterations: Maximum number of iterations (default: 3)
        satisfaction_threshold: Score to stop iterations (default: 85)
        api_key: Claude API key (default: None, uses environment variable)
    
    Returns:
        Dictionary with results
    """
    start_time = time.time()
    
    # Set experiment name if not provided
    if not experiment_name:
        experiment_name = os.path.splitext(os.path.basename(input_svg))[0]
    
    # Create output directory
    if not output_dir:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"experiment_{experiment_name}_{timestamp}"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save experiment details
    experiment_doc = {
        "experiment_name": experiment_name,
        "input_svg": input_svg,
        "timestamp": datetime.datetime.now().isoformat(),
        "max_iterations": max_iterations,
        "satisfaction_threshold": satisfaction_threshold,
        "output_directory": output_dir
    }
    
    experiment_doc_path = os.path.join(output_dir, "experiment_details.json")
    with open(experiment_doc_path, "w") as f:
        json.dump(experiment_doc, f, indent=2)
    
    # Create improvement directory
    improvement_dir = os.path.join(output_dir, "improvement")
    os.makedirs(improvement_dir, exist_ok=True)
    
    # Copy input SVG to the improvement directory
    initial_copy_path = os.path.join(improvement_dir, os.path.basename(input_svg))
    shutil.copy(input_svg, initial_copy_path)
    
    print(f"\n=== IMPROVING SVG DESIGN: {experiment_name} ===")
    
    # Run the design loop
    design_loop = VisualDesignLoopWithAPI(
        initial_copy_path,
        api_key=api_key,
        output_dir=improvement_dir,
        max_iterations=max_iterations,
        satisfaction_threshold=satisfaction_threshold
    )
    
    try:
        # Run improvement loop
        final_svg, final_feedback = design_loop.run()
        final_score = final_feedback.get('overall_score', 0)
        
        # Create summary report
        print("\n=== CREATING WORKFLOW SUMMARY ===")
        
        summary = {
            "experiment_name": experiment_name,
            "input_svg": input_svg,
            "final_svg": final_svg,
            "final_score": final_score,
            "improvement_report": os.path.join(improvement_dir, "progress_report.html"),
            "total_time_seconds": time.time() - start_time,
            "timestamp": datetime.datetime.now().isoformat(),
            "improvement_iterations": len(design_loop.history)
        }
        
        # Save summary
        summary_path = os.path.join(output_dir, "workflow_summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Create report
        report_path = os.path.join(output_dir, "workflow_report.md")
        create_markdown_report(summary, report_path, experiment_name)
        
        return {
            "success": True,
            "summary": summary,
            "report_path": report_path,
            "final_svg": final_svg
        }
    
    except Exception as e:
        error_message = f"Design improvement failed: {str(e)}"
        print(f"Error: {error_message}")
        
        return {
            "success": False,
            "error": error_message
        }

def create_markdown_report(summary, report_path, experiment_name):
    """Create markdown report for the workflow."""
    
    report_lines = [
        f"# SVG Design Experiment: {experiment_name}",
        "",
        f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Experiment Overview",
        "",
        "This experiment tests the SVG improvement workflow:",
        "1. Starting with a manually created SVG diagram",
        "2. Running visual evaluation and automated critique",
        "3. Performing iterative improvement based on feedback",
        "",
        "## Input SVG",
        "",
        f"* Initial SVG: [{Path(summary['input_svg']).name}]({summary['input_svg']})",
        "",
        "## Improvement Process",
        "",
        f"* Improvement Iterations: {summary['improvement_iterations']}",
        f"* Final SVG: [{Path(summary['final_svg']).name}]({summary['final_svg']})",
        f"* Final Quality Score: {summary['final_score']}/100",
        f"* Detailed Progress Report: [{Path(summary['improvement_report']).name}]({summary['improvement_report']})",
        "",
        "## Results Summary",
        "",
        f"* Total Processing Time: {summary['total_time_seconds']:.2f} seconds",
        f"* Final Design Score: {summary['final_score']}/100",
        "",
        "## Observations and Analysis",
        "",
        "What worked well:",
        "- (Placeholder for human analysis)",
        "",
        "Areas for improvement:",
        "- (Placeholder for human analysis)",
        "",
        "## View Results",
        "",
        "To view the detailed visual progress report, open the HTML file in your browser:",
        "",
        f"`open \"{summary['improvement_report']}\"`",
        "",
        "## Reproducibility",
        "",
        "To reproduce this experiment, use:",
        "",
        f"```bash",
        f"python test_manual_svgs.py {summary['input_svg']} --experiment-name \"{experiment_name}\" --iterations {summary.get('improvement_iterations', 3)}",
        f"```"
    ]
    
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))

def main():
    """Parse arguments and run the workflow."""
    parser = argparse.ArgumentParser(
        description="Run improvement workflow on manually created SVGs"
    )
    parser.add_argument(
        "input_svg",
        help="Path to the SVG file to improve"
    )
    parser.add_argument(
        "--experiment-name", "-e",
        help="Name of the experiment (default: derived from SVG filename)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        help="Directory to save outputs (default: creates timestamped directory)"
    )
    parser.add_argument(
        "--iterations", "-i",
        type=int,
        default=3,
        help="Maximum number of iterations (default: 3)"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=int,
        default=85,
        help="Score threshold to stop iterations (default: 85)"
    )
    parser.add_argument(
        "--api-key", "-k",
        help="Claude API key (defaults to ANTHROPIC_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    try:
        result = run_improvement_only(
            args.input_svg,
            experiment_name=args.experiment_name,
            output_dir=args.output_dir,
            max_iterations=args.iterations,
            satisfaction_threshold=args.threshold,
            api_key=args.api_key
        )
        
        if result["success"]:
            print("\n=== IMPROVEMENT WORKFLOW COMPLETED SUCCESSFULLY ===")
            print(f"Final SVG: {result['final_svg']}")
            print(f"Workflow Report: {result['report_path']}")
            return 0
        else:
            print(f"\nWorkflow failed: {result.get('error', 'Unknown error')}")
            return 1
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())