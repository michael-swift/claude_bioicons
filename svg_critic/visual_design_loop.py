#!/usr/bin/env python3
"""
Visual Design Loop - An iterative system for analyzing and improving SVG visualizations
using vision-based feedback.

This tool creates a feedback loop between SVG rendering, visual analysis, and code improvements
to produce optimized scientific illustrations.
"""

import os
import sys
import json
import argparse
import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess
import datetime
from visual_svg_critic import VisualSVGCritic, MockClaudeAPI, generate_report

# Initialize config
DEFAULT_MAX_ITERATIONS = 3
DEFAULT_SATISFACTION_THRESHOLD = 85  # 0-100 score

class VisualDesignLoop:
    """
    Manages the iterative process between SVG generation and vision-based design evaluation.
    """
    
    def __init__(self, input_svg_path, output_dir=None, max_iterations=DEFAULT_MAX_ITERATIONS, 
                 satisfaction_threshold=DEFAULT_SATISFACTION_THRESHOLD, use_claude_api=False):
        """
        Initialize the design loop with configuration parameters.
        
        Args:
            input_svg_path: Path to initial SVG file
            output_dir: Directory to store intermediate and final SVGs
            max_iterations: Maximum number of improvement iterations
            satisfaction_threshold: Score threshold to stop iterations (0-100)
            use_claude_api: Whether to use Claude API for improvements (mock in this implementation)
        """
        self.input_svg_path = input_svg_path
        self.max_iterations = max_iterations
        self.satisfaction_threshold = satisfaction_threshold
        self.use_claude_api = use_claude_api
        
        # Set up output directory
        if output_dir:
            self.output_dir = output_dir
        else:
            base_name = os.path.splitext(os.path.basename(input_svg_path))[0]
            self.output_dir = f"{base_name}_visual_iterations"
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Copy input SVG to output directory
        self.current_svg_path = os.path.join(self.output_dir, os.path.basename(input_svg_path))
        shutil.copy(input_svg_path, self.current_svg_path)
        
        # Initialize history
        self.history = []
        
        # Initialize Claude API mock
        self.claude_api = MockClaudeAPI()
    
    def run(self):
        """
        Run the design loop for the specified number of iterations or until 
        satisfaction threshold is reached.
        
        Returns:
            Final SVG path and evaluation report
        """
        current_score = 0
        
        for iteration in range(1, self.max_iterations + 1):
            print(f"\n--- Iteration {iteration}/{self.max_iterations} ---")
            
            # Step 1: Evaluate current SVG with visual SVG critic
            print(f"Evaluating: {self.current_svg_path}")
            critic = VisualSVGCritic(self.current_svg_path)
            feedback = critic.evaluate()
            current_score = feedback['overall_score']
            
            # Generate suggestions
            suggestions = critic.suggest_improvements(feedback)
            
            # Record history
            self.history.append({
                'iteration': iteration,
                'svg_path': self.current_svg_path,
                'score': current_score,
                'feedback': feedback,
                'suggestions': suggestions,
                'timestamp': datetime.datetime.now().isoformat()
            })
            
            # Save evaluation report
            report = generate_report(feedback, suggestions)
            report_path = os.path.join(self.output_dir, f"evaluation_{iteration}.md")
            with open(report_path, 'w') as f:
                f.write(report)
            
            print(f"\nEvaluation Score: {current_score}/100")
            
            # Check if we've reached satisfaction threshold
            if current_score >= self.satisfaction_threshold:
                print(f"\nSatisfaction threshold reached: {current_score} >= {self.satisfaction_threshold}")
                break
                
            # Check if this is the last iteration
            if iteration == self.max_iterations:
                print("\nReached maximum iterations.")
                break
                
            # Step 2: Generate improved SVG
            print("\nGenerating improvements...")
            
            # Determine output path for improved SVG
            improved_svg_path = os.path.join(
                self.output_dir, 
                f"{os.path.splitext(os.path.basename(self.current_svg_path))[0]}_iter{iteration}.svg"
            )
            
            if self.use_claude_api:
                # Use Claude API for sophisticated improvements (mock implementation)
                self._improve_with_claude(self.current_svg_path, feedback, improved_svg_path)
            else:
                # Use simpler automated improvements
                self._apply_improvements(self.current_svg_path, feedback, improved_svg_path)
            
            # Update current SVG path for next iteration
            self.current_svg_path = improved_svg_path
        
        # Create final summary
        self._create_summary()
        
        return self.current_svg_path, self.history[-1]['feedback']
    
    def _improve_with_claude(self, svg_path, feedback, output_path):
        """
        Use Claude API to generate sophisticated improvements.
        
        Args:
            svg_path: Path to the SVG file to improve
            feedback: Evaluation feedback
            output_path: Path to save the improved SVG
        """
        # Read SVG code
        with open(svg_path, 'r') as f:
            svg_code = f.read()
        
        # Call Claude API mock
        result = self.claude_api.improve_svg(svg_code, feedback)
        
        if not result.get('success', False):
            print(f"Warning: Claude API improvement failed: {result.get('error', 'Unknown error')}")
            print("Falling back to automated improvements...")
            self._apply_improvements(svg_path, feedback, output_path)
            return
        
        # Save improved SVG
        with open(output_path, 'w') as f:
            f.write(result['improved_svg'])
            
        print(f"Saved Claude-improved SVG to: {output_path}")
        print("Improvements made:")
        for improvement in result.get('improvements', []):
            print(f"- {improvement}")
    
    def _apply_improvements(self, svg_path, feedback, output_path):
        """
        Apply automated improvements based on feedback.
        
        Args:
            svg_path: Path to the SVG file to improve
            feedback: Evaluation feedback
            output_path: Path to save the improved SVG
        """
        # Parse SVG
        namespaces = {
            'svg': 'http://www.w3.org/2000/svg',
            'xlink': 'http://www.w3.org/1999/xlink'
        }
        
        # Register namespaces for ElementTree
        for prefix, uri in namespaces.items():
            ET.register_namespace(prefix, uri)
        
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        improvements_made = []
        
        # Process visual issues
        for issue in feedback['visual_feedback']['visual_issues']:
            if issue['type'] == 'readability':
                # Fix small text
                count = 0
                for elem in root.iter('{http://www.w3.org/2000/svg}text'):
                    font_size = elem.get('font-size', '')
                    try:
                        size = float(''.join(c for c in font_size if c.isdigit() or c == '.'))
                        if size < 10:
                            elem.set('font-size', '12')
                            count += 1
                    except ValueError:
                        pass
                
                if count > 0:
                    improvements_made.append(f"Increased font size for {count} small text elements")
            
            elif issue['type'] == 'balance':
                # This is more complex to fix automatically
                improvements_made.append("Noted visual imbalance issue - would need manual adjustment")
        
        # Process structure issues
        for opp in feedback['improvement_opportunities']:
            if opp['type'] == 'color_standardization':
                # Standardize colors
                standard_palette = ['#19aeff', '#ff4141', '#ffc022', '#5dbb63', '#333333']
                color_changes = {}
                
                for elem in root.iter():
                    fill = elem.get('fill')
                    if fill and fill not in ('none', 'transparent') and fill.lower() not in [c.lower() for c in standard_palette]:
                        # Simple heuristic: replace with a standard color
                        new_color = standard_palette[hash(fill) % len(standard_palette)]
                        elem.set('fill', new_color)
                        color_changes[fill] = new_color
                
                if color_changes:
                    improvements_made.append(f"Standardized {len(color_changes)} colors to Bioicons palette")
        
        # Save improved SVG
        tree.write(output_path)
        
        print(f"Saved improved SVG to: {output_path}")
        print("Improvements made:")
        for improvement in improvements_made:
            print(f"- {improvement}")
    
    def _create_summary(self):
        """Create a summary of the iterations and improvements."""
        summary = {
            'input_svg': self.input_svg_path,
            'output_dir': self.output_dir,
            'iterations_count': len(self.history),
            'final_score': self.history[-1]['score'],
            'final_svg': self.current_svg_path,
            'iteration_scores': [iter_data['score'] for iter_data in self.history]
        }
        
        summary_path = os.path.join(self.output_dir, "summary.json")
        with open(summary_path, "w") as f:
            # Use a custom encoder to handle datetime objects
            json.dump(summary, f, indent=2, default=str)
            
        # Create HTML visualization of progress
        self._create_html_summary()
        
        return summary_path
    
    def _create_html_summary(self):
        """Create an HTML visualization of the design improvement process."""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html lang='en'>")
        html.append("<head>")
        html.append("    <meta charset='UTF-8'>")
        html.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html.append("    <title>Visual SVG Design Loop - Progress Report</title>")
        html.append("    <style>")
        html.append("        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }")
        html.append("        h1, h2 { color: #333; }")
        html.append("        .iteration { border: 1px solid #ddd; margin-bottom: 30px; padding: 20px; border-radius: 5px; }")
        html.append("        .iteration-header { display: flex; justify-content: space-between; align-items: center; }")
        html.append("        .score { font-size: 24px; font-weight: bold; color: #19aeff; }")
        html.append("        .svg-container { margin: 20px 0; border: 1px dashed #ccc; padding: 10px; }")
        html.append("        .suggestion { background-color: #f8f9fa; padding: 10px; margin: 5px 0; border-left: 4px solid #ffc022; }")
        html.append("        .issue { background-color: #ffebee; padding: 10px; margin: 5px 0; border-left: 4px solid #ff4141; }")
        html.append("        .metrics { display: flex; flex-wrap: wrap; gap: 20px; margin: 20px 0; }")
        html.append("        .metric-card { border: 1px solid #eee; padding: 15px; border-radius: 5px; min-width: 200px; }")
        html.append("        .metric-title { font-weight: bold; margin-bottom: 10px; }")
        html.append("        .metric-value { font-size: 20px; color: #333; }")
        html.append("        .progress-chart { width: 100%; height: 200px; margin: 20px 0; background-color: #f8f9fa; padding: 10px; }")
        html.append("    </style>")
        html.append("    <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>")
        html.append("</head>")
        html.append("<body>")
        html.append(f"    <h1>Visual SVG Design Loop - Progress Report</h1>")
        html.append(f"    <p>Input SVG: {os.path.basename(self.input_svg_path)}</p>")
        html.append(f"    <p>Final Score: {self.history[-1]['score']}/100</p>")
        
        # Progress chart
        html.append("    <div class='progress-chart'>")
        html.append("        <canvas id='progressChart'></canvas>")
        html.append("    </div>")
        
        # Chart data
        scores = [iter_data['score'] for iter_data in self.history]
        html.append("    <script>")
        html.append("        const ctx = document.getElementById('progressChart').getContext('2d');")
        html.append("        new Chart(ctx, {")
        html.append("            type: 'line',")
        html.append("            data: {")
        html.append(f"                labels: {list(range(1, len(scores) + 1))},")
        html.append("                datasets: [{")
        html.append("                    label: 'SVG Quality Score',")
        html.append(f"                    data: {scores},")
        html.append("                    backgroundColor: 'rgba(25, 174, 255, 0.2)',")
        html.append("                    borderColor: 'rgba(25, 174, 255, 1)',")
        html.append("                    borderWidth: 2,")
        html.append("                    tension: 0.1")
        html.append("                }]")
        html.append("            },")
        html.append("            options: {")
        html.append("                scales: {")
        html.append("                    y: {")
        html.append("                        beginAtZero: true,")
        html.append("                        max: 100")
        html.append("                    }")
        html.append("                }")
        html.append("            }")
        html.append("        });")
        html.append("    </script>")
        
        # Iterations
        for iteration_data in self.history:
            iteration = iteration_data['iteration']
            score = iteration_data['score']
            feedback = iteration_data['feedback']
            suggestions = iteration_data.get('suggestions', [])
            
            html.append(f"    <div class='iteration'>")
            html.append(f"        <div class='iteration-header'>")
            html.append(f"            <h2>Iteration {iteration}</h2>")
            html.append(f"            <div class='score'>{score}/100</div>")
            html.append(f"        </div>")
            
            # SVG
            svg_filename = os.path.basename(iteration_data['svg_path'])
            html.append(f"        <div class='svg-container'>")
            html.append(f"            <h3>SVG: {svg_filename}</h3>")
            html.append(f"            <object data='{svg_filename}' type='image/svg+xml' width='100%' height='400px'></object>")
            html.append(f"        </div>")
            
            # Element distribution
            html.append(f"        <h3>Element Distribution</h3>")
            html.append(f"        <div class='metrics'>")
            for region, count in feedback['visual_feedback']['elements_by_region'].items():
                html.append(f"            <div class='metric-card'>")
                html.append(f"                <div class='metric-title'>{region}</div>")
                html.append(f"                <div class='metric-value'>{count} elements</div>")
                html.append(f"            </div>")
            html.append(f"        </div>")
            
            # Issues
            if feedback['all_issues']:
                html.append(f"        <h3>Issues</h3>")
                for issue in feedback['all_issues']:
                    html.append(f"        <div class='issue'>")
                    html.append(f"            <strong>{issue['type'].upper()}</strong> ({issue['severity']}): {issue['description']}")
                    html.append(f"        </div>")
            
            # Suggestions
            if suggestions:
                html.append(f"        <h3>Improvement Suggestions</h3>")
                for suggestion in suggestions:
                    html.append(f"        <div class='suggestion'>")
                    html.append(f"            <strong>{suggestion['title']}</strong>: {suggestion['description']}")
                    html.append(f"        </div>")
            
            html.append(f"    </div>")
        
        html.append("</body>")
        html.append("</html>")
        
        # Write HTML file
        html_path = os.path.join(self.output_dir, "progress_report.html")
        with open(html_path, "w") as f:
            f.write("\n".join(html))


