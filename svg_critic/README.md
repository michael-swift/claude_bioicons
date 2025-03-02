# SVG Critic & Generator - End-to-End SVG Design System

SVG Critic is an AI-augmented tool for creating, analyzing, and improving SVG diagrams used in scientific illustrations. It provides a complete workflow from text prompts to final optimized SVGs, creating a feedback loop between "SVG Claude" (the code generator) and "Designer Claude" (the visual assessor) to incrementally improve scientific visualizations.

## Key Features

- **Text-to-SVG Generation**: Create initial SVG diagrams from text prompts
- **Automated Visual Design Assessment**: Evaluate SVGs based on multiple design criteria
- **Claude Vision API Integration**: Provide human-like visual analysis of SVG diagrams
- **Iterative Improvement Process**: Provide feedback and implement changes over multiple iterations
- **Comprehensive Metrics**: Analyze layout balance, color harmony, visual hierarchy, and accessibility
- **Standardization**: Encourage adherence to established design guidelines
- **Visual Progress Tracking**: Generate HTML reports showing improvement across iterations
- **Experiment Tracking**: Document and track SVG design experiments systematically

## Components

The system includes several key components:

### 1. SVG Generator (Text-to-SVG)

Create initial SVG diagrams from text descriptions:

- **Text Prompt Processing**: Convert natural language descriptions to SVG designs
- **Bioicons Repository Context**: Leverage existing design patterns and components
- **Structured Output Format**: Generate valid SVG files with proper attributes and namespaces
- **Metadata Tracking**: Save prompt and generation details for reproducibility

### 2. SVG Critic (Local Analysis)

Core analysis engine that evaluates SVG files and provides structured feedback:

- **Layout Analysis**: Evaluates element distribution across quadrants 
- **Color Harmony**: Checks adherence to standard palette
- **Visual Hierarchy**: Assesses size relationships between elements
- **Accessibility**: Evaluates text size and color contrast
- **Overlap Detection**: Identifies elements that obscure each other

### 3. Visual SVG Critic

Enhanced version that uses a more vision-oriented approach:

- **Region-based Analysis**: Analyzes distribution of elements by region
- **Visual Balance Assessment**: Identifies imbalances in element distribution
- **Mock Visual Rendering**: Simulates visual perception of the diagram

### 4. Claude API Integration

Full integration with Claude's Vision API for human-like analysis:

- **SVG to PNG Conversion**: Converts SVG to PNG for visual analysis
- **Claude Vision Analysis**: Sends rendered image to Claude for expert feedback
- **Claude SVG Improvement**: Uses Claude to modify SVG code based on feedback

### 5. Design Loop

Orchestrates the iterative improvement process:

1. Evaluates current SVG (using local critic or Claude API)
2. Implements improvements based on feedback
3. Repeats until satisfaction threshold is reached or max iterations completed
4. Generates comprehensive progress report

### 6. Complete Workflow

End-to-end orchestration from text prompt to optimized SVG:

1. Generates initial SVG from text prompt
2. Runs the design loop for iterative improvement
3. Tracks and documents the entire process
4. Creates comprehensive reports with all artifacts

## Installation

### Prerequisites

- Python 3.7+
- Required Python packages:
  - requests
  - Pillow (for image handling)
  - CairoSVG (optional, for better SVG rendering)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/svg-critic.git
   cd svg-critic
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Claude API key (if using API features):
   ```
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

## Usage

### 1. Basic Local Analysis

```bash
# Analyze a SVG file with local critic
python svg_critic/visual_svg_critic.py /path/to/your/diagram.svg

# Get improvement suggestions
python svg_critic/visual_svg_critic.py /path/to/your/diagram.svg --improve
```

### 2. Running the Design Loop (Local)

```bash
# Run design loop on an SVG file using local analysis
python svg_critic/visual_design_loop.py /path/to/your/diagram.svg

# Specify output directory and iterations
python svg_critic/visual_design_loop.py /path/to/your/diagram.svg -o output_folder -i 5

# Set custom satisfaction threshold
python svg_critic/visual_design_loop.py /path/to/your/diagram.svg -t 90
```

### 3. Claude API Integration

```bash
# Test SVG to PNG conversion
python svg_critic/test_claude_api.py --convert /path/to/your/diagram.svg

# Analyze PNG with Claude API
python svg_critic/test_claude_api.py --analyze /path/to/your/diagram.png

# Improve SVG based on feedback
python svg_critic/test_claude_api.py --improve /path/to/your/diagram.svg --feedback /path/to/feedback.md
```

### 4. Full Claude API Design Loop

```bash
# Run the full Claude API design loop
python svg_critic/visual_design_loop_with_api.py /path/to/your/diagram.svg

