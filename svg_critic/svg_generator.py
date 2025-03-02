#!/usr/bin/env python3
"""
SVG Generator - Module for generating SVG diagrams from text prompts using Claude.

This module handles the generation of initial SVG designs based on text prompts.
"""

import os
import json
import requests
from pathlib import Path
import time
import datetime

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

# API Constants
DEFAULT_MODEL = "claude-3-7-sonnet-20250219"
API_ENDPOINT = "https://api.anthropic.com/v1/messages"

class SVGGenerator:
    """
    Handles generation of SVG diagrams from text prompts using Claude.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the SVG Generator.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY environment variable)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not provided. Either pass api_key parameter or set ANTHROPIC_API_KEY environment variable."
            )
            
    def generate_svg(self, prompt, output_dir=None, svg_name=None, max_tokens=4000):
        """
        Generate an SVG diagram based on a text prompt.
        
        Args:
            prompt: Text prompt describing the desired diagram
            output_dir: Directory to save outputs (default: creates "generated_svgs")
            svg_name: Base name for the SVG file (default: timestamp-based name)
            max_tokens: Maximum tokens for response
            
        Returns:
            Dictionary with SVG code and metadata
        """
        # Set up output directory
        if not output_dir:
            output_dir = "generated_svgs"
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up SVG filename
        if not svg_name:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            svg_name = f"generated_{timestamp}"
        
        svg_path = os.path.join(output_dir, f"{svg_name}.svg")
        prompt_path = os.path.join(output_dir, f"{svg_name}_prompt.txt")
        metadata_path = os.path.join(output_dir, f"{svg_name}_metadata.json")
        
        # Save the original prompt
        with open(prompt_path, "w") as f:
            f.write(prompt)
        
        # Enhance the prompt with specific SVG generation instructions
        enhanced_prompt = self._create_svg_generation_prompt(prompt)
        
        # Prepare API request
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": DEFAULT_MODEL,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": enhanced_prompt
                }
            ]
        }
        
        # Send request to Claude API
        try:
            print(f"Sending SVG generation request to Claude API...")
            start_time = time.time()
            
            response = requests.post(API_ENDPOINT, headers=headers, json=data)
            response.raise_for_status()
            
            end_time = time.time()
            
            result = response.json()
            svg_content = result["content"][0]["text"]
            
            # Extract the SVG code from Claude's response
            svg_code = self._extract_svg_code(svg_content)
            
            # Save the SVG file
            with open(svg_path, "w") as f:
                f.write(svg_code)
                
            # Save metadata
            metadata = {
                "prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "timestamp": datetime.datetime.now().isoformat(),
                "model": DEFAULT_MODEL,
                "generation_time_seconds": end_time - start_time,
                "svg_path": svg_path,
                "prompt_path": prompt_path
            }
            
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            print(f"SVG generated and saved to: {svg_path}")
            
            return {
                "success": True,
                "svg_code": svg_code,
                "svg_path": svg_path,
                "prompt_path": prompt_path,
                "metadata_path": metadata_path,
                "metadata": metadata
            }
            
        except Exception as e:
            error_message = f"SVG generation failed: {str(e)}"
            print(error_message)
            
            return {
                "success": False,
                "error": error_message
            }
    
    def _create_svg_generation_prompt(self, user_prompt):
        """
        Enhance the user prompt with specific instructions for SVG generation.
        
        Args:
            user_prompt: The user's diagram description
            
        Returns:
            Enhanced prompt with SVG generation instructions
        """
        # Detect topics in the user prompt to provide more targeted guidance
        topics = self._detect_topics(user_prompt)
        topic_guidance = self._get_topic_specific_guidance(topics)
        
        prompt = f"""
You are an expert SVG designer specializing in scientific and biotechnology diagrams for the Bioicons project. Create a complete, standalone SVG diagram based on this request:

"{user_prompt}"

## CONTEXT: BIOICONS REPOSITORY

You are generating SVGs for the Bioicons project, which is an open-source library of high-quality scientific SVG icons. The repository already contains hundreds of SVG icons organized by:
1. License type (cc-0, cc-by-3.0, cc-by-4.0, etc.)
2. Scientific category (Cell_types, Genetics, Nucleic_acids, etc.)
3. Author name

