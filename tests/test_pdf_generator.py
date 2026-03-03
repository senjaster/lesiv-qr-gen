"""Tests for PDF Generator module."""

import pytest
from pathlib import Path
from PIL import Image
from src.core.pdf_generator import PDFGenerator
from src.core.svg_processor import SVGProcessor
from src.core.csv_parser import QRPosition
from src.core.qr_generator import QRGenerator


class TestPDFGenerator:
    """Test PDFGenerator class."""
    
    @pytest.fixture
    def sample_svg(self, tmp_path):
        """Create a sample SVG file."""
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 210 297">
    <rect width="210" height="297" fill="lightblue"/>
    <text x="105" y="148.5" text-anchor="middle" font-size="20">Test SVG</text>
</svg>'''
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)
        return str(svg_file)
    
    @pytest.fixture
    def svg_processor(self, sample_svg):
        """Create SVG processor."""
        return SVGProcessor(sample_svg, 210.0)
    
    @pytest.fixture
    def qr_generator(self):
        """Create QR generator."""
        return QRGenerator()
    
    @pytest.fixture
    def sample_qr_positions(self):
        """Create sample QR positions."""
        return [
            QRPosition(x_mm=50.0, y_mm=50.0, size_mm=20.0, rotation_deg=0),
            QRPosition(x_mm=160.0, y_mm=50.0, size_mm=20.0, rotation_deg=0),
            QRPosition(x_mm=105.0, y_mm=148.5, size_mm=25.0, rotation_deg=0),
        ]
    
    def test_init(self, svg_processor):
        """Test PDF generator initialization."""
        generator = PDFGenerator(svg_processor)
        
        assert generator.svg_processor == svg_processor
        assert generator.page_width_mm == 210.0
        assert generator.page_height_mm == 297.0
    
    def test_create_page_basic(self, svg_processor, qr_generator, sample_qr_positions, tmp_path):
        """Test creating a basic PDF page."""
        generator = PDFGenerator(svg_processor)
        
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
    
    def test_create_page_with_rotation(self, svg_processor, qr_generator, tmp_path):
        """Test creating PDF with rotated QR codes."""
        generator = PDFGenerator(svg_processor)
        
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
    
    def test_create_page_mismatch_positions_images(self, svg_processor, qr_generator, sample_qr_positions, tmp_path):
        """Test error when positions and images don't match."""
        generator = PDFGenerator(svg_processor)
        
        # Create fewer images than positions
        qr_images = {
            0: qr_generator.generate(1, 20.0),
        }
        
        output_path = tmp_path / "output.pdf"
        
        with pytest.raises(ValueError, match="Mismatch"):
            generator.create_page(sample_qr_positions, qr_images, str(output_path))
    
    def test_create_page_missing_image(self, svg_processor, qr_generator, sample_qr_positions, tmp_path):
        """Test error when image is missing for a position."""
        generator = PDFGenerator(svg_processor)
        
        # Create images with wrong indices
        qr_images = {
            0: qr_generator.generate(1, 20.0),
            1: qr_generator.generate(2, 20.0),
            99: qr_generator.generate(3, 25.0),  # Wrong index
        }
        
        output_path = tmp_path / "output.pdf"
        
        with pytest.raises(ValueError, match="Missing QR image"):
            generator.create_page(sample_qr_positions, qr_images, str(output_path))
    
    def test_create_page_creates_directory(self, svg_processor, qr_generator, sample_qr_positions, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        generator = PDFGenerator(svg_processor)
        
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
    
    def test_create_multiple_pages(self, svg_processor, qr_generator, sample_qr_positions, tmp_path):
        """Test creating multiple PDF pages."""
        generator = PDFGenerator(svg_processor)
        
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
    
    def test_create_page_different_sizes(self, svg_processor, qr_generator, tmp_path):
        """Test creating PDF with different QR code sizes."""
        generator = PDFGenerator(svg_processor)
        
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