def main():
    """Main function to handle command line arguments and run the design loop."""
    parser = argparse.ArgumentParser(description="Visual SVG Design Loop - Vision-based iterative SVG improvement")
    parser.add_argument("svg_path", help="Path to the input SVG file")
    parser.add_argument("--output-dir", "-o", help="Directory to store iterations and results")
    parser.add_argument("--iterations", "-i", type=int, default=DEFAULT_MAX_ITERATIONS,
                        help=f"Maximum number of improvement iterations (default: {DEFAULT_MAX_ITERATIONS})")
    parser.add_argument("--threshold", "-t", type=int, default=DEFAULT_SATISFACTION_THRESHOLD,
                        help=f"Score threshold to stop iterations (0-100, default: {DEFAULT_SATISFACTION_THRESHOLD})")
    parser.add_argument("--use-claude", "-c", action="store_true",
                        help="Use Claude API for improvements (mock implementation)")
    args = parser.parse_args()
    
    try:
        # Verify the SVG exists
        if not os.path.isfile(args.svg_path):
            print(f"Error: SVG file not found at {args.svg_path}")
            return 1
        
        # Initialize and run the design loop
        design_loop = VisualDesignLoop(
            args.svg_path,
            output_dir=args.output_dir,
            max_iterations=args.iterations,
            satisfaction_threshold=args.threshold,
            use_claude_api=args.use_claude
        )
        
        final_svg, final_feedback = design_loop.run()
        
        print("\n--- Final Results ---")
        print(f"Final SVG: {final_svg}")
        print(f"Final Score: {final_feedback['overall_score']}/100")
        print(f"Progress Report: {os.path.join(design_loop.output_dir, 'progress_report.html')}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())