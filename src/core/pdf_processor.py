"""PDF Processor Module

Handles PDF template file processing and dimension extraction.
"""

from pathlib import Path
from typing import Tuple
from pypdf import PdfReader


class PDFProcessor:
    """Process PDF template files for QR code embedding."""
    
    # Conversion factor: PDF uses points, 1 inch = 72 points, 1 inch = 25.4 mm
    POINTS_TO_MM = 25.4 / 72.0
    MM_TO_POINTS = 72.0 / 25.4
    
    def __init__(self, pdf_path: str):
        """Initialize PDF processor.
        
        Args:
            pdf_path: Path to PDF file
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF is invalid or has no pages
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if self.pdf_path.suffix.lower() != '.pdf':
            raise ValueError(f"File must be a PDF: {pdf_path}")
        
        self._parse_pdf()
    
    def _parse_pdf(self) -> None:
        """Parse PDF file and extract dimensions from first page."""
        try:
            reader = PdfReader(str(self.pdf_path))
            
            if len(reader.pages) == 0:
                raise ValueError("PDF file has no pages")
            
            # Get first page dimensions
            first_page = reader.pages[0]
            mediabox = first_page.mediabox
            
            # MediaBox gives dimensions in points
            self.width_points = float(mediabox.width)
            self.height_points = float(mediabox.height)
            
            # Convert to millimeters
            self.width_mm = self.width_points * self.POINTS_TO_MM
            self.height_mm = self.height_points * self.POINTS_TO_MM
            
            # Calculate aspect ratio
            self.aspect_ratio = self.height_mm / self.width_mm
            
        except Exception as e:
            raise ValueError(f"Error parsing PDF: {e}")
    
    def get_page_dimensions_mm(self) -> Tuple[float, float]:
        """Get page dimensions in millimeters.
        
        Returns:
            Tuple of (width_mm, height_mm)
        """
        return (self.width_mm, self.height_mm)
    
    def get_page_dimensions_points(self) -> Tuple[float, float]:
        """Get page dimensions in PDF points.
        
        Returns:
            Tuple of (width_points, height_points)
        """
        return (self.width_points, self.height_points)
    
    def get_aspect_ratio(self) -> float:
        """Get PDF aspect ratio (height/width).
        
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
    
    def points_to_mm(self, points: float) -> float:
        """Convert PDF points to millimeters.
        
        Args:
            points: Value in points
            
        Returns:
            Value in millimeters
        """
        return points * self.POINTS_TO_MM
    
    def get_pdf_path(self) -> str:
        """Get PDF file path.
        
        Returns:
            Path to PDF file as string
        """
        return str(self.pdf_path)
    
    def get_pdf_reader(self) -> PdfReader:
        """Get a PdfReader instance for the PDF file.
        
        Returns:
            PdfReader instance
        """
        return PdfReader(str(self.pdf_path))
