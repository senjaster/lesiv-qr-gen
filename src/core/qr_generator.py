"""QR Code Generator Module

Generates QR codes with unique IDs for embedding in PDFs.
"""

import qrcode
import qrcode.constants
import qrcode.image.pil
from PIL import Image
from typing import Optional


class QRGenerator:
    """Generate QR codes with unique URLs."""
    
    def __init__(self, error_correction: str = "M", base_url: Optional[str] = None):
        """Initialize QR generator.
        
        Args:
            error_correction: Error correction level (L, M, Q, H). Default is M (15%).
            base_url: Base URL for QR codes. Must be provided.
        """
        self.error_correction_map = {
            "L": qrcode.constants.ERROR_CORRECT_L,  # 7%
            "M": qrcode.constants.ERROR_CORRECT_M,  # 15%
            "Q": qrcode.constants.ERROR_CORRECT_Q,  # 25%
            "H": qrcode.constants.ERROR_CORRECT_H,  # 30%
        }
        
        if error_correction not in self.error_correction_map:
            raise ValueError(f"Invalid error correction level: {error_correction}")
        
        self.error_correction = self.error_correction_map[error_correction]
        
        if base_url is None:
            raise ValueError("base_url must be provided")
        
        self.base_url = base_url
    
    def generate_url(self, qr_id: int) -> str:
        """Generate URL for QR code.
        
        Args:
            qr_id: Unique identifier for the QR code
            
        Returns:
            Complete URL string
        """
        return f"{self.base_url}{qr_id}"
    
    def generate(self, qr_id: int, size_mm: float, dpi: int = 300) -> Image.Image:
        """Generate QR code image.
        
        Args:
            qr_id: Unique identifier for the QR code
            size_mm: Desired size in millimeters (square)
            dpi: Dots per inch for resolution (default: 300)
            
        Returns:
            PIL Image object containing the QR code
        """
        url = self.generate_url(qr_id)
        
        # Calculate pixel size from mm and DPI
        # 1 inch = 25.4 mm
        size_inches = size_mm / 25.4
        size_pixels = int(size_inches * dpi)
        
        # Create QR code with PIL image factory
        qr = qrcode.QRCode(
            version=None,  # Auto-determine version
            error_correction=self.error_correction,
            box_size=10,  # Size of each box in pixels (will be scaled)
            border=0,  # No border (we'll handle positioning in PDF)
            image_factory=qrcode.image.pil.PilImage,
        )
        
        qr.add_data(url)
        qr.make(fit=True)
        
        # Generate PIL image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Resize to exact pixel dimensions
        img = img.resize((size_pixels, size_pixels), Image.Resampling.LANCZOS)
        
        return img
    
    def generate_batch(self, qr_ids: list[int], size_mm: float, dpi: int = 300) -> dict[int, Image.Image]:
        """Generate multiple QR codes.
        
        Args:
            qr_ids: List of unique identifiers
            size_mm: Desired size in millimeters (square)
            dpi: Dots per inch for resolution (default: 300)
            
        Returns:
            Dictionary mapping QR IDs to PIL Image objects
        """
        return {qr_id: self.generate(qr_id, size_mm, dpi) for qr_id in qr_ids}
