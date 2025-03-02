#!/usr/bin/env python3
"""
SVG Design Loop - An iterative system for analyzing and improving SVG visualizations.

This tool creates a feedback loop between SVG Claude (code generation) and 
Designer Claude (visual assessment) to produce optimized scientific illustrations.
"""

import os
import sys
import json
import argparse
import shutil
import xml.etree.ElementTree as ET
from svg_critic import SVGCritic, generate_human_readable_report

# Initialize config
DEFAULT_MAX_ITERATIONS = 3
DEFAULT_SATISFACTION_THRESHOLD = 85  # 0-100 score

class SVGDesignLoop:
    """
    Manages the iterative process between SVG generation and design evaluation.
    """
    
    def __init__(self, input_svg_path, output_dir=None, max_iterations=DEFAULT_MAX_ITERATIONS, 
                 satisfaction_threshold=DEFAULT_SATISFACTION_THRESHOLD):
        """
        Initialize the design loop with configuration parameters.
        
        Args:
            input_svg_path: Path to initial SVG file
            output_dir: Directory to store intermediate and final SVGs
            max_iterations: Maximum number of improvement iterations
            satisfaction_threshold: Score threshold to stop iterations (0-100)
        """
        self.input_svg_path = input_svg_path
        self.max_iterations = max_iterations
        self.satisfaction_threshold = satisfaction_threshold
        
        # Set up output directory
        if output_dir:
            self.output_dir = output_dir
        else:
            base_name = os.path.splitext(os.path.basename(input_svg_path))[0]
            self.output_dir = f"{base_name}_iterations"
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Copy input SVG to output directory
        self.current_svg_path = os.path.join(self.output_dir, os.path.basename(input_svg_path))
        shutil.copy(input_svg_path, self.current_svg_path)
        
        # Initialize history
        self.history = []
    
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
            
            # Step 1: Evaluate current SVG with Designer Claude
            print(f"Evaluating: {self.current_svg_path}")
            evaluation = self._evaluate_svg()
            current_score = evaluation['overall_score']
            
            # Record history
            self.history.append({
                'iteration': iteration,
                'svg_path': self.current_svg_path,
                'score': current_score,
                'evaluation': evaluation
            })
            
            # Print summary of evaluation
            report = generate_human_readable_report(evaluation)
            print(f"\nEvaluation Score: {current_score}/100")
            
            # Check if we've reached satisfaction threshold
            if current_score >= self.satisfaction_threshold:
                print(f"\nSatisfaction threshold reached: {current_score} >= {self.satisfaction_threshold}")
                break
                
            # Check if this is the last iteration
            if iteration == self.max_iterations:
                print("\nReached maximum iterations.")
                break
                
            # Step 2: Generate improved SVG with SVG Claude
            print("\nGenerating improvements...")
            self._improve_svg(evaluation, iteration)
        
        # Create final summary
        self._create_summary()
        
        return self.current_svg_path, self.history[-1]['evaluation']
    
    def _evaluate_svg(self):
        """
        Evaluate the current SVG using Designer Claude (SVGCritic).
        
        Returns:
            Evaluation dictionary
        """
        critic = SVGCritic(self.current_svg_path)
        evaluation = critic.evaluate()
        
        # Save evaluation report
        report_path = f"{self.current_svg_path}.evaluation.json"
        with open(report_path, "w") as f:
            json.dump(evaluation, f, indent=2)
        
        # Save human readable report
        report = generate_human_readable_report(evaluation)
        report_path = f"{self.current_svg_path}.report.md"
        with open(report_path, "w") as f:
            f.write(report)
        
        return evaluation
    
    def _improve_svg(self, evaluation, iteration):
        """
        Improve the SVG based on evaluation feedback.
        
        Args:
            evaluation: Evaluation dictionary from Designer Claude
            iteration: Current iteration number
        
        Returns:
            Path to improved SVG
        """
        # For this prototype, we'll implement a simple set of automated improvements
        # In a full implementation, this would call Claude API to get more sophisticated changes
        improved_svg_path = os.path.join(
            self.output_dir, 
            f"{os.path.splitext(os.path.basename(self.current_svg_path))[0]}_iter{iteration}.svg"
        )
        
        # Parse the SVG
        tree = ET.parse(self.current_svg_path)
        root = tree.getroot()
        
        # Apply improvements based on evaluation feedback
        self._fix_overlaps(root, evaluation)
        self._improve_layout(root, evaluation)
        self._improve_color_harmony(root, evaluation)
        self._improve_accessibility(root, evaluation)
        
        # Save improved SVG
        tree.write(improved_svg_path)
        
        # Update current SVG path
        self.current_svg_path = improved_svg_path
        
        return improved_svg_path
    
    def _fix_overlaps(self, root, evaluation):
        """Apply fixes for overlapping elements."""
        # In a real implementation, this would be much more sophisticated
        # For now, we'll just move elements slightly
        
        for issue in evaluation['critical_issues']:
            if issue['type'] == 'overlap':
                # Find elements by ID
                elem1_id, elem2_id = issue['elements']
                
                # Find elements in the SVG
                for elem in root.iter():
                    if elem.get('id') == elem1_id:
                        # Move element slightly left and up
                        transform = elem.get('transform', '')
                        if transform:
                            # If there's already a transform, append to it
                            elem.set('transform', f"{transform} translate(-10,-10)")
                        else:
                            # Otherwise create a new transform
                            elem.set('transform', "translate(-10,-10)")
    
    def _improve_layout(self, root, evaluation):
        """Improve layout based on evaluation."""
        # Example: Add a title if missing
        has_title = False
        for elem in root.iter('{http://www.w3.org/2000/svg}text'):
            if elem.get('font-size') and float(elem.get('font-size', '0').replace('px', '')) > 18:
                has_title = True
                break
        
        if not has_title:
            # Create a title element
            title_elem = ET.SubElement(root, '{http://www.w3.org/2000/svg}text')
            title_elem.set('x', str(float(root.get('width', '800')) / 2))
            title_elem.set('y', '30')
            title_elem.set('font-family', 'Arial, sans-serif')
            title_elem.set('font-size', '24')
            title_elem.set('text-anchor', 'middle')
            title_elem.set('fill', '#333')
            title_elem.text = "Diagram Title"
    
    def _improve_color_harmony(self, root, evaluation):
        """Improve color harmony based on evaluation."""
        # Example: Replace non-standard colors with palette colors
        standard_palette = ['#19aeff', '#ff4141', '#ffc022', '#5dbb63', '#333333']
        
        if evaluation['color_harmony']['palette_adherence'] < 70:
            for elem in root.iter():
                if elem.get('fill') and elem.get('fill') not in [*standard_palette, 'none', 'transparent']:
                    # Replace with a standard color
                    elem.set('fill', standard_palette[hash(elem.get('fill')) % len(standard_palette)])
    
    def _improve_accessibility(self, root, evaluation):
        """Improve accessibility based on evaluation."""
        # Example: Increase font size for small text
        if evaluation['accessibility']['font_size_score'] < 80:
            for elem in root.iter('{http://www.w3.org/2000/svg}text'):
                font_size = elem.get('font-size', '12')
                if font_size.isdigit() and int(font_size) < 10:
                    elem.set('font-size', '12')
    
    def _create_summary(self):
        """Create a summary of the iterations and improvements."""
        summary = {
            'input_svg': self.input_svg_path,
            'output_dir': self.output_dir,
            'iterations': self.history,
            'final_score': self.history[-1]['score'],
            'final_svg': self.current_svg_path
        }
        
        summary_path = os.path.join(self.output_dir, "summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
            
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
        html.append("    <title>SVG Design Loop - Progress Report</title>")
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
        html.append("    </style>")
        html.append("</head>")
        html.append("<body>")
        html.append(f"    <h1>SVG Design Loop - Progress Report</h1>")
        html.append(f"    <p>Input SVG: {os.path.basename(self.input_svg_path)}</p>")
        html.append(f"    <p>Final Score: {self.history[-1]['score']}/100</p>")
        
        # Iterations
        for iteration in self.history:
            html.append(f"    <div class='iteration'>")
            html.append(f"        <div class='iteration-header'>")
            html.append(f"            <h2>Iteration {iteration['iteration']}</h2>")
            html.append(f"            <div class='score'>{iteration['score']}/100</div>")
            html.append(f"        </div>")
            
            # SVG
            svg_filename = os.path.basename(iteration['svg_path'])
            html.append(f"        <div class='svg-container'>")
            html.append(f"            <h3>SVG: {svg_filename}</h3>")
            html.append(f"            <object data='{svg_filename}' type='image/svg+xml' width='100%' height='400px'></object>")
            html.append(f"        </div>")
            
            # Metrics
            html.append(f"        <div class='metrics'>")
            
            # Layout balance
            html.append(f"            <div class='metric-card'>")
            html.append(f"                <div class='metric-title'>Layout Balance</div>")
            html.append(f"                <div class='metric-value'>{iteration['evaluation']['layout_assessment']['balance_score']:.1f}/100</div>")
            html.append(f"            </div>")
            
            # Color harmony
            html.append(f"            <div class='metric-card'>")
            html.append(f"                <div class='metric-title'>Color Harmony</div>")
            html.append(f"                <div class='metric-value'>{iteration['evaluation']['color_harmony']['palette_adherence']:.1f}%</div>")
            html.append(f"            </div>")
            
            # Visual hierarchy
            html.append(f"            <div class='metric-card'>")
            html.append(f"                <div class='metric-title'>Visual Hierarchy</div>")
            html.append(f"                <div class='metric-value'>{iteration['evaluation']['visual_hierarchy']['score']}/100</div>")
            html.append(f"            </div>")
            
            # Accessibility
            html.append(f"            <div class='metric-card'>")
            html.append(f"                <div class='metric-title'>Accessibility</div>")
            html.append(f"                <div class='metric-value'>{iteration['evaluation']['accessibility']['score']:.1f}/100</div>")
            html.append(f"            </div>")
            
            html.append(f"        </div>")
            
            # Issues
            if iteration['evaluation']['critical_issues']:
                html.append(f"        <h3>Critical Issues</h3>")
                for issue in iteration['evaluation']['critical_issues']:
                    html.append(f"        <div class='issue'>")
                    html.append(f"            <strong>{issue['severity'].upper()}</strong>: Overlap between elements {' and '.join(issue['elements'])}")
                    html.append(f"        </div>")
            
            # Suggestions
            html.append(f"        <h3>Improvement Suggestions</h3>")
            
            for suggestion in iteration['evaluation']['layout_assessment']['suggestions']:
                html.append(f"        <div class='suggestion'><strong>Layout</strong>: {suggestion}</div>")
                
            for suggestion in iteration['evaluation']['color_harmony']['suggestions']:
                html.append(f"        <div class='suggestion'><strong>Color</strong>: {suggestion}</div>")
                
            for suggestion in iteration['evaluation']['visual_hierarchy']['suggestions']:
                html.append(f"        <div class='suggestion'><strong>Hierarchy</strong>: {suggestion}</div>")
                
            for suggestion in iteration['evaluation']['accessibility']['suggestions']:
                html.append(f"        <div class='suggestion'><strong>Accessibility</strong>: {suggestion}</div>")
            
            html.append(f"    </div>")
        
        html.append("</body>")
        html.append("</html>")
        
        # Write HTML file
        html_path = os.path.join(self.output_dir, "progress_report.html")
        with open(html_path, "w") as f:
            f.write("\n".join(html))


def main():
    """Main function to handle command line arguments and run the design loop."""
    parser = argparse.ArgumentParser(description="SVG Design Loop - Iterative SVG improvement system")
    parser.add_argument("svg_path", help="Path to the input SVG file")
    parser.add_argument("--output-dir", "-o", help="Directory to store iterations and results")
    parser.add_argument("--iterations", "-i", type=int, default=DEFAULT_MAX_ITERATIONS,
                        help=f"Maximum number of improvement iterations (default: {DEFAULT_MAX_ITERATIONS})")
    parser.add_argument("--threshold", "-t", type=int, default=DEFAULT_SATISFACTION_THRESHOLD,
                        help=f"Score threshold to stop iterations (0-100, default: {DEFAULT_SATISFACTION_THRESHOLD})")
    args = parser.parse_args()
    
    try:
        # Initialize and run the design loop
        design_loop = SVGDesignLoop(
            args.svg_path,
            output_dir=args.output_dir,
            max_iterations=args.iterations,
            satisfaction_threshold=args.threshold
        )
        
        final_svg, final_evaluation = design_loop.run()
        
        print("\n--- Final Results ---")
        print(f"Final SVG: {final_svg}")
        print(f"Final Score: {final_evaluation['overall_score']}/100")
        print(f"Progress Report: {os.path.join(design_loop.output_dir, 'progress_report.html')}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())