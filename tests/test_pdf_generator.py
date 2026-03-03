"""Tests for PDF Generator module."""

import pytest
from pathlib import Path
from PIL import Image
from src.core.pdf_generator import PDFGenerator
from src.core.pdf_processor import PDFProcessor
from src.core.csv_parser import QRPosition
from src.core.qr_generator import QRGenerator
from src.core.config_manager import ConfigManager


class TestPDFGenerator:
    """Test PDFGenerator class."""
    
    @pytest.fixture
    def sample_pdf(self, tmp_path):
        """Create a sample PDF file."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        
        pdf_file = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf_file), pagesize=A4)
        c.drawString(100, 750, "Test PDF")
        c.save()
        return str(pdf_file)
    
    @pytest.fixture
    def pdf_processor(self, sample_pdf):
        """Create PDF processor."""
        return PDFProcessor(sample_pdf)
    
    @pytest.fixture
    def qr_generator(self):
        """Create QR generator."""
        return QRGenerator(base_url=ConfigManager.DEFAULT_QR_BASE_URL)
    
    @pytest.fixture
    def sample_qr_positions(self):
        """Create sample QR positions."""
        return [
            QRPosition(x_mm=50.0, y_mm=50.0, size_mm=20.0, rotation_deg=0),
            QRPosition(x_mm=160.0, y_mm=50.0, size_mm=20.0, rotation_deg=0),
            QRPosition(x_mm=105.0, y_mm=148.5, size_mm=25.0, rotation_deg=0),
        ]
    
    def test_init(self, pdf_processor):
        """Test PDF generator initialization."""
        generator = PDFGenerator(pdf_processor)
        
        assert generator.pdf_processor == pdf_processor
        assert generator.page_width_mm > 0
        assert generator.page_height_mm > 0
    
    def test_create_page_basic(self, pdf_processor, qr_generator, sample_qr_positions, tmp_path):
        """Test creating a basic PDF page."""
        generator = PDFGenerator(pdf_processor)
        
        # Generate QR images
        qr_images = {}
        for idx, pos in enumerate(sample_qr_positions):
            qr_images[idx] = qr_generator.generate(1000 + idx, pos.size_mm)
        
        # Create output path
        output_path = tmp_path / "output.pdf"
        
        # Generate PDF
        generator.create_page(sample_qr_positions, qr_images, str(output_path))
        
        # Verify PDF was created
        assert output_path.exists()
        assert output_path.stat().st_size > 0
    
    def test_create_page_with_rotation(self, pdf_processor, qr_generator, tmp_path):
        """Test creating PDF with rotated QR codes."""
        generator = PDFGenerator(pdf_processor)
        
        # Create positions with rotation
        positions = [
            QRPosition(x_mm=50.0, y_mm=50.0, size_mm=20.0, rotation_deg=45),
            QRPosition(x_mm=160.0, y_mm=50.0, size_mm=20.0, rotation_deg=90),
        ]
        
        # Generate QR images
        qr_images = {}
        for idx, pos in enumerate(positions):
            qr_images[idx] = qr_generator.generate(2000 + idx, pos.size_mm)
        
        # Create output path
        output_path = tmp_path / "rotated.pdf"
        
        # Generate PDF
        generator.create_page(positions, qr_images, str(output_path))
        
        # Verify PDF was created
        assert output_path.exists()
        assert output_path.stat().st_size > 0
    
    def test_create_page_mismatch_positions_images(self, pdf_processor, qr_generator, sample_qr_positions, tmp_path):
        """Test error when positions and images don't match."""
        generator = PDFGenerator(pdf_processor)
        
        # Create fewer images than positions
        qr_images = {
            0: qr_generator.generate(1, 20.0),
        }
        
        output_path = tmp_path / "output.pdf"
        
        with pytest.raises(ValueError, match="Mismatch"):
            generator.create_page(sample_qr_positions, qr_images, str(output_path))
    
    def test_create_page_missing_image(self, pdf_processor, qr_generator, sample_qr_positions, tmp_path):
        """Test error when image is missing for a position."""
        generator = PDFGenerator(pdf_processor)
        
        # Create images with wrong indices
        qr_images = {
            0: qr_generator.generate(1, 20.0),
            1: qr_generator.generate(2, 20.0),
            99: qr_generator.generate(3, 25.0),  # Wrong index
        }
        
        output_path = tmp_path / "output.pdf"
        
        with pytest.raises(IOError, match="Failed to create PDF"):
            generator.create_page(sample_qr_positions, qr_images, str(output_path))
    
    def test_create_page_creates_directory(self, pdf_processor, qr_generator, sample_qr_positions, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        generator = PDFGenerator(pdf_processor)
        
        # Generate QR images
        qr_images = {}
        for idx, pos in enumerate(sample_qr_positions):
            qr_images[idx] = qr_generator.generate(3000 + idx, pos.size_mm)
        
        # Create output path in non-existent directory
        output_path = tmp_path / "subdir" / "nested" / "output.pdf"
        
        # Generate PDF
        generator.create_page(sample_qr_positions, qr_images, str(output_path))
        
        # Verify PDF was created
        assert output_path.exists()
        assert output_path.parent.exists()
    
    def test_create_multiple_pages(self, pdf_processor, qr_generator, sample_qr_positions, tmp_path):
        """Test creating multiple PDF pages."""
        generator = PDFGenerator(pdf_processor)
        
        # Prepare data for 3 pages
        pages_data = []
        for page_num in range(3):
            qr_images = {}
            for idx, pos in enumerate(sample_qr_positions):
                qr_id = (page_num * 100) + idx
                qr_images[idx] = qr_generator.generate(qr_id, pos.size_mm)
            
            output_path = tmp_path / f"page_{page_num}.pdf"
            pages_data.append((sample_qr_positions, qr_images, str(output_path)))
        
        # Generate all pages
        created_files = generator.create_multiple_pages(pages_data)
        
        # Verify all files were created
        assert len(created_files) == 3
        for file_path in created_files:
            assert Path(file_path).exists()
            assert Path(file_path).stat().st_size > 0
    
    def test_create_page_different_sizes(self, pdf_processor, qr_generator, tmp_path):
        """Test creating PDF with different QR code sizes."""
        generator = PDFGenerator(pdf_processor)
        
        # Create positions with different sizes
        positions = [
            QRPosition(x_mm=50.0, y_mm=50.0, size_mm=10.0, rotation_deg=0),
            QRPosition(x_mm=105.0, y_mm=100.0, size_mm=20.0, rotation_deg=0),
            QRPosition(x_mm=160.0, y_mm=150.0, size_mm=30.0, rotation_deg=0),
        ]
        
        # Generate QR images with matching sizes
        qr_images = {}
        for idx, pos in enumerate(positions):
            qr_images[idx] = qr_generator.generate(4000 + idx, pos.size_mm)
        
        # Create output path
        output_path = tmp_path / "different_sizes.pdf"
        
        # Generate PDF
        generator.create_page(positions, qr_images, str(output_path))
        
        # Verify PDF was created
        assert output_path.exists()
        assert output_path.stat().st_size > 0