# Run with custom API key
python svg_critic/visual_design_loop_with_api.py /path/to/your/diagram.svg --api-key your_api_key

# Force local analysis only
python svg_critic/visual_design_loop_with_api.py /path/to/your/diagram.svg --local-only
```

### 5. Running Complete Text-to-SVG Experiments

First, set up your API key in the .env file:
```bash
# Copy the example file
cp .env.example .env

# Edit with your actual API key
nano .env  # or use your preferred text editor
```

Then verify your API key is working:
```bash
python test_api_key.py
```

Now you can run experiments:
```bash
# Generate SVG from text prompt
python svg_generator.py "Create a CRISPR-Cas9 workflow diagram showing the main steps" \
  --output-dir generated_svgs --name crispr_workflow

# Run full experiment with iterative improvement
python complete_workflow.py "Create a cell signaling pathway diagram showing MAPK/ERK cascade" \
  --experiment-name mapk_pathway --iterations 3 --threshold 85

# Run AAV gene therapy loop diagram test
python complete_workflow.py "Create a design build test (deep)learn loop diagram for AAV/gene therapy" \
  --experiment-name aav_gene_therapy_cycle --iterations 3
```

### 6. Using SVG Critic and Generator in Python Code

```python
# SVG Generator - Text to SVG
from svg_generator import SVGGenerator

generator = SVGGenerator()
result = generator.generate_svg(
    "Create a clinical trial flowchart",
    output_dir="generated_svgs",
    svg_name="clinical_trial"
)
print(f"SVG generated at: {result['svg_path']}")

# Local SVG Critic
from svg_critic import SVGCritic, generate_human_readable_report

# Analyze a single SVG
critic = SVGCritic("diagram.svg")
evaluation = critic.evaluate()

# Generate human-readable report
report = generate_human_readable_report(evaluation)
print(report)

# Visual SVG Critic
from visual_svg_critic import VisualSVGCritic

# Create visual critic
visual_critic = VisualSVGCritic("diagram.svg")
feedback = visual_critic.evaluate()
suggestions = visual_critic.suggest_improvements(feedback)

# Claude API Integration
from claude_api import ClaudeAPI, svg_to_png

# Convert SVG to PNG
png_path = svg_to_png("diagram.svg", "diagram.png")

# Analyze with Claude API
api = ClaudeAPI()
result = api.analyze_image(png_path)

# Improve SVG based on feedback
with open("diagram.svg", "r") as f:
    svg_code = f.read()
improved_svg = api.improve_svg(svg_code, result)

# Complete Workflow
from complete_workflow import CompleteWorkflow

