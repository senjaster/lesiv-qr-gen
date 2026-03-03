"""Tests for QR Generator module."""

import pytest
from PIL import Image
from src.core.qr_generator import QRGenerator


class TestQRGenerator:
    """Test QRGenerator class."""
    
    def test_init_default(self):
        """Test initialization with default error correction."""
        gen = QRGenerator()
        assert gen.error_correction is not None
    
    def test_init_custom_error_correction(self):
        """Test initialization with custom error correction levels."""
        for level in ["L", "M", "Q", "H"]:
            gen = QRGenerator(error_correction=level)
            assert gen.error_correction is not None
    
    def test_init_invalid_error_correction(self):
        """Test initialization with invalid error correction."""
        with pytest.raises(ValueError, match="Invalid error correction level"):
            QRGenerator(error_correction="X")
    
    def test_generate_url(self):
        """Test URL generation."""
        gen = QRGenerator()
        url = gen.generate_url(12345)
        assert url == "https://qr.thermoelectrica.ru?id=12345"
        
        url = gen.generate_url(1)
        assert url == "https://qr.thermoelectrica.ru?id=1"
    
    def test_generate_qr_code(self):
        """Test QR code generation."""
        gen = QRGenerator()
        img = gen.generate(12345, size_mm=20.0, dpi=300)
        
        # Check it's a PIL Image
        assert isinstance(img, Image.Image)
        
        # Check size is correct (20mm at 300 DPI)
        expected_pixels = int((20.0 / 25.4) * 300)
        assert img.size == (expected_pixels, expected_pixels)
    
    def test_generate_different_sizes(self):
        """Test QR code generation with different sizes."""
        gen = QRGenerator()
        
        # Test 10mm
        img1 = gen.generate(1, size_mm=10.0, dpi=300)
        expected_pixels_1 = int((10.0 / 25.4) * 300)
        assert img1.size == (expected_pixels_1, expected_pixels_1)
        
        # Test 30mm
        img2 = gen.generate(2, size_mm=30.0, dpi=300)
        expected_pixels_2 = int((30.0 / 25.4) * 300)
        assert img2.size == (expected_pixels_2, expected_pixels_2)
        
        # Verify different sizes
        assert img1.size != img2.size
    
    def test_generate_different_dpi(self):
        """Test QR code generation with different DPI."""
        gen = QRGenerator()
        
        # Test 150 DPI
        img1 = gen.generate(1, size_mm=20.0, dpi=150)
        expected_pixels_1 = int((20.0 / 25.4) * 150)
        assert img1.size == (expected_pixels_1, expected_pixels_1)
        
        # Test 600 DPI
        img2 = gen.generate(2, size_mm=20.0, dpi=600)
        expected_pixels_2 = int((20.0 / 25.4) * 600)
        assert img2.size == (expected_pixels_2, expected_pixels_2)
        
        # Verify different sizes
        assert img1.size != img2.size
    
    def test_generate_batch(self):
        """Test batch QR code generation."""
        gen = QRGenerator()
        qr_ids = [1, 2, 3, 4, 5]
        
        images = gen.generate_batch(qr_ids, size_mm=20.0, dpi=300)
        
        # Check all IDs are present
        assert len(images) == len(qr_ids)
        for qr_id in qr_ids:
            assert qr_id in images
            assert isinstance(images[qr_id], Image.Image)
    
    def test_generate_unique_codes(self):
        """Test that different IDs generate different QR codes."""
        gen = QRGenerator()
        
        img1 = gen.generate(1, size_mm=20.0, dpi=300)
        img2 = gen.generate(2, size_mm=20.0, dpi=300)
        
        # Convert to bytes and compare
        import io
        buf1 = io.BytesIO()
        buf2 = io.BytesIO()
        img1.save(buf1, format='PNG')
        img2.save(buf2, format='PNG')
        
        # Different IDs should produce different images
        assert buf1.getvalue() != buf2.getvalue()
