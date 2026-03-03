"""PDF Generator Module

Creates PDF files with embedded SVG backgrounds and QR codes.
"""

from fpdf import FPDF
from PIL import Image
from pathlib import Path
from typing import Dict, List
import tempfile
import math

from .svg_processor import SVGProcessor
from .csv_parser import QRPosition


class PDFGenerator:
    """Generate PDF files with SVG and QR codes."""
    
    def __init__(self, svg_processor: SVGProcessor):
        """Initialize PDF generator.
        
        Args:
            svg_processor: SVGProcessor instance with loaded SVG
        """
        self.svg_processor = svg_processor
        self.page_width_mm, self.page_height_mm = svg_processor.get_page_dimensions()
    
    def create_page(
        self,
        qr_positions: List[QRPosition],
        qr_images: Dict[int, Image.Image],
        output_path: str
    ) -> None:
        """Create a PDF page with SVG background and QR codes.
        
        Args:
            qr_positions: List of QR position specifications
            qr_images: Dictionary mapping position index to QR code images
            output_path: Path where PDF should be saved
            
        Raises:
            ValueError: If positions and images don't match
            IOError: If PDF cannot be created
        """
        if len(qr_positions) != len(qr_images):
            raise ValueError(
                f"Mismatch: {len(qr_positions)} positions but {len(qr_images)} images"
            )
        
        # Create PDF with custom page size
        pdf = FPDF(unit='mm', format=(self.page_width_mm, self.page_height_mm))
        pdf.add_page()
        
        # Add SVG as background
        svg_path = self.svg_processor.get_svg_path()
        try:
            # fpdf2 supports SVG directly
            pdf.image(
                svg_path,
                x=0,
                y=0,
                w=self.page_width_mm,
                h=self.page_height_mm
            )
        except Exception as e:
            raise IOError(f"Failed to embed SVG: {e}")
        
        # Add QR codes at specified positions
        for idx, position in enumerate(qr_positions):
            if idx not in qr_images:
                raise ValueError(f"Missing QR image for position {idx}")
            
            qr_img = qr_images[idx]
            
            # Save QR image to temporary file (fpdf needs file path)
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                qr_img.save(tmp.name, 'PNG')
                tmp_path = tmp.name
            
            try:
                # Calculate top-left corner from center position
                x_topleft = position.x_mm - (position.size_mm / 2)
                y_topleft = position.y_mm - (position.size_mm / 2)
                
                # Handle rotation if needed
                if position.rotation_deg != 0:
                    # fpdf2 doesn't support image rotation directly
                    # We need to rotate the image before embedding
                    rotated_img = qr_img.rotate(
                        -position.rotation_deg,  # Negative for clockwise
                        expand=True,
                        fillcolor='white'
                    )
                    
                    # Save rotated image
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_rot:
                        rotated_img.save(tmp_rot.name, 'PNG')
                        tmp_rot_path = tmp_rot.name
                    
                    # Calculate new size after rotation
                    angle_rad = math.radians(position.rotation_deg)
                    new_width = abs(position.size_mm * math.cos(angle_rad)) + \
                                abs(position.size_mm * math.sin(angle_rad))
                    new_height = abs(position.size_mm * math.sin(angle_rad)) + \
                                 abs(position.size_mm * math.cos(angle_rad))
                    
                    # Adjust position to keep center the same
                    x_topleft = position.x_mm - (new_width / 2)
                    y_topleft = position.y_mm - (new_height / 2)
                    
                    pdf.image(
                        tmp_rot_path,
                        x=x_topleft,
                        y=y_topleft,
                        w=new_width,
                        h=new_height
                    )
                    
                    # Clean up rotated temp file
                    Path(tmp_rot_path).unlink(missing_ok=True)
                else:
                    # No rotation needed
                    pdf.image(
                        tmp_path,
                        x=x_topleft,
                        y=y_topleft,
                        w=position.size_mm,
                        h=position.size_mm
                    )
            finally:
                # Clean up temp file
                Path(tmp_path).unlink(missing_ok=True)
        
        # Save PDF
        try:
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            pdf.output(output_path)
        except Exception as e:
            raise IOError(f"Failed to save PDF: {e}")
    
    def create_multiple_pages(
        self,
        pages_data: List[tuple[List[QRPosition], Dict[int, Image.Image], str]]
    ) -> List[str]:
        """Create multiple PDF pages.
        
        Args:
            pages_data: List of tuples (qr_positions, qr_images, output_path)
            
        Returns:
            List of created file paths
        """
        created_files = []
        
        for qr_positions, qr_images, output_path in pages_data:
            self.create_page(qr_positions, qr_images, output_path)
            created_files.append(output_path)
        
        return created_files
