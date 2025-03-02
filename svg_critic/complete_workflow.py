#!/usr/bin/env python3
"""
Complete SVG Design Workflow - From text prompt to optimized SVG

This script combines SVG generation from text prompts with iterative design improvement
using Claude's vision API, creating a full end-to-end workflow.
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
import datetime
import shutil

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

from svg_generator import SVGGenerator
from visual_design_loop_with_api import VisualDesignLoopWithAPI


class CompleteWorkflow:
    """
    Manages the complete SVG design workflow from text prompt to optimized SVG.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the workflow manager.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY environment variable)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not provided. Either pass api_key parameter or set ANTHROPIC_API_KEY environment variable."
            )
        
        # Initialize components
        self.generator = SVGGenerator(api_key=self.api_key)
    
    def run_workflow(self, prompt, output_dir=None, experiment_name=None, max_iterations=3, satisfaction_threshold=85):
        """
        Run the complete workflow from prompt to optimized SVG.
        
        Args:
            prompt: Text prompt describing the desired diagram
            output_dir: Directory to save all outputs (default: creates timestamped directory)
            experiment_name: Name of this experiment (default: derived from prompt)
            max_iterations: Maximum number of improvement iterations
            satisfaction_threshold: Score threshold to stop iterations (0-100)
            
        Returns:
            Dictionary with workflow results
        """
        start_time = time.time()
        
        # Create experiment name if not provided
        if not experiment_name:
            # Extract first 5 words from prompt for a concise name
            words = prompt.split()[:5]
            experiment_name = "_".join(words).lower()
            # Remove special characters for filename safety
            experiment_name = "".join(c if c.isalnum() or c == "_" else "_" for c in experiment_name)
            # Limit length
            experiment_name = experiment_name[:50]
        
        # Create output directory with experiment name
        if not output_dir:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"experiment_{experiment_name}_{timestamp}"
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Create experiment documentation
        experiment_doc = {
            "experiment_name": experiment_name,
            "prompt": prompt,
            "timestamp": datetime.datetime.now().isoformat(),
            "max_iterations": max_iterations,
            "satisfaction_threshold": satisfaction_threshold,
            "output_directory": output_dir
        }
        
        # Save experiment documentation
        experiment_doc_path = os.path.join(output_dir, "experiment_details.json")
        with open(experiment_doc_path, "w") as f:
            json.dump(experiment_doc, f, indent=2)
        
        # Define subdirectories with experiment name
        generation_dir = os.path.join(output_dir, "1_generation")
        improvement_dir = os.path.join(output_dir, "2_improvement")
        
        # Step 1: Generate initial SVG from prompt
        print(f"\n=== STEP 1: GENERATING SVG FROM PROMPT ===")
        print(f"Experiment: {experiment_name}")
        
        os.makedirs(generation_dir, exist_ok=True)
        
        generation_result = self.generator.generate_svg(
            prompt,
            output_dir=generation_dir,
            svg_name=f"{experiment_name}_initial"
        )
        
        if not generation_result["success"]:
            return {
                "success": False,
                "error": f"SVG generation failed: {generation_result.get('error', 'Unknown error')}"
            }
        
        initial_svg_path = generation_result["svg_path"]
        
        # Step 2: Improve the SVG through iterative design loop
        print("\n=== STEP 2: IMPROVING SVG DESIGN ===")
        
        os.makedirs(improvement_dir, exist_ok=True)
        
        # Copy the initial SVG to the improvement directory with a different name
        initial_filename = os.path.basename(initial_svg_path)
        initial_copy_path = os.path.join(improvement_dir, initial_filename)
        if initial_svg_path != initial_copy_path:  # Only copy if not the same file
            shutil.copy(initial_svg_path, initial_copy_path)
        
        # Run the design loop
        design_loop = VisualDesignLoopWithAPI(
            initial_copy_path,
            api_key=self.api_key,
            output_dir=improvement_dir,
            max_iterations=max_iterations,
            satisfaction_threshold=satisfaction_threshold
        )
        
        try:
            final_svg, final_feedback = design_loop.run()
            final_score = final_feedback.get('overall_score', 0)
            
            # Step 3: Create a summary report
            print("\n=== STEP 3: CREATING WORKFLOW SUMMARY ===")
            
            # Create workflow summary
            summary = {
                "prompt": prompt,
                "initial_svg": initial_svg_path,
                "final_svg": final_svg,
                "final_score": final_score,
                "initial_prompt_path": generation_result["prompt_path"],
                "enhanced_prompt_path": generation_result["metadata_path"],
                "improvement_report": os.path.join(improvement_dir, "progress_report.html"),
                "total_time_seconds": time.time() - start_time,
                "timestamp": datetime.datetime.now().isoformat(),
                "improvement_iterations": len(design_loop.history)
            }
            
            # Save summary to JSON
            summary_path = os.path.join(output_dir, "workflow_summary.json")
            with open(summary_path, "w") as f:
                json.dump(summary, f, indent=2, default=str)
            
            # Create a markdown report
            report_path = os.path.join(output_dir, "workflow_report.md")
            self._create_markdown_report(summary, report_path)
            
            return {
                "success": True,
                "summary": summary,
                "summary_path": summary_path,
                "report_path": report_path,
                "final_svg": final_svg,
                "initial_svg": initial_svg_path,
                "progress_report": os.path.join(improvement_dir, "progress_report.html")
            }
            
        except Exception as e:
            error_message = f"Design improvement failed: {str(e)}"
            print(f"Error: {error_message}")
            
            return {
                "success": False,
                "error": error_message,
                "initial_svg": initial_svg_path
            }
    
    def _create_markdown_report(self, summary, report_path):
        """
        Create a markdown report of the workflow.
        
        Args:
            summary: Workflow summary dictionary
            report_path: Path to save the report
        """
        # Extract experiment name from directory if available
        experiment_name = "Unnamed Experiment"
        output_dir = os.path.dirname(report_path)
        experiment_doc_path = os.path.join(output_dir, "experiment_details.json")
        
        if os.path.exists(experiment_doc_path):
            try:
                with open(experiment_doc_path, 'r') as f:
                    experiment_details = json.load(f)
                    experiment_name = experiment_details.get('experiment_name', experiment_name)
            except:
                pass
        
        # Create report
        report_lines = [
            f"# SVG Design Experiment: {experiment_name}",
            "",
            f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Experiment Overview",
            "",
            "This experiment tests the SVG generation and improvement workflow, processing a text prompt through multiple stages:",
            "1. Initial SVG creation from text prompt",
            "2. Visual evaluation and automated critique",
            "3. Iterative improvement based on feedback",
            "",
            "## Original Prompt",
            "",
            f"```\n{summary['prompt']}\n```",
            "",
            "## Workflow Steps",
            "",
            "### 1. Initial SVG Generation",
            "",
            f"* Initial SVG: [{Path(summary['initial_svg']).name}]({summary['initial_svg']})",
            f"* Original Prompt: [{Path(summary['initial_prompt_path']).name}]({summary['initial_prompt_path']})",
            f"* Enhanced Prompt: [{Path(summary['enhanced_prompt_path']).name}]({summary['enhanced_prompt_path']})",
            "",
            "### 2. Iterative Design Improvement",
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
            f"python complete_workflow.py \"$PROMPT\" --experiment-name \"{experiment_name}\" --iterations {summary.get('improvement_iterations', 3)}",
            f"```",
            "",
            "Where $PROMPT is the original text prompt for the experiment."
        ]
        
        with open(report_path, "w") as f:
            f.write("\n".join(report_lines))


