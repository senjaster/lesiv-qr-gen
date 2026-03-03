"""Main Application Core

Orchestrates all components to generate PDF files with QR codes.
"""

from pathlib import Path
from typing import Callable, List, Optional
import logging

from .config_manager import ConfigManager
from .id_manager import IDManager
from .csv_parser import CSVParser, QRPosition
from .qr_generator import QRGenerator
from .svg_processor import SVGProcessor
from .pdf_generator import PDFGenerator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QRCodeAppError(Exception):
    """Base exception for QRCodeApp errors."""
    pass


class ValidationError(QRCodeAppError):
    """Raised when input validation fails."""
    pass


class GenerationError(QRCodeAppError):
    """Raised when PDF generation fails."""
    pass


class QRCodeApp:
    """Main application for generating PDFs with QR codes."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the application.
        
        Args:
            config_manager: Optional ConfigManager instance. If None, creates default.
        """
        self.config_manager = config_manager or ConfigManager()
        self.qr_generator = QRGenerator(error_correction="M")
        logger.info("QRCodeApp initialized")
    
    def validate_inputs(
        self,
        svg_path: str,
        csv_path: str,
        page_width_mm: float,
        num_pages: int,
        output_root: str
    ) -> None:
        """Validate all input parameters.
        
        Args:
            svg_path: Path to SVG file
            csv_path: Path to CSV file with QR positions
            page_width_mm: Target page width in millimeters
            num_pages: Number of pages to generate
            output_root: Root output directory
            
        Raises:
            ValidationError: If any validation fails
        """
        # Validate SVG file
        svg_file = Path(svg_path)
        if not svg_file.exists():
            raise ValidationError(f"SVG file not found: {svg_path}")
        if not svg_file.is_file():
            raise ValidationError(f"SVG path is not a file: {svg_path}")
        if svg_file.suffix.lower() != '.svg':
            raise ValidationError(f"File is not an SVG: {svg_path}")
        
        # Validate CSV file
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise ValidationError(f"CSV file not found: {csv_path}")
        if not csv_file.is_file():
            raise ValidationError(f"CSV path is not a file: {csv_path}")
        if csv_file.suffix.lower() != '.csv':
            raise ValidationError(f"File is not a CSV: {csv_path}")
        
        # Validate page width
        if page_width_mm <= 0:
            raise ValidationError(f"Page width must be positive: {page_width_mm}")
        if page_width_mm > 1000:  # Sanity check
            raise ValidationError(f"Page width too large (max 1000mm): {page_width_mm}")
        
        # Validate number of pages
        if num_pages <= 0:
            raise ValidationError(f"Number of pages must be positive: {num_pages}")
        if num_pages > 10000:  # Sanity check
            raise ValidationError(f"Number of pages too large (max 10000): {num_pages}")
        
        # Validate output directory
        output_dir = Path(output_root)
        if output_dir.exists() and not output_dir.is_dir():
            raise ValidationError(f"Output path exists but is not a directory: {output_root}")
        
        # Try to create output directory if it doesn't exist
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValidationError(f"Cannot create output directory: {e}")
        
        # Check write permissions
        if not output_dir.exists() or not output_dir.is_dir():
            raise ValidationError(f"Output directory not accessible: {output_root}")
        
        logger.info("Input validation passed")
    
    def generate_pages(
        self,
        svg_path: str,
        csv_path: str,
        page_width_mm: float,
        num_pages: int,
        output_root: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[str]:
        """Generate PDF pages with QR codes.
        
        Args:
            svg_path: Path to SVG file
            csv_path: Path to CSV file with QR positions
            page_width_mm: Target page width in millimeters
            num_pages: Number of pages to generate
            output_root: Root output directory
            progress_callback: Optional callback function(current, total, message)
            
        Returns:
            List of generated PDF file paths
            
        Raises:
            ValidationError: If input validation fails
            GenerationError: If PDF generation fails
        """
        try:
            # Validate inputs
            logger.info("Validating inputs...")
            self.validate_inputs(svg_path, csv_path, page_width_mm, num_pages, output_root)
            
            if progress_callback:
                progress_callback(0, num_pages, "Validation complete")
            
            # Parse CSV for QR positions
            logger.info(f"Parsing CSV file: {csv_path}")
            try:
                qr_positions = CSVParser.parse(csv_path)
            except Exception as e:
                raise ValidationError(f"Failed to parse CSV: {e}")
            
            if not qr_positions:
                raise ValidationError("CSV file contains no QR positions")
            
            logger.info(f"Found {len(qr_positions)} QR positions")
            
            if progress_callback:
                progress_callback(0, num_pages, f"Loaded {len(qr_positions)} QR positions")
            
            # Process SVG
            logger.info(f"Processing SVG file: {svg_path}")
            try:
                svg_processor = SVGProcessor(svg_path, page_width_mm)
            except Exception as e:
                raise ValidationError(f"Failed to process SVG: {e}")
            
            page_width, page_height = svg_processor.get_page_dimensions()
            logger.info(f"Page dimensions: {page_width:.2f}mm x {page_height:.2f}mm")
            
            # Validate QR positions are within page bounds
            if not CSVParser.validate(qr_positions, page_width, page_height):
                raise ValidationError("Some QR positions are outside page bounds")
            
            if progress_callback:
                progress_callback(0, num_pages, "SVG processed successfully")
            
            # Initialize ID manager
            logger.info(f"Initializing ID manager for output: {output_root}")
            id_manager = IDManager(output_root)
            
            # Initialize PDF generator
            pdf_generator = PDFGenerator(svg_processor)
            
            # Generate pages
            generated_files = []
            
            for page_idx in range(num_pages):
                try:
                    # Get next page info
                    page_num, start_id = id_manager.get_next_page_info()
                    logger.info(f"Generating page {page_num} (starting ID: {start_id})")
                    
                    # Generate QR codes for this page
                    qr_ids = id_manager.generate_ids(len(qr_positions))
                    qr_images = {}
                    
                    for idx, (qr_id, pos) in enumerate(zip(qr_ids, qr_positions)):
                        qr_images[idx] = self.qr_generator.generate(qr_id, pos.size_mm)
                    
                    # Generate filename
                    filename = id_manager.format_filename(page_num, min(qr_ids), max(qr_ids))
                    output_path = id_manager.get_output_path() / filename
                    
                    # Create PDF
                    pdf_generator.create_page(qr_positions, qr_images, str(output_path))
                    
                    # Update page info for next iteration
                    id_manager.update_page_info(page_num, max(qr_ids))
                    
                    generated_files.append(str(output_path))
                    logger.info(f"Generated: {output_path.name}")
                    
                    if progress_callback:
                        progress_callback(
                            page_idx + 1,
                            num_pages,
                            f"Generated page {page_num}: {output_path.name}"
                        )
                
                except Exception as e:
                    error_msg = f"Failed to generate page {page_idx + 1}: {e}"
                    logger.error(error_msg)
                    raise GenerationError(error_msg)
            
            # Save configuration
            self.config_manager.set("svg_path", svg_path)
            self.config_manager.set("csv_path", csv_path)
            self.config_manager.set("output_folder", output_root)
            self.config_manager.set("page_width_mm", page_width_mm)
            self.config_manager.set("num_pages", num_pages)
            self.config_manager.save()
            
            logger.info(f"Successfully generated {len(generated_files)} PDF files")
            
            if progress_callback:
                progress_callback(num_pages, num_pages, "Generation complete!")
            
            return generated_files
        
        except (ValidationError, GenerationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Wrap unexpected exceptions
            error_msg = f"Unexpected error during generation: {e}"
            logger.error(error_msg, exc_info=True)
            raise GenerationError(error_msg)
    
    def get_last_config(self) -> dict:
        """Get last used configuration.
        
        Returns:
            Dictionary with configuration values
        """
        return {
            "svg_path": self.config_manager.get("svg_path", ""),
            "csv_path": self.config_manager.get("csv_path", ""),
            "output_folder": self.config_manager.get("output_folder", ""),
            "page_width_mm": self.config_manager.get("page_width_mm", 210.0),
            "num_pages": self.config_manager.get("num_pages", 1),
        }
