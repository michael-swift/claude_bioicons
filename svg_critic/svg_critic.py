"""
SVG Critic - A system for analyzing and providing feedback on SVG visualizations.

This tool evaluates SVG files based on design principles and provides structured feedback
to improve visual clarity, organization, and effectiveness.
"""

import re
import math
import xml.etree.ElementTree as ET
import json
from collections import defaultdict
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union

# Define namespaces for parsing SVG
NAMESPACES = {
    'svg': 'http://www.w3.org/2000/svg',
    'xlink': 'http://www.w3.org/1999/xlink',
    'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
    'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'
}

# Register namespaces for ElementTree
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)


class SVGCritic:
    """
    Analyzes SVG files and provides design feedback.
    """
    
    def __init__(self, svg_path: str):
        """
        Initialize with path to SVG file.
        
        Args:
            svg_path: Path to the SVG file to analyze
        """
        self.svg_path = svg_path
        self.tree = ET.parse(svg_path)
        self.root = self.tree.getroot()
        self.width = float(self.root.get('width', '800'))
        self.height = float(self.root.get('height', '600'))
        self.elements = self._parse_elements()
        self.color_palette = self._extract_color_palette()
        
    def _parse_elements(self) -> List[Dict]:
        """Extract all SVG elements into a structured format."""
        elements = []
        
        def process_element(elem, parent_id=None, group_transform=None):
            elem_id = elem.get('id', '')
            elem_type = elem.tag.split('}')[-1]  # Remove namespace prefix
            
            # Get element attributes
            attrs = {k: v for k, v in elem.attrib.items()}
            
            # Process transform attribute
            transform = attrs.get('transform', group_transform)
            
            # Handle different element types
            if elem_type in ['rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'path']:
                bbox = self._calculate_bbox(elem, transform)
                elements.append({
                    'id': elem_id,
                    'type': elem_type,
                    'attributes': attrs,
                    'transform': transform,
                    'parent_id': parent_id,
                    'bbox': bbox
                })
            
            # Process children recursively
            for child in elem:
                process_element(child, elem_id, transform)
        
        # Start processing from root
        for child in self.root:
            process_element(child)
            
        return elements
    
    def _calculate_bbox(self, elem, transform=None) -> Dict[str, float]:
        """Calculate bounding box for an element (approximate)."""
        elem_type = elem.tag.split('}')[-1]
        
        if elem_type == 'rect':
            x = float(elem.get('x', '0'))
            y = float(elem.get('y', '0'))
            width = float(elem.get('width', '0'))
            height = float(elem.get('height', '0'))
            return {'x1': x, 'y1': y, 'x2': x + width, 'y2': y + height}
            
        elif elem_type == 'circle':
            cx = float(elem.get('cx', '0'))
            cy = float(elem.get('cy', '0'))
            r = float(elem.get('r', '0'))
            return {'x1': cx - r, 'y1': cy - r, 'x2': cx + r, 'y2': cy + r}
            
        elif elem_type == 'ellipse':
            cx = float(elem.get('cx', '0'))
            cy = float(elem.get('cy', '0'))
            rx = float(elem.get('rx', '0'))
            ry = float(elem.get('ry', '0'))
            return {'x1': cx - rx, 'y1': cy - ry, 'x2': cx + rx, 'y2': cy + ry}
            
        # For more complex elements like paths, we'd need more sophisticated calculations
        # This is a placeholder for demonstration
        return {'x1': 0, 'y1': 0, 'x2': 0, 'y2': 0}
    
    def _extract_color_palette(self) -> Dict[str, int]:
        """Extract and count colors used in the SVG."""
        colors = defaultdict(int)
        
        for elem in self.elements:
            attrs = elem['attributes']
            fill = attrs.get('fill')
            stroke = attrs.get('stroke')
            
            if fill and fill != 'none':
                colors[fill] += 1
            if stroke and stroke != 'none':
                colors[stroke] += 1
                
        return dict(colors)
    
    def detect_overlaps(self) -> List[Dict]:
        """
        Detect overlapping elements in the SVG.
        
        Returns:
            List of overlapping element pairs with overlap details
        """
        overlaps = []
        
        for i, elem1 in enumerate(self.elements):
            bbox1 = elem1.get('bbox', {})
            if not bbox1 or 'x1' not in bbox1:
                continue
                
            for j, elem2 in enumerate(self.elements[i+1:], i+1):
                # Skip elements with the same parent
                if elem1.get('parent_id') == elem2.get('parent_id'):
                    continue
                    
                bbox2 = elem2.get('bbox', {})
                if not bbox2 or 'x1' not in bbox2:
                    continue
                
                # Check for overlap
                if (bbox1['x1'] < bbox2['x2'] and bbox1['x2'] > bbox2['x1'] and
                    bbox1['y1'] < bbox2['y2'] and bbox1['y2'] > bbox2['y1']):
                    
                    # Calculate overlap area
                    overlap_width = min(bbox1['x2'], bbox2['x2']) - max(bbox1['x1'], bbox2['x1'])
                    overlap_height = min(bbox1['y2'], bbox2['y2']) - max(bbox1['y1'], bbox2['y1'])
                    overlap_area = overlap_width * overlap_height
                    
                    # Calculate percentage of smaller element
                    area1 = (bbox1['x2'] - bbox1['x1']) * (bbox1['y2'] - bbox1['y1'])
                    area2 = (bbox2['x2'] - bbox2['x1']) * (bbox2['y2'] - bbox2['y1'])
                    smaller_area = min(area1, area2)
                    overlap_percentage = (overlap_area / smaller_area) * 100 if smaller_area > 0 else 0
                    
                    if overlap_percentage > 10:  # Only report significant overlaps
                        overlaps.append({
                            'element1': elem1.get('id', f"element-{i}"),
                            'element2': elem2.get('id', f"element-{j}"),
                            'overlap_percentage': overlap_percentage,
                            'severity': 'high' if overlap_percentage > 50 else 'medium'
                        })
        
        return overlaps
    
    def analyze_layout(self) -> Dict:
        """
        Analyze layout organization and quadrant distribution.
        
        Returns:
            Dictionary with layout analysis metrics
        """
        # Define quadrants
        quadrants = {
            'q1': {'x1': 0, 'y1': 0, 'x2': self.width/2, 'y2': self.height/2},
            'q2': {'x1': self.width/2, 'y1': 0, 'x2': self.width, 'y2': self.height/2},
            'q3': {'x1': self.width/2, 'y1': self.height/2, 'x2': self.width, 'y2': self.height},
            'q4': {'x1': 0, 'y1': self.height/2, 'x2': self.width/2, 'y2': self.height}
        }
        
        # Count elements in each quadrant
        quadrant_counts = {q: 0 for q in quadrants}
        
        for elem in self.elements:
            bbox = elem.get('bbox', {})
            if not bbox or 'x1' not in bbox:
                continue
                
            # Find center point of element
            center_x = (bbox['x1'] + bbox['x2']) / 2
            center_y = (bbox['y1'] + bbox['y2']) / 2
            
            # Determine quadrant
            for q, q_bbox in quadrants.items():
                if (q_bbox['x1'] <= center_x <= q_bbox['x2'] and 
                    q_bbox['y1'] <= center_y <= q_bbox['y2']):
                    quadrant_counts[q] += 1
                    break
        
        # Calculate balance score (0-100)
        total_elements = sum(quadrant_counts.values())
        if total_elements == 0:
            balance_score = 100  # No elements
        else:
            expected_per_quadrant = total_elements / 4
            deviations = [abs(count - expected_per_quadrant) for count in quadrant_counts.values()]
            max_possible_deviation = total_elements
            actual_deviation = sum(deviations)
            balance_score = 100 - (actual_deviation / max_possible_deviation * 100)
        
        return {
            'quadrant_distribution': quadrant_counts,
            'balance_score': balance_score,
            'suggestions': self._generate_layout_suggestions(quadrant_counts, balance_score)
        }
    
    def _generate_layout_suggestions(self, quadrant_counts: Dict, balance_score: float) -> List[str]:
        """Generate suggestions for improving layout based on quadrant analysis."""
        suggestions = []
        
        # Check for empty quadrants
        empty_quadrants = [q for q, count in quadrant_counts.items() if count == 0]
        if empty_quadrants:
            suggestions.append(f"Add content to empty quadrant(s): {', '.join(empty_quadrants)}")
        
        # Check for imbalanced quadrants
        if balance_score < 70:
            max_q = max(quadrant_counts, key=quadrant_counts.get)
            min_q = min(quadrant_counts, key=quadrant_counts.get)
            suggestions.append(f"Redistribute elements from {max_q} to {min_q} for better balance")
        
        return suggestions
    
    def analyze_color_harmony(self) -> Dict:
        """
        Analyze color palette for harmony and consistency.
        
        Returns:
            Dictionary with color analysis metrics
        """
        # Count unique colors (excluding 'none' and common defaults)
        unique_colors = [c for c in self.color_palette.keys() 
                        if c and c.lower() not in ['none', 'transparent', 'inherit']]
        
        # Check if standard palette colors are used
        standard_palette = ['#19aeff', '#ff4141', '#ffc022', '#5dbb63', '#333333']
        palette_usage = {color: color in unique_colors for color in standard_palette}
        
        # Calculate consistency score
        total_color_uses = sum(self.color_palette.values())
        standard_color_uses = sum(self.color_palette.get(c, 0) for c in standard_palette)
        
        consistency_score = (standard_color_uses / total_color_uses * 100) if total_color_uses > 0 else 0
        
        # Prepare suggestions
        suggestions = []
        if len(unique_colors) > 8:
            suggestions.append("Reduce color palette to improve visual cohesion")
        
        missing_standards = [c for c, used in palette_usage.items() if not used]
        if missing_standards:
            suggestions.append(f"Consider using standard palette colors: {', '.join(missing_standards)}")
        
        return {
            'unique_colors': len(unique_colors),
            'palette_adherence': consistency_score,
            'suggestions': suggestions
        }
    
    def analyze_visual_hierarchy(self) -> Dict:
        """
        Analyze visual hierarchy based on size relationships.
        
        Returns:
            Dictionary with hierarchy analysis metrics
        """
        # Collect size information
        sizes = []
        for elem in self.elements:
            bbox = elem.get('bbox', {})
            if not bbox or 'x1' not in bbox:
                continue
                
            width = bbox['x2'] - bbox['x1']
            height = bbox['y2'] - bbox['y1']
            area = width * height
            
            if area > 0:
                sizes.append(area)
        
        if not sizes:
            return {
                'score': 0,
                'suggestions': ["Not enough measurable elements to analyze hierarchy"]
            }
        
        # Calculate size variety
        sizes.sort()
        if len(sizes) < 2:
            size_ratio = 1
        else:
            size_ratio = sizes[-1] / sizes[0]  # Largest to smallest ratio
        
        # Score based on ratio (ideally around 10-20x difference between largest and smallest)
        if size_ratio < 5:
            hierarchy_score = 60  # Too little size variation
            suggestion = "Increase size contrast between primary and secondary elements"
        elif 5 <= size_ratio <= 25:
            hierarchy_score = 100  # Good variation
            suggestion = "Current size hierarchy is appropriate"
        else:
            hierarchy_score = 75  # Too much variation
            suggestion = "Reduce extreme size differences that may overwhelm smaller elements"
        
        return {
            'score': hierarchy_score,
            'size_ratio': size_ratio,
            'suggestions': [suggestion]
        }

    def analyze_accessibility(self) -> Dict:
        """
        Analyze for accessibility concerns.
        
        Returns:
            Dictionary with accessibility analysis metrics
        """
        # Analyze text elements
        text_elements = [e for e in self.elements if e['type'] == 'text']
        small_text_count = 0
        
        for elem in text_elements:
            font_size = elem['attributes'].get('font-size', '12')
            # Extract numeric part of font-size
            font_size_num = float(re.search(r'(\d+)', font_size).group(1)) if re.search(r'(\d+)', font_size) else 12
            
            if font_size_num < 10:
                small_text_count += 1
        
        # Text size score
        text_size_score = 100 - (small_text_count / len(text_elements) * 100) if text_elements else 100
        
        # Simple color contrast check - just flagging potential issues
        contrast_issues = []
        for elem in self.elements:
            fill = elem['attributes'].get('fill', '').lower()
            
            # Check for potentially low-contrast combinations
            if fill in ['#ffffff', 'white'] and elem['attributes'].get('stroke', '') in ['#f0f0f0', '#f8f9fa']:
                contrast_issues.append(f"Low contrast white on light gray in element {elem.get('id', 'unknown')}")
            elif fill in ['#000000', 'black'] and elem['attributes'].get('stroke', '') in ['#333333', '#444444']:
                contrast_issues.append(f"Low contrast black on dark gray in element {elem.get('id', 'unknown')}")
        
        # Overall accessibility score
        accessibility_score = (text_size_score + (100 - len(contrast_issues) * 10)) / 2
        accessibility_score = max(0, min(100, accessibility_score))
        
        suggestions = []
        if small_text_count > 0:
            suggestions.append(f"Increase font size for {small_text_count} text elements that are smaller than 10px")
        if contrast_issues:
            suggestions.append("Improve color contrast for better readability")
        
        return {
            'score': accessibility_score,
            'font_size_score': text_size_score,
            'contrast_issues': len(contrast_issues),
            'suggestions': suggestions
        }

    def suggest_code_improvements(self) -> List[Dict]:
        """
        Suggest specific code changes to improve the SVG.
        
        Returns:
            List of suggested code modifications
        """
        suggestions = []
        
        # Check for missing IDs
        missing_ids = [i for i, elem in enumerate(self.elements) 
                      if not elem.get('id') and elem['type'] not in ['defs', 'title']]
        
        if missing_ids:
            suggestions.append({
                'type': 'general',
                'issue': 'Missing element IDs',
                'suggestion': f"Add ID attributes to {len(missing_ids)} elements for better maintainability"
            })
        
        # Check for overlaps and suggest fixes
        overlaps = self.detect_overlaps()
        for overlap in overlaps:
            elem1 = overlap['element1']
            elem2 = overlap['element2']
            
            suggestions.append({
                'type': 'position',
                'elements': [elem1, elem2],
                'issue': f"Elements overlap by {overlap['overlap_percentage']:.1f}%",
                'suggestion': f"Adjust position of {elem1} or {elem2} to prevent overlap"
            })
        
        # Check for elements near edges
        edge_buffer = 20  # pixels
        for i, elem in enumerate(self.elements):
            bbox = elem.get('bbox', {})
            if not bbox or 'x1' not in bbox:
                continue
                
            # Check if element is very close to SVG edge
            if (bbox['x1'] < edge_buffer or 
                bbox['y1'] < edge_buffer or 
                bbox['x2'] > self.width - edge_buffer or 
                bbox['y2'] > self.height - edge_buffer):
                
                elem_id = elem.get('id', f"element-{i}")
                suggestions.append({
                    'type': 'position',
                    'elements': [elem_id],
                    'issue': f"Element {elem_id} is too close to SVG edge",
                    'suggestion': f"Move {elem_id} inward to maintain proper margin"
                })
        
        return suggestions
    
    def evaluate(self) -> Dict:
        """
        Perform full evaluation of the SVG.
        
        Returns:
            Dictionary with complete evaluation results
        """
        # Analyze various aspects
        overlaps = self.detect_overlaps()
        layout = self.analyze_layout()
        color_harmony = self.analyze_color_harmony()
        visual_hierarchy = self.analyze_visual_hierarchy()
        accessibility = self.analyze_accessibility()
        code_improvements = self.suggest_code_improvements()
        
        # Calculate overall score (weighted average)
        weights = {
            'overlaps': 0.25,
            'layout': 0.20,
            'color_harmony': 0.15,
            'visual_hierarchy': 0.20,
            'accessibility': 0.20
        }
        
        # Convert overlap count to a score (0-100)
        overlap_score = 100 - min(100, len(overlaps) * 20)
        
        # Weighted score calculation
        overall_score = (
            weights['overlaps'] * overlap_score +
            weights['layout'] * layout['balance_score'] +
            weights['color_harmony'] * color_harmony['palette_adherence'] +
            weights['visual_hierarchy'] * visual_hierarchy['score'] +
            weights['accessibility'] * accessibility['score']
        )
        
        # Round to nearest integer
        overall_score = round(overall_score)
        
        return {
            'overall_score': overall_score,
            'critical_issues': [
                {
                    'type': 'overlap', 
                    'elements': [o['element1'], o['element2']], 
                    'severity': o['severity']
                } 
                for o in overlaps
            ],
            'layout_assessment': layout,
            'color_harmony': color_harmony,
            'visual_hierarchy': visual_hierarchy,
            'accessibility': accessibility,
            'suggested_code_changes': code_improvements
        }


def generate_human_readable_report(evaluation: Dict) -> str:
    """
    Convert the evaluation dictionary to a human-readable report.
    
    Args:
        evaluation: The evaluation dictionary returned by SVGCritic.evaluate()
        
    Returns:
        A formatted string with the evaluation report
    """
    report = [
        "# SVG Design Evaluation Report",
        "",
        f"## Overall Score: {evaluation['overall_score']}/100",
        "",
    ]
    
    # Critical issues
    if evaluation['critical_issues']:
        report.append("## Critical Issues")
        for issue in evaluation['critical_issues']:
            report.append(f"- **{issue['severity'].upper()}**: Overlap between elements {' and '.join(issue['elements'])}")
        report.append("")
    else:
        report.append("## Critical Issues\nNo critical issues detected! 👍\n")
    
    # Layout assessment
    report.append("## Layout Assessment")
    report.append(f"- **Balance Score**: {evaluation['layout_assessment']['balance_score']:.1f}/100")
    report.append("- **Quadrant Distribution**:")
    for q, count in evaluation['layout_assessment']['quadrant_distribution'].items():
        report.append(f"  - {q.upper()}: {count} elements")
    
    if evaluation['layout_assessment']['suggestions']:
        report.append("- **Suggestions**:")
        for suggestion in evaluation['layout_assessment']['suggestions']:
            report.append(f"  - {suggestion}")
    report.append("")
    
    # Color harmony
    report.append("## Color Harmony")
    report.append(f"- **Unique Colors**: {evaluation['color_harmony']['unique_colors']}")
    report.append(f"- **Palette Adherence**: {evaluation['color_harmony']['palette_adherence']:.1f}%")
    
    if evaluation['color_harmony']['suggestions']:
        report.append("- **Suggestions**:")
        for suggestion in evaluation['color_harmony']['suggestions']:
            report.append(f"  - {suggestion}")
    report.append("")
    
    # Visual hierarchy
    report.append("## Visual Hierarchy")
    report.append(f"- **Score**: {evaluation['visual_hierarchy']['score']}/100")
    if 'size_ratio' in evaluation['visual_hierarchy']:
        report.append(f"- **Size Ratio (largest:smallest)**: {evaluation['visual_hierarchy']['size_ratio']:.1f}x")
    
    if evaluation['visual_hierarchy']['suggestions']:
        report.append("- **Suggestions**:")
        for suggestion in evaluation['visual_hierarchy']['suggestions']:
            report.append(f"  - {suggestion}")
    report.append("")
    
    # Accessibility
    report.append("## Accessibility")
    report.append(f"- **Score**: {evaluation['accessibility']['score']:.1f}/100")
    report.append(f"- **Font Size Score**: {evaluation['accessibility']['font_size_score']:.1f}/100")
    report.append(f"- **Contrast Issues**: {evaluation['accessibility']['contrast_issues']}")
    
    if evaluation['accessibility']['suggestions']:
        report.append("- **Suggestions**:")
        for suggestion in evaluation['accessibility']['suggestions']:
            report.append(f"  - {suggestion}")
    report.append("")
    
    # Suggested code changes
    if evaluation['suggested_code_changes']:
        report.append("## Suggested Code Improvements")
        for suggestion in evaluation['suggested_code_changes']:
            report.append(f"- **{suggestion['type'].title()}**: {suggestion['issue']}")
            report.append(f"  - Suggestion: {suggestion['suggestion']}")
        report.append("")
    
    return "\n".join(report)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python svg_critic.py <svg_file_path>")
        sys.exit(1)
    
    svg_path = sys.argv[1]
    critic = SVGCritic(svg_path)
    evaluation = critic.evaluate()
    
    # Output human-readable report
    report = generate_human_readable_report(evaluation)
    print(report)
    
    # Output JSON for programmatic use
    # with open(f"{svg_path}.evaluation.json", "w") as f:
    #     json.dump(evaluation, f, indent=2)