{topic_guidance}

When appropriate, REUSE existing concepts and design patterns from these icons as building blocks in your new design. Common patterns include:
- Scientific objects like DNA helices, vectors, and laboratory equipment
- Simplified 2D representations of complex biological structures
- Clean, minimal layouts with clear visual hierarchy
- Arrows and flow indicators for process directionality

## DESIGN REQUIREMENTS:

1. SECTOR-BASED LAYOUT:
   - Divide canvas into logical sectors before placing elements
   - For cyclical diagrams, define a central boundary
   - Assign dedicated viewport areas for each component
   - Use transforms to place elements within their allocated sectors
   - Maintain 25-50px minimum spacing between elements

2. COLOR PALETTE (use these exact hex codes):
   - Primary Blue: #19aeff
   - Accent Red: #ff4141
   - Accent Orange: #ffc022
   - Accent Green: #5dbb63
   - Text/Strokes: #333333
   - Background: #f8f9fa (light gray)

3. VISUAL HIERARCHY:
   - Main components: Larger scale (0.6-0.8 of available space)
   - Supporting elements: Smaller scale (0.3-0.5 of available space) 
   - Stroke width proportional to element size (larger elements = thicker strokes)
   - Use strong contrast for important elements

4. COMPONENT-BASED APPROACH:
   - Build diagrams from discrete, reusable components
   - Group related elements with <g> tags and descriptive IDs
   - Use consistent styling within component groups
   - Maintain clear visual separation between component groups

5. SVG TECHNICAL SPECIFICATIONS:
   - Use width="800" height="600" for the SVG
   - Use ONLY standard SVG elements (rect, circle, path, text, g, etc.)
   - Set viewBox="0 0 800 600" to ensure proper scaling
   - Text must be minimum 12px and have good contrast
   - Include clear, descriptive element IDs for all major components
   - Use semantic grouping with the <g> element
   - Avoid inline CSS styles; use SVG attributes instead

6. SCIENTIFIC ACCURACY:
   - Follow standard scientific visualization conventions
   - Use appropriate proportions and relationships between elements
   - Simplify complex concepts without sacrificing accuracy
   - For scientific diagrams/cycles, ensure directionality is clear

## OUTPUT FORMAT:
- Start with <?xml version="1.0" encoding="UTF-8" standalone="no"?>
- Include proper SVG attributes and namespaces
- ALL text must be <text> elements (no embedded HTML)
- Return ONLY the complete SVG code with no explanation or commentary

Create a professional, scientifically accurate SVG suitable for research publications and presentations.
"""
        return prompt
    
    def _detect_topics(self, prompt):
        """
        Detect scientific topics in the user prompt.
        
        Args:
            prompt: The user's diagram description
            
        Returns:
            List of detected topics
        """
        topics = []
        prompt_lower = prompt.lower()
        
        # Check for various scientific domains
        if any(term in prompt_lower for term in ["aav", "gene therapy", "gene editing", "viral vector"]):
            topics.append("gene_therapy")
            
        if any(term in prompt_lower for term in ["crispr", "cas9", "genome editing"]):
            topics.append("crispr")
            
        if any(term in prompt_lower for term in ["cell signal", "pathway", "cascade", "receptor"]):
            topics.append("signaling")
            
        if any(term in prompt_lower for term in ["protein", "structure", "folding", "enzyme"]):
            topics.append("protein")
            
        if "cycle" in prompt_lower or "loop" in prompt_lower:
            topics.append("cycle")
            
        if any(term in prompt_lower for term in ["workflow", "pipeline", "process"]):
            topics.append("workflow")
            
        # If no specific topics detected, add a default topic
        if not topics:
            topics.append("default")
            
        return topics
    
    def _get_topic_specific_guidance(self, topics):
        """
        Get topic-specific guidance for SVG creation.
        
        Args:
            topics: List of detected topics
            
        Returns:
            String with topic-specific guidance
        """
        guidance = []
        
        if "gene_therapy" in topics:
            guidance.append("""For AAV/gene therapy diagrams, consider incorporating these relevant elements:
