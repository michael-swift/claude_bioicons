"""
Claude API Integration - Module for interacting with Claude Vision API

This module handles the secure connection to Claude's API for analyzing and improving SVGs.
"""

import os
import base64
import json
import requests
from pathlib import Path
import time
import subprocess
import tempfile

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

# API Constants
DEFAULT_MODEL = "claude-3-7-sonnet-20250219"  # Use latest Sonnet model
DEFAULT_MAX_TOKENS = 1000
API_ENDPOINT = "https://api.anthropic.com/v1/messages"

class ClaudeAPI:
    """
    Handles interactions with the Claude API for image analysis and text generation.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the Claude API client.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY environment variable)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not provided. Either pass api_key parameter or set ANTHROPIC_API_KEY environment variable."
            )
    
    def analyze_image(self, image_path, prompt=None, model=DEFAULT_MODEL, max_tokens=DEFAULT_MAX_TOKENS):
        """
        Send an image to Claude for analysis.
        
        Args:
            image_path: Path to the image file
            prompt: Prompt to guide Claude's analysis
            model: Claude model to use
            max_tokens: Maximum tokens for response
            
        Returns:
            Claude's analysis of the image
        """
        # Ensure image exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Prepare default prompt if not provided
        if not prompt:
            prompt = """
            You are a professional graphic designer and visual design critic. 
            Analyze this SVG diagram with a focus on design principles:
            
            1. Visual Balance: How well are elements distributed across the diagram?
            2. Color Harmony: Are colors consistent and harmonious?
            3. Visual Hierarchy: Is there clear distinction between primary and secondary elements?
            4. Readability: Are text elements readable and appropriately sized?
            5. Flow: Does the diagram guide the eye in a logical way?
            
            Provide specific, actionable feedback for improving the design. Be critical but constructive.
            Focus on issues that would affect audience comprehension and perception.
            """
        
        # Encode image
        with open(image_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode("utf-8")
            mime_type = "image/png"  # Assuming PNG format
        
        # Prepare request
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": img_data
                            }
                        }
                    ]
                }
            ]
        }
        
        # Send request to Claude API
        try:
            response = requests.post(API_ENDPOINT, headers=headers, json=data)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            result = response.json()
            return {
                "success": True,
                "analysis": result["content"][0]["text"],
                "model": result.get("model", model),
                "raw_response": result
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"API request failed: {str(e)}",
                "raw_error": str(e)
            }
    
    def improve_svg(self, svg_code, feedback, model=DEFAULT_MODEL, max_tokens=4000):
        """
        Ask Claude to improve an SVG based on feedback.
        
        Args:
            svg_code: Original SVG code
            feedback: Feedback from visual analysis
            model: Claude model to use
            max_tokens: Maximum tokens for response
            
        Returns:
            Improved SVG code
        """
        # Prepare prompt
        prompt = f"""
        You are an expert SVG coder. I need you to improve this SVG based on design feedback.
        
        DESIGN FEEDBACK:
        {feedback["analysis"]}
        
        ORIGINAL SVG CODE:
        ```xml
        {svg_code}
        ```
        
        Please improve this SVG to address the issues in the feedback. Return ONLY the improved
        SVG code without any explanation. The SVG should begin with <?xml version="1.0" encoding="UTF-8"?>
        and should be a complete valid SVG document.
        
        Focus on maintaining the original design intent while making these improvements:
        1. Fix any layout or balance issues
        2. Standardize colors to the Bioicons palette: #19aeff, #ff4141, #ffc022, #5dbb63, #333333
        3. Improve text readability
        4. Enhance visual hierarchy
        
        ONLY return the improved SVG code without any wrapper text.
        """
        
        # Prepare request
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        # Send request to Claude API
        try:
            response = requests.post(API_ENDPOINT, headers=headers, json=data)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            result = response.json()
            improved_svg = result["content"][0]["text"]
            
            # Remove any markdown code blocks if present
            improved_svg = improved_svg.replace("```xml", "").replace("```svg", "").replace("```", "").strip()
            
            # Ensure it starts with XML declaration
            if not improved_svg.startswith("<?xml"):
                improved_svg = '<?xml version="1.0" encoding="UTF-8"?>\n' + improved_svg
            
            return {
                "success": True,
                "improved_svg": improved_svg,
                "model": result.get("model", model)
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"API request failed: {str(e)}",
                "raw_error": str(e)
            }


def svg_to_png(svg_path, output_path=None, width=1200, height=None):
    """
    Convert SVG to PNG using rsvg-convert.
    
    Args:
        svg_path: Path to SVG file
        output_path: Path for output PNG (default: based on SVG name)
        width: Output width in pixels
        height: Output height in pixels (default: proportional to width)
        
    Returns:
        Path to the generated PNG
    
    Raises:
        Exception: If conversion fails
    """
    # Verify input file exists
    if not os.path.exists(svg_path):
        raise FileNotFoundError(f"SVG file not found: {svg_path}")
    
    # Set default output path if not provided
    if not output_path:
        output_path = os.path.splitext(svg_path)[0] + ".png"
    
    # Build command
    cmd = ["rsvg-convert", "-o", output_path]
    if width:
        cmd.extend(["-w", str(width)])
    if height:
        cmd.extend(["-h", str(height)])
    cmd.append(svg_path)
    
    try:
        # Run the conversion
        print(f"Running conversion command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Verify the output exists and is not empty
        if not os.path.exists(output_path):
            raise Exception("Conversion failed: Output file does not exist")
            
        if os.path.getsize(output_path) == 0:
            raise Exception("Conversion failed: Output file is empty")
            
        print(f"SVG successfully converted to PNG: {output_path}")
        return output_path
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise Exception(f"SVG to PNG conversion failed: {error_msg}")
        
    except Exception as e:
        raise Exception(f"SVG to PNG conversion failed: {str(e)}")


if __name__ == "__main__":
    # Simple test code when run directly
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude API tools for SVG analysis")
    parser.add_argument("--convert", help="Convert SVG to PNG")
    parser.add_argument("--output", help="Output path for conversion")
    parser.add_argument("--analyze", help="Analyze image with Claude")
    parser.add_argument("--width", type=int, default=1200, help="Width for PNG conversion")
    
    args = parser.parse_args()
    
    if args.convert:
        output = args.output or f"{os.path.splitext(args.convert)[0]}.png"
        png_path = svg_to_png(args.convert, output, width=args.width)
        print(f"Converted SVG to PNG: {png_path}")
    
    if args.analyze:
        # Check for API key
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("Error: ANTHROPIC_API_KEY environment variable not set")
            sys.exit(1)
            
        # Initialize API
        api = ClaudeAPI()
        
        # Analyze image
        result = api.analyze_image(args.analyze)
        
        if result["success"]:
            print("\n" + "="*80)
            print("Claude's Analysis:")
            print("="*80)
            print(result["analysis"])
        else:
            print(f"Error: {result['error']}")
            sys.exit(1)