def main():
    """Main function to parse arguments and run the workflow."""
    parser = argparse.ArgumentParser(
        description="Complete SVG Design Workflow - From text prompt to optimized SVG"
    )
    parser.add_argument(
        "prompt", 
        help="Text prompt describing the desired diagram"
    )
    parser.add_argument(
        "--output-dir", "-o", 
        help="Directory to save all outputs (default: creates timestamped directory)"
    )
    parser.add_argument(
        "--experiment-name", "-e",
        help="Name of this experiment (default: derived from prompt)"
    )
    parser.add_argument(
        "--iterations", "-i", 
        type=int, 
        default=3,
        help="Maximum number of improvement iterations (default: 3)"
    )
    parser.add_argument(
        "--threshold", "-t", 
        type=int, 
        default=85,
        help="Score threshold to stop iterations (0-100, default: 85)"
    )
    parser.add_argument(
        "--api-key", "-k", 
        help="Claude API key (defaults to ANTHROPIC_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize workflow
        workflow = CompleteWorkflow(api_key=args.api_key)
        
        # Run workflow
        result = workflow.run_workflow(
            args.prompt,
            output_dir=args.output_dir,
            experiment_name=args.experiment_name,
            max_iterations=args.iterations,
            satisfaction_threshold=args.threshold
        )
        
        if result["success"]:
            print("\n=== WORKFLOW COMPLETED SUCCESSFULLY ===")
            print(f"Initial SVG: {result['initial_svg']}")
            print(f"Final SVG: {result['final_svg']}")
            print(f"Progress Report: {result['progress_report']}")
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