- DNA/RNA strands (in Nucleic_acids category)
- Viral capsid representations (in Viruses category)
- Cell components like nucleus, cytoplasm (in Cell_types, Intracellular_components categories)
- Laboratory equipment such as pipettes, plates (in Lab_apparatus category)""")
            
        if "crispr" in topics:
            guidance.append("""For CRISPR/Cas9 diagrams, consider incorporating these relevant elements:
- DNA/RNA structures (in Nucleic_acids category)
- Guide RNA representations (in Nucleic_acids category)
- Cas9 protein (in Receptors_channels or Intracellular_components categories)
- Cell nucleus and genomic DNA (in Cell_types, Intracellular_components categories)""")
            
        if "signaling" in topics:
            guidance.append("""For cell signaling pathway diagrams, consider incorporating these relevant elements:
- Cell membrane and receptors (in Cell_membrane, Receptors_channels categories)
- Intracellular signaling proteins (in Intracellular_components category)
- Nucleus and gene expression elements (in Intracellular_components category)
- Protein-protein interactions and phosphorylation events""")
            
        if "protein" in topics:
            guidance.append("""For protein structure diagrams, consider incorporating these relevant elements:
- Amino acid representations (in Amino-Acids category if available)
- Secondary structure elements (alpha helices, beta sheets)
- Tertiary structure representations
- Protein-ligand or protein-protein interfaces""")
            
        if "cycle" in topics:
            guidance.append("""For cycle/loop diagrams, use these design principles:
- Create a clear circular or cyclic layout with distinct phases
- Use directional arrows to indicate process flow
- Position elements evenly around the circle or loop
- Consider using the center area for common elements or key summary information""")
            
        if "workflow" in topics:
            guidance.append("""For workflow/pipeline diagrams, use these design principles:
- Create a linear or branching layout with clear directionality
- Use consistent shapes for similar process steps
- Include numbered or labeled steps for easy reference
- Use consistent spacing between workflow stages""")
            
        if "default" in topics and not guidance:
            guidance.append("""Consider which categories in the Bioicons repository are most relevant to your task:
- Cell_types for cellular components and structures
- Genetics or Nucleic_acids for DNA/RNA elements
- Intracellular_components for proteins and organelles
- Lab_apparatus for laboratory equipment and experimental setup
- Scientific_graphs for data visualization components""")
            
        return "\n\n".join(guidance)
    
    def _extract_svg_code(self, response_text):
        """
        Extract SVG code from Claude's response.
        
        Args:
            response_text: The raw text of Claude's response
            
        Returns:
            Clean SVG code
        """
        # Remove any markdown code blocks if present
        svg_code = response_text.replace("```xml", "").replace("```svg", "").replace("```", "").strip()
        
        # Remove any explanatory text before the SVG code
        if "<?xml" in svg_code:
            svg_code = svg_code[svg_code.find("<?xml"):]
        
        # If there are multiple XML declarations, keep only the first one
        if svg_code.count("<?xml") > 1:
            first_decl_end = svg_code.find("?>") + 2
            second_decl_start = svg_code.find("<?xml", first_decl_end)
            if second_decl_start > 0:
                svg_code = svg_code[:first_decl_end] + svg_code[svg_code.find("<svg", second_decl_start):]
        
        # Ensure it starts with XML declaration
        if not svg_code.startswith("<?xml"):
            svg_code = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + svg_code
        
        return svg_code


def main():
    """Main function to handle command line arguments and generate SVGs."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate SVG diagrams from text prompts using Claude")
    parser.add_argument("prompt", help="Text prompt describing the desired diagram")
    parser.add_argument("--output-dir", "-o", help="Directory to save outputs")
    parser.add_argument("--name", "-n", help="Base name for the SVG file")
    parser.add_argument("--api-key", "-k", help="Claude API key (defaults to ANTHROPIC_API_KEY env var)")
    
    args = parser.parse_args()
    
    try:
        # Initialize generator
        generator = SVGGenerator(api_key=args.api_key)
        
        # Generate SVG
        result = generator.generate_svg(
            args.prompt,
            output_dir=args.output_dir,
            svg_name=args.name
        )
        
        if result["success"]:
            print(f"\nSVG generation complete!")
            print(f"SVG file: {result['svg_path']}")
            print(f"Prompt file: {result['prompt_path']}")
            print(f"Metadata file: {result['metadata_path']}")
        else:
            print(f"\nError: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
        
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())