workflow = CompleteWorkflow()
experiment_result = workflow.run_workflow(
    "Create a genetic engineering workflow diagram",
    experiment_name="genetic_engineering",
    max_iterations=3,
    satisfaction_threshold=90
)
print(f"Final SVG: {experiment_result['final_svg']}")
print(f"Experiment report: {experiment_result['report_path']}")
```

## Interpreting Results

The system generates several types of output:

### 1. Evaluation Report

A markdown file with a detailed assessment of the SVG:
- Overall score (0-100)
- Layout balance analysis
- Color harmony assessment
- Visual hierarchy evaluation
- Accessibility considerations
- Specific improvement suggestions

### 2. Improved SVG Files

For each iteration, an improved version of the SVG is generated that addresses issues identified in the evaluation.

### 3. HTML Progress Report

A comprehensive visual report showing:
- Score improvement over iterations
- Side-by-side comparisons of SVG versions
- Rendered PNG previews (with API integration)
- Detailed analysis for each iteration
- Interactive charts of progress metrics

## Standardized Design Guidelines

SVG Critic evaluates designs based on Bioicons' established guidelines:

1. **Sector-based Layout**:
   - SVGs should divide the canvas into logical quadrants
   - Elements should be positioned within appropriate sectors
   - Central area should be reserved for common elements or kept clear

2. **Standard Color Palette**:
   - Primary Blue: #19aeff
   - Accent Red: #ff4141
   - Accent Orange: #ffc022
   - Accent Green: #5dbb63
   - Text/Strokes: #333333

3. **Visual Hierarchy**:
   - Main components: Larger scale (0.6-0.8)
   - Supporting elements: Smaller scale (0.3-0.5)
   - Stroke width proportional to element size

4. **Accessibility**:
   - Minimum font size: 10px (12px recommended)
   - Strong contrast for text elements
   - Clear visual differentiation between elements

## Modules in Detail

### `svg_critic.py`

The original code-based SVG analysis module. Works well for detecting specific code-level issues but has limitations in understanding design intent.

### `visual_svg_critic.py`

An enhanced version that takes a more vision-oriented approach to SVG analysis, focusing on overall layout and visual balance rather than just code structure.

### `claude_api.py`

Handles interactions with the Claude API, including:
- SVG to PNG conversion (using multiple methods)
- Image analysis with Claude Vision API
- SVG code improvement based on visual feedback

### `visual_design_loop.py`

Implements the local-only iterative design loop process.

### `visual_design_loop_with_api.py`

Implements the full Claude API-enhanced design loop process, with fallback to local analysis if API is unavailable.

### `test_claude_api.py`

Utility script for testing individual components of the Claude API integration.

## Experiment System for Text-to-SVG

The system now includes a complete experiment-tracking system for Text-to-SVG generation and improvement. Each experiment:

1. Creates a uniquely identified, timestamped experiment directory
2. Tracks the original prompt and all configuration parameters
3. Saves all artifacts (SVGs, feedback, metadata) in a standardized structure
4. Generates comprehensive reports with reproducibility commands
5. Evaluates SVG quality at each iteration

### Experiment Directory Structure

```
experiment_aav_gene_therapy_20250226_123456/
├── experiment_details.json           # Experiment configuration and metadata
├── workflow_report.md                # Human-readable experiment report
├── workflow_summary.json             # Machine-readable experiment summary
├── 1_generation/                     # Initial SVG generation artifacts
│   ├── aav_gene_therapy_initial.svg  # Initial SVG design
│   ├── aav_gene_therapy_initial_prompt.txt  # Original user prompt
│   └── aav_gene_therapy_initial_metadata.json  # Generation process details
└── 2_improvement/                    # Design improvement cycle artifacts
    ├── aav_gene_therapy_initial.svg  # Starting point (copy of initial)
    ├── iteration_1.svg               # First improved version
    ├── iteration_1_feedback.json     # Critique of initial version
    ├── iteration_2.svg               # Second improved version
    ├── iteration_2_feedback.json     # Critique of first improved version
    ├── final.svg                     # Final improved version
    └── progress_report.html          # Visual report of all versions
```

### Standardized Test Prompts

We've developed a set of standard test prompts that exercise different aspects of the system:

1. **AAV Gene Therapy Cycle**:
   ```
   Create a design build test (deep)learn loop diagram for AAV/gene therapy
   ```
   This prompt tests the system's ability to create cyclical diagrams with clear directionality.

2. **Cell Signaling Pathway**:
   ```
   Create a cell signaling pathway diagram showing MAPK/ERK cascade from 
   receptor tyrosine kinase activation to gene expression changes
   ```
   This tests the creation of complex pathways with nested components.

3. **CRISPR-Cas9 Workflow**:
   ```
   Design a CRISPR-Cas9 workflow diagram showing guide RNA design, 
   Cas9 complex formation, DNA binding, cutting, and repair outcomes
   ```
   This tests linear workflow visualization with multiple steps.

4. **Protein Structure Visualization**:
   ```
   Create a diagram showing the four levels of protein structure: 
   primary, secondary, tertiary, and quaternary
   ```
   This tests the system's ability to create hierarchical visualizations.

These standardized prompts allow us to consistently evaluate system improvements and compare different approaches.

## Troubleshooting

### SVG to PNG Conversion Issues

If you encounter problems with SVG to PNG conversion:

1. Install additional conversion tools:
   ```
   # Ubuntu/Debian
   sudo apt-get install librsvg2-bin imagemagick inkscape
   
   # macOS
   brew install librsvg imagemagick inkscape
   ```

2. Try installing the CairoSVG Python package:
   ```
   pip install cairosvg
   ```

3. Check that your SVG file is valid:
   ```
   xmllint --noout your_file.svg
   ```

### Claude API Issues

1. Ensure your API key is set correctly:
   ```
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

2. Check for API rate limiting or quota issues
3. Verify that your PNG file is valid and not too large

## Future Development

1. **Advanced Claude Integration**: Implement more sophisticated AI-generated improvements
2. **Learning System**: Train on successful illustrations to improve recommendations
3. **Domain-Specific Rules**: Add specialized rules for different scientific domains
4. **Interactive Web Interface**: Allow designers to apply suggestions selectively
5. **Version Control Integration**: Track changes and allow reverting to previous iterations
6. **Automated Testing**: Add comprehensive testing for all system components

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.