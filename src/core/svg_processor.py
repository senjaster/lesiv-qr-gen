"""SVG Processor Module

Handles SVG file processing, scaling, and coordinate conversion.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple, Optional
import re


class SVGProcessor:
    """Process SVG files for PDF embedding."""
    
    # Conversion factor: 1 mm = 2.83465 points
    MM_TO_POINTS = 2.83465
    
    def __init__(self, svg_path: str, target_width_mm: float):
        """Initialize SVG processor.
        
        Args:
            svg_path: Path to SVG file
            target_width_mm: Target page width in millimeters
            
        Raises:
            FileNotFoundError: If SVG file doesn't exist
            ValueError: If SVG is invalid or target width is invalid
        """
        self.svg_path = Path(svg_path)
        if not self.svg_path.exists():
            raise FileNotFoundError(f"SVG file not found: {svg_path}")
        
        if target_width_mm <= 0:
            raise ValueError(f"Target width must be positive: {target_width_mm}")
        
        self.target_width_mm = target_width_mm
        self._parse_svg()
    
    def _parse_svg(self) -> None:
        """Parse SVG file and extract dimensions."""
        try:
            tree = ET.parse(self.svg_path)
            root = tree.getroot()
            
            # Remove namespace if present
            if '}' in root.tag:
                ns = root.tag.split('}')[0] + '}'
            else:
                ns = ''
            
            # Try to get dimensions from width/height attributes
            width_attr = root.get('width')
            height_attr = root.get('height')
            
            # Try to get viewBox
            viewbox_attr = root.get('viewBox')
            
            if viewbox_attr:
                # Parse viewBox: "min-x min-y width height"
                viewbox_parts = re.split(r'[\s,]+', viewbox_attr.strip())
                if len(viewbox_parts) >= 4:
                    self.viewbox_width = float(viewbox_parts[2])
                    self.viewbox_height = float(viewbox_parts[3])
                else:
                    raise ValueError("Invalid viewBox format")
            elif width_attr and height_attr:
                # Parse width and height (remove units if present)
                self.viewbox_width = self._parse_dimension(width_attr)
                self.viewbox_height = self._parse_dimension(height_attr)
            else:
                raise ValueError("SVG must have either viewBox or width/height attributes")
            
            # Calculate aspect ratio
            self.aspect_ratio = self.viewbox_height / self.viewbox_width
            
            # Calculate page height based on target width and aspect ratio
            self.page_height_mm = self.target_width_mm * self.aspect_ratio
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid SVG file: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing SVG: {e}")
    
    def _parse_dimension(self, dim_str: str) -> float:
        """Parse dimension string and convert to numeric value.
        
        Args:
            dim_str: Dimension string (e.g., "100", "100px", "100mm")
            
        Returns:
            Numeric value (units removed)
        """
        # Remove common units
        dim_str = dim_str.strip().lower()
        for unit in ['px', 'pt', 'mm', 'cm', 'in']:
            if dim_str.endswith(unit):
                dim_str = dim_str[:-len(unit)]
                break
        
        return float(dim_str)
    
    def get_page_dimensions(self) -> Tuple[float, float]:
        """Get page dimensions in millimeters.
        
        Returns:
            Tuple of (width_mm, height_mm)
        """
        return (self.target_width_mm, self.page_height_mm)
    
    def get_aspect_ratio(self) -> float:
        """Get SVG aspect ratio (height/width).
        
        Returns:
            Aspect ratio
        """
        return self.aspect_ratio
    
    def mm_to_points(self, mm: float) -> float:
        """Convert millimeters to PDF points.
        
        Args:
            mm: Value in millimeters
            
        Returns:
            Value in points
        """
        return mm * self.MM_TO_POINTS
    
    def get_svg_data(self) -> bytes:
        """Read SVG file content.
        
        Returns:
            SVG file content as bytes
        """
        return self.svg_path.read_bytes()
    
    def get_svg_path(self) -> str:
        """Get SVG file path.
        
        Returns:
            Path to SVG file as string
        """
        return str(self.svg_path)
