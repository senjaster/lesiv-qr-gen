"""PDF Generator Module

Creates PDF files by merging template PDFs with QR code overlays.
"""

from PIL import Image
from pathlib import Path
from typing import Dict, List
from io import BytesIO
import math

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from .pdf_processor import PDFProcessor
from .csv_parser import QRPosition


class PDFGenerator:
    """Generate PDF files by merging templates with QR codes."""
    
    def __init__(self, pdf_processor: PDFProcessor):
        """Initialize PDF generator.
        
        Args:
            pdf_processor: PDFProcessor instance with loaded PDF template
        """
        self.pdf_processor = pdf_processor
        self.page_width_mm, self.page_height_mm = pdf_processor.get_page_dimensions_mm()
        self.page_width_points, self.page_height_points = pdf_processor.get_page_dimensions_points()
    
    def create_page(
        self,
        qr_positions: List[QRPosition],
        qr_images: Dict[int, Image.Image],
        output_path: str
    ) -> None:
        """Create a PDF page by merging template with QR codes.
        
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
        
        try:
            # Read the template PDF
            template_reader = self.pdf_processor.get_pdf_reader()
            template_page = template_reader.pages[0]
            
            # Create a new PDF with QR codes using reportlab
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=(self.page_width_points, self.page_height_points))
            
            # Add QR codes at specified positions
            for idx, position in enumerate(qr_positions):
                if idx not in qr_images:
                    raise ValueError(f"Missing QR image for position {idx}")
                
                qr_img = qr_images[idx]
                
                # Convert mm to points for reportlab
                x_points = self.pdf_processor.mm_to_points(position.x_mm)
                y_points = self.pdf_processor.mm_to_points(position.y_mm)
                size_points = self.pdf_processor.mm_to_points(position.size_mm)
                
                # Calculate top-left corner from center position
                # Note: PDF coordinate system has origin at bottom-left
                x_topleft = x_points - (size_points / 2)
                y_topleft = self.page_height_points - y_points - (size_points / 2)
                
                # Handle rotation if needed
                if position.rotation_deg != 0:
                    # Save canvas state
                    can.saveState()
                    
                    # Translate to center of QR code
                    can.translate(x_points, self.page_height_points - y_points)
                    
                    # Rotate (reportlab uses degrees, positive is counter-clockwise)
                    can.rotate(-position.rotation_deg)  # Negative for clockwise
                    
                    # Draw image centered at origin
                    can.drawImage(
                        ImageReader(qr_img),
                        -size_points / 2,
                        -size_points / 2,
                        width=size_points,
                        height=size_points,
                        mask='auto'
                    )
                    
                    # Restore canvas state
                    can.restoreState()
                else:
                    # No rotation needed
                    can.drawImage(
                        ImageReader(qr_img),
                        x_topleft,
                        y_topleft,
                        width=size_points,
                        height=size_points,
                        mask='auto'
                    )
            
            # Save the QR codes layer
            can.save()
            
            # Merge: Overlay QR layer on top of template
            packet.seek(0)
            qr_reader = PdfReader(packet)
            qr_page = qr_reader.pages[0]
            
            # Merge the two PDF pages
            template_page.merge_page(qr_page)
            
            # Write output
            writer = PdfWriter()
            writer.add_page(template_page)
            
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
                
        except Exception as e:
            raise IOError(f"Failed to create PDF: {e}")
    
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
