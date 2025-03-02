# Installation Guide

This guide will help you set up the SVG Critic and Generator system.

## Prerequisites

- Python 3.8+
- Anthropic API key (get one at https://console.anthropic.com/)
- For SVG rendering: Cairo libraries

## Step 1: Install Dependencies

### On macOS:

```bash
# Install Cairo (required for SVG rendering)
brew install cairo

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### On Linux:

```bash
# Install Cairo (required for SVG rendering)
sudo apt-get install libcairo2-dev pkg-config python3-dev

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### On Windows:

```bash
# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install Python dependencies (cairosvg is optional on Windows)
pip install -r requirements.txt
```

## Step 2: Configure API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your Anthropic API key
# Replace "your_claude_api_key_here" with your actual key
nano .env  # or use your preferred text editor
```

## Step 3: Verify Installation

```bash
# Test your API key setup
python tests/test_api_key.py
```

If the test is successful, you'll see a confirmation message.

## Step 4: Run Example Experiment

```bash
# Run a simple experiment to generate an SVG from a prompt
python complete_workflow.py "Create a design build test (deep)learn loop diagram for AAV/gene therapy" \
  --experiment-name aav_gene_therapy_cycle --iterations 2
```

## Common Issues

1. **SVG Rendering Issues**: If you encounter problems with CairoSVG:
   - Ensure Cairo is properly installed on your system
   - Try updating CairoSVG: `pip install --upgrade cairosvg`

2. **API Key Issues**:
   - Double-check your API key in the .env file
   - Ensure your Anthropic account has sufficient quota
   - Verify the API key has the proper permissions

3. **Package Dependency Issues**:
   - Make sure you're using a compatible Python version (3.8+)
   - Try upgrading pip: `pip install --upgrade pip`
   - Install packages one by one to identify problematic dependencies

## Using uv (Alternative Installation)

For faster dependency resolution, you can use [uv](https://github.com/astral-sh/uv):

```bash
# Install uv
pip install uv

# Create a virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt
```