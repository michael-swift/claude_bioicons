#!/usr/bin/env python3
"""
Visual Design Loop with Claude API - An iterative system for analyzing and improving SVG visualizations
using Claude Vision API for feedback.

This tool creates a feedback loop between SVG rendering, Claude Vision analysis, and code improvements
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
import datetime

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment variables from {env_file}")
except ImportError:
    pass

from visual_svg_critic import VisualSVGCritic, generate_report
from claude_api import ClaudeAPI, svg_to_png

# Initialize config
DEFAULT_MAX_ITERATIONS = 3
DEFAULT_SATISFACTION_THRESHOLD = 85  # 0-100 score

class VisualDesignLoopWithAPI:
    """
    Manages the iterative process between SVG generation and Claude Vision API feedback.
    """
    
    def __init__(self, input_svg_path, api_key=None, output_dir=None, max_iterations=DEFAULT_MAX_ITERATIONS, 
                 satisfaction_threshold=DEFAULT_SATISFACTION_THRESHOLD):
        """
        Initialize the design loop with configuration parameters.
        
        Args:
            input_svg_path: Path to initial SVG file
            api_key: Claude API key (defaults to ANTHROPIC_API_KEY env var)
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
            self.output_dir = f"{base_name}_api_iterations"
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set the current SVG path (don't copy if it's already in the output dir)
        self.current_svg_path = os.path.join(self.output_dir, os.path.basename(input_svg_path))
        if os.path.abspath(input_svg_path) != os.path.abspath(self.current_svg_path):
            shutil.copy(input_svg_path, self.current_svg_path)
        
        # Initialize history
        self.history = []
        
        # Initialize Claude API
        try:
            self.claude_api = ClaudeAPI(api_key)
            print("Successfully initialized Claude API")
        except ValueError as e:
            print(f"Warning: {str(e)}")
            print("Will use local SVG critic as fallback")
            self.claude_api = None
    
    def _has_claude_api(self):
        """Check if Claude API is available and properly initialized."""
        return self.claude_api is not None
    
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
            
            # Step 1: Evaluate current SVG with Claude Vision API (or local fallback)
            print(f"Evaluating: {self.current_svg_path}")
            
            try:
                if self._has_claude_api():
                    print("Using Claude Vision API for analysis...")
                    feedback = self._evaluate_with_claude()
                else:
                    print("Using local SVG critic for analysis (Claude API not available)...")
                    critic = VisualSVGCritic(self.current_svg_path)
                    feedback = critic.evaluate()
                
                current_score = feedback.get('overall_score', 50)  # Default score if not present
            except Exception as e:
                print(f"ERROR: Evaluation failed - {str(e)}")
                raise Exception(f"Design loop failed: {str(e)}")
            
            # Generate suggestions (use local method regardless of API usage)
            if self._has_claude_api():
                suggestions = self._extract_suggestions_from_claude(feedback)
            else:
                critic = VisualSVGCritic(self.current_svg_path)
                suggestions = critic.suggest_improvements(feedback)
            
            # Record history
            self.history.append({
                'iteration': iteration,
                'svg_path': self.current_svg_path,
                'score': current_score,
                'feedback': feedback,
                'suggestions': suggestions,
                'timestamp': datetime.datetime.now().isoformat(),
                'used_api': self._has_claude_api()
            })
            
            # Save evaluation report
            report_path = os.path.join(self.output_dir, f"evaluation_{iteration}.md")
            
            if self._has_claude_api():
                with open(report_path, 'w') as f:
                    f.write(f"# Claude Vision API Analysis - Iteration {iteration}\n\n")
                    f.write(feedback['analysis'])
            else:
                report = generate_report(feedback, suggestions)
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
            
            if self._has_claude_api():
                # Use Claude API for sophisticated improvements
                self._improve_with_claude(improved_svg_path)
            else:
                # Use simpler automated improvements
                critic = VisualSVGCritic(self.current_svg_path)
                critic._apply_improvements(self.current_svg_path, feedback, improved_svg_path)
            
            # Update current SVG path for next iteration
            self.current_svg_path = improved_svg_path
        
        # Create final summary
        self._create_summary()
        
        return self.current_svg_path, self.history[-1]['feedback']
    
    def _evaluate_with_claude(self):
        """
        Send SVG to Claude Vision API for evaluation.
        
        Returns:
            Feedback dictionary from Claude
            
        Raises:
            Exception: If PNG conversion or API request fails
        """
        # Convert SVG to PNG for Claude Vision
        png_path = os.path.join(self.output_dir, f"{Path(self.current_svg_path).stem}_render.png")
        
        # This will raise an exception if conversion fails
        svg_to_png(self.current_svg_path, png_path)
        
        # Verify PNG was created successfully
        if not os.path.exists(png_path) or os.path.getsize(png_path) == 0:
            raise Exception("PNG conversion failed or produced empty file")
            
        # Prepare prompt for SVG design critique
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
        
        # Call Claude API
        result = self.claude_api.analyze_image(png_path, prompt)
        
        if not result.get('success', False):
            error_msg = result.get('error', 'Unknown error')
            raise Exception(f"Claude API analysis failed: {error_msg}")
        
        # Extract score from analysis text
        analysis = result['analysis']
        score = self._extract_score_from_analysis(analysis)
        
        return {
            'analysis': analysis,
            'overall_score': score,
            'source': 'claude_api',
            'raw_response': result.get('raw_response')
        }
    
    def _extract_score_from_analysis(self, analysis):
        """
        Extract numerical score from Claude's analysis text.
        
        Args:
            analysis: Text of Claude's analysis
            
        Returns:
            Score as integer (0-100), or default 50 if not found
        """
        import re
        
        # Look for pattern like "OVERALL SCORE: 75/100"
        match = re.search(r'OVERALL SCORE:\s*(\d+)/100', analysis)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        
        # If not found, try to infer from text sentiment
        positive_indicators = ['excellent', 'great', 'good', 'strong', 'effective']
        negative_indicators = ['poor', 'weak', 'confusing', 'cluttered', 'inconsistent']
        
        positive_count = sum(1 for word in positive_indicators if word in analysis.lower())
        negative_count = sum(1 for word in negative_indicators if word in analysis.lower())
        
        # Simple sentiment score calculation
        total = positive_count + negative_count
        if total > 0:
            sentiment_score = (positive_count / total) * 100
            return round(sentiment_score)
        
        # Default score if nothing else works
        return 50
    
    def _extract_suggestions_from_claude(self, feedback):
        """
        Extract structured suggestions from Claude's free-text analysis.
        
        Args:
            feedback: Feedback dictionary from Claude with 'analysis' key
            
        Returns:
            List of suggestion dictionaries
        """
        import re
        
        analysis = feedback.get('analysis', '')
        suggestions = []
        
        # Look for suggestions section
        suggestion_section_match = re.search(r'IMPROVEMENT SUGGESTIONS:(.*?)($|(?=^\w+:))', 
                                            analysis, re.MULTILINE | re.DOTALL)
        
        if suggestion_section_match:
            suggestion_text = suggestion_section_match.group(1).strip()
            
            # Match numbered suggestions like "1. Fix this" or "1) Fix this"
            suggestion_matches = re.finditer(r'(\d+)[\.\)]\s*([^\n]+)', suggestion_text)
            
            for match in suggestion_matches:
                number = match.group(1)
                text = match.group(2).strip()
                
                suggestions.append({
                    'title': f"Suggestion {number}",
                    'description': text,
                    'type': self._categorize_suggestion(text)
                })
        
        # If no structured suggestions found, try to extract from general text
        if not suggestions:
            # Look for phrases like "should improve X" or "needs better Y"
            improvement_phrases = [
                r'should (improve|enhance|fix|address) ([^\.]+)',
                r'needs (better|improved|more|clearer) ([^\.]+)',
                r'(consider|try) ([^\.]+)',
                r'(recommend|suggest) ([^\.]+)'
            ]
            
            for phrase in improvement_phrases:
                matches = re.finditer(phrase, analysis, re.IGNORECASE)
                for i, match in enumerate(matches, 1):
                    action = match.group(1)
                    target = match.group(2).strip()
                    
                    suggestions.append({
                        'title': f"{action.capitalize()} {target}",
                        'description': f"{action.capitalize()} {target} for better design",
                        'type': self._categorize_suggestion(target)
                    })
                    
                    # Limit to 5 suggestions
                    if len(suggestions) >= 5:
                        break
        
        return suggestions
    
    def _categorize_suggestion(self, text):
        """Categorize a suggestion based on its text content."""
        text = text.lower()
        
        if any(word in text for word in ['color', 'palette', 'hue', 'contrast']):
            return 'color_harmony'
        elif any(word in text for word in ['layout', 'position', 'alignment', 'distribute']):
            return 'layout'
        elif any(word in text for word in ['text', 'font', 'readable', 'legible']):
            return 'readability'
        elif any(word in text for word in ['hierarchy', 'emphasis', 'prominence']):
            return 'visual_hierarchy'
        else:
            return 'general'
    
    def _improve_with_claude(self, output_path):
        """
        Use Claude API to generate sophisticated improvements.
        
        Args:
            output_path: Path to save the improved SVG
        """
        # Read SVG code
        with open(self.current_svg_path, 'r') as f:
            svg_code = f.read()
        
        # Get latest feedback
        latest_feedback = self.history[-1]['feedback']
        
        # Call Claude API
        result = self.claude_api.improve_svg(svg_code, latest_feedback)
        
        if not result.get('success', False):
            print(f"Warning: Claude API improvement failed: {result.get('error', 'Unknown error')}")
            print("Falling back to automated improvements...")
            critic = VisualSVGCritic(self.current_svg_path)
            critic._apply_improvements(self.current_svg_path, latest_feedback, output_path)
            return
        
        # Save improved SVG
        with open(output_path, 'w') as f:
            f.write(result['improved_svg'])
            
        print(f"Saved Claude-improved SVG to: {output_path}")
    
    def _create_summary(self):
        """Create a summary of the iterations and improvements."""
        summary = {
            'input_svg': self.input_svg_path,
            'output_dir': self.output_dir,
            'iterations_count': len(self.history),
            'final_score': self.history[-1]['score'],
            'final_svg': self.current_svg_path,
            'iteration_scores': [iter_data['score'] for iter_data in self.history],
            'used_claude_api': [iter_data.get('used_api', False) for iter_data in self.history]
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
        html.append("    <title>Claude API SVG Design Loop - Progress Report</title>")
        html.append("    <style>")
        html.append("        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }")
        html.append("        h1, h2 { color: #333; }")
        html.append("        .iteration { border: 1px solid #ddd; margin-bottom: 30px; padding: 20px; border-radius: 5px; }")
        html.append("        .iteration-header { display: flex; justify-content: space-between; align-items: center; }")
        html.append("        .score { font-size: 24px; font-weight: bold; color: #19aeff; }")
        html.append("        .api-badge { background-color: #5dbb63; color: white; padding: 5px 10px; border-radius: 12px; font-size: 12px; }")
        html.append("        .local-badge { background-color: #ffc022; color: white; padding: 5px 10px; border-radius: 12px; font-size: 12px; }")
        html.append("        .svg-container { margin: 20px 0; border: 1px dashed #ccc; padding: 10px; }")
        html.append("        .suggestion { background-color: #f8f9fa; padding: 10px; margin: 5px 0; border-left: 4px solid #ffc022; }")
        html.append("        .issue { background-color: #ffebee; padding: 10px; margin: 5px 0; border-left: 4px solid #ff4141; }")
        html.append("        .metrics { display: flex; flex-wrap: wrap; gap: 20px; margin: 20px 0; }")
        html.append("        .metric-card { border: 1px solid #eee; padding: 15px; border-radius: 5px; min-width: 200px; }")
        html.append("        .metric-title { font-weight: bold; margin-bottom: 10px; }")
        html.append("        .metric-value { font-size: 20px; color: #333; }")
        html.append("        .progress-chart { width: 100%; height: 200px; margin: 20px 0; background-color: #f8f9fa; padding: 10px; }")
        html.append("        .analysis { white-space: pre-wrap; background-color: #f9f9f9; padding: 15px; border-left: 4px solid #19aeff; }")
        html.append("    </style>")
        html.append("    <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>")
        html.append("</head>")
        html.append("<body>")
        html.append(f"    <h1>Claude API SVG Design Loop - Progress Report</h1>")
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
            used_api = iteration_data.get('used_api', False)
            
            html.append(f"    <div class='iteration'>")
            html.append(f"        <div class='iteration-header'>")
            html.append(f"            <h2>Iteration {iteration}")
            html.append(f"            <span class='{('api-badge' if used_api else 'local-badge')}'>{('Claude API' if used_api else 'Local Analysis')}</span></h2>")
            html.append(f"            <div class='score'>{score}/100</div>")
            html.append(f"        </div>")
            
            # SVG
            svg_filename = os.path.basename(iteration_data['svg_path'])
            png_filename = os.path.splitext(svg_filename)[0] + "_render.png"
            
            html.append(f"        <div class='svg-container'>")
            html.append(f"            <h3>SVG: {svg_filename}</h3>")
            
            # Show both rendered PNG and SVG
            if os.path.exists(os.path.join(self.output_dir, png_filename)):
                html.append(f"            <div style='display: flex; gap: 20px;'>")
                html.append(f"                <div style='flex: 1;'>")
                html.append(f"                    <p><strong>Rendered PNG:</strong></p>")
                html.append(f"                    <img src='{png_filename}' alt='Rendered SVG' style='max-width: 100%; height: auto;'/>")
                html.append(f"                </div>")
                html.append(f"                <div style='flex: 1;'>")
                html.append(f"                    <p><strong>Original SVG:</strong></p>")
                html.append(f"                    <object data='{svg_filename}' type='image/svg+xml' width='100%' height='400px'></object>")
                html.append(f"                </div>")
                html.append(f"            </div>")
            else:
                html.append(f"            <object data='{svg_filename}' type='image/svg+xml' width='100%' height='400px'></object>")
            
            html.append(f"        </div>")
            
            # Analysis
            if used_api:
                html.append(f"        <h3>Claude API Analysis</h3>")
                html.append(f"        <div class='analysis'>{feedback['analysis']}</div>")
            else:
                # Element distribution if using local critic
                if 'visual_feedback' in feedback:
                    html.append(f"        <h3>Element Distribution</h3>")
                    html.append(f"        <div class='metrics'>")
                    for region, count in feedback['visual_feedback']['elements_by_region'].items():
                        html.append(f"            <div class='metric-card'>")
                        html.append(f"                <div class='metric-title'>{region}</div>")
                        html.append(f"                <div class='metric-value'>{count} elements</div>")
                        html.append(f"            </div>")
                    html.append(f"        </div>")
                
                # Issues list if using local critic
                if 'all_issues' in feedback and feedback['all_issues']:
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
    parser = argparse.ArgumentParser(
        description="Visual SVG Design Loop with Claude API - Vision-based iterative SVG improvement"
    )
    parser.add_argument("svg_path", help="Path to the input SVG file")
    parser.add_argument("--output-dir", "-o", help="Directory to store iterations and results")
    parser.add_argument("--iterations", "-i", type=int, default=DEFAULT_MAX_ITERATIONS,
                       help=f"Maximum number of improvement iterations (default: {DEFAULT_MAX_ITERATIONS})")
    parser.add_argument("--threshold", "-t", type=int, default=DEFAULT_SATISFACTION_THRESHOLD,
                       help=f"Score threshold to stop iterations (0-100, default: {DEFAULT_SATISFACTION_THRESHOLD})")
    parser.add_argument("--api-key", "-k", help="Claude API key (defaults to ANTHROPIC_API_KEY env var)")
    parser.add_argument("--local-only", "-l", action="store_true",
                       help="Use only local analysis, even if API key is available")
    args = parser.parse_args()
    
    try:
        # Verify the SVG exists
        if not os.path.isfile(args.svg_path):
            print(f"Error: SVG file not found at {args.svg_path}")
            return 1
        
        # Check API key if not using local-only mode
        api_key = None
        if not args.local_only:
            api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                print("Warning: No API key provided. Either set ANTHROPIC_API_KEY environment variable")
                print("or provide with --api-key parameter. Will use local SVG critic instead.")
        
        # Initialize and run the design loop
        design_loop = VisualDesignLoopWithAPI(
            args.svg_path,
            api_key=api_key,
            output_dir=args.output_dir,
            max_iterations=args.iterations,
            satisfaction_threshold=args.threshold
        )
        
        final_svg, final_feedback = design_loop.run()
        
        print("\n--- Final Results ---")
        print(f"Final SVG: {final_svg}")
        print(f"Final Score: {final_feedback.get('overall_score', '(not available)')}/100")
        print(f"Progress Report: {os.path.join(design_loop.output_dir, 'progress_report.html')}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())