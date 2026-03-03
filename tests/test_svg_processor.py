"""Tests for SVG Processor module."""

import pytest
from pathlib import Path
from src.core.svg_processor import SVGProcessor


class TestSVGProcessor:
    """Test SVGProcessor class."""
    
    @pytest.fixture
    def sample_svg_with_viewbox(self, tmp_path):
        """Create a sample SVG file with viewBox."""
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 150">
    <rect width="100" height="150" fill="blue"/>
</svg>'''
        svg_file = tmp_path / "sample_viewbox.svg"
        svg_file.write_text(svg_content)
        return str(svg_file)
    
    @pytest.fixture
    def sample_svg_with_dimensions(self, tmp_path):
        """Create a sample SVG file with width/height."""
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="300">
    <rect width="200" height="300" fill="red"/>
</svg>'''
        svg_file = tmp_path / "sample_dimensions.svg"
        svg_file.write_text(svg_content)
        return str(svg_file)
    
    @pytest.fixture
    def sample_svg_with_units(self, tmp_path):
        """Create a sample SVG file with units."""
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="150mm">
    <rect width="100" height="150" fill="green"/>
</svg>'''
        svg_file = tmp_path / "sample_units.svg"
        svg_file.write_text(svg_content)
        return str(svg_file)
    
    def test_init_file_not_found(self):
        """Test initialization with non-existent file."""
        with pytest.raises(FileNotFoundError):
            SVGProcessor("nonexistent.svg", 210.0)
    
    def test_init_invalid_width(self, sample_svg_with_viewbox):
        """Test initialization with invalid target width."""
        with pytest.raises(ValueError, match="Target width must be positive"):
            SVGProcessor(sample_svg_with_viewbox, 0)
        
        with pytest.raises(ValueError, match="Target width must be positive"):
            SVGProcessor(sample_svg_with_viewbox, -10)
    
    def test_parse_svg_with_viewbox(self, sample_svg_with_viewbox):
        """Test parsing SVG with viewBox."""
        processor = SVGProcessor(sample_svg_with_viewbox, 210.0)
        
        assert processor.viewbox_width == 100
        assert processor.viewbox_height == 150
        assert processor.aspect_ratio == 1.5
        assert processor.target_width_mm == 210.0
        assert processor.page_height_mm == 315.0  # 210 * 1.5
    
    def test_parse_svg_with_dimensions(self, sample_svg_with_dimensions):
        """Test parsing SVG with width/height attributes."""
        processor = SVGProcessor(sample_svg_with_dimensions, 210.0)
        
        assert processor.viewbox_width == 200
        assert processor.viewbox_height == 300
        assert processor.aspect_ratio == 1.5
        assert processor.page_height_mm == 315.0
    
    def test_parse_svg_with_units(self, sample_svg_with_units):
        """Test parsing SVG with units in dimensions."""
        processor = SVGProcessor(sample_svg_with_units, 210.0)
        
        assert processor.viewbox_width == 100
        assert processor.viewbox_height == 150
        assert processor.aspect_ratio == 1.5
    
    def test_get_page_dimensions(self, sample_svg_with_viewbox):
        """Test getting page dimensions."""
        processor = SVGProcessor(sample_svg_with_viewbox, 210.0)
        width, height = processor.get_page_dimensions()
        
        assert width == 210.0
        assert height == 315.0
    
    def test_get_aspect_ratio(self, sample_svg_with_viewbox):
        """Test getting aspect ratio."""
        processor = SVGProcessor(sample_svg_with_viewbox, 210.0)
        ratio = processor.get_aspect_ratio()
        
        assert ratio == 1.5
    
    def test_mm_to_points(self, sample_svg_with_viewbox):
        """Test millimeter to points conversion."""
        processor = SVGProcessor(sample_svg_with_viewbox, 210.0)
        
        # 1 mm = 2.83465 points
        assert processor.mm_to_points(1.0) == pytest.approx(2.83465)
        assert processor.mm_to_points(10.0) == pytest.approx(28.3465)
        assert processor.mm_to_points(210.0) == pytest.approx(595.2765)
    
    def test_get_svg_data(self, sample_svg_with_viewbox):
        """Test getting SVG file data."""
        processor = SVGProcessor(sample_svg_with_viewbox, 210.0)
        data = processor.get_svg_data()
        
        assert isinstance(data, bytes)
        assert b'<svg' in data
        assert b'viewBox="0 0 100 150"' in data
    
    def test_get_svg_path(self, sample_svg_with_viewbox):
        """Test getting SVG file path."""
        processor = SVGProcessor(sample_svg_with_viewbox, 210.0)
        path = processor.get_svg_path()
        
        assert isinstance(path, str)
        assert Path(path).exists()
        assert path.endswith('.svg')
    
    def test_different_target_widths(self, sample_svg_with_viewbox):
        """Test with different target widths."""
        # A4 width
        processor1 = SVGProcessor(sample_svg_with_viewbox, 210.0)
        assert processor1.page_height_mm == 315.0
        
        # Letter width
        processor2 = SVGProcessor(sample_svg_with_viewbox, 215.9)
        assert processor2.page_height_mm == pytest.approx(323.85)
        
        # Custom width
        processor3 = SVGProcessor(sample_svg_with_viewbox, 100.0)
        assert processor3.page_height_mm == 150.0
    
    def test_parse_dimension_various_formats(self, sample_svg_with_viewbox):
        """Test dimension parsing with various formats."""
        processor = SVGProcessor(sample_svg_with_viewbox, 210.0)
        
        assert processor._parse_dimension("100") == 100.0
        assert processor._parse_dimension("100px") == 100.0
        assert processor._parse_dimension("100pt") == 100.0
        assert processor._parse_dimension("100mm") == 100.0
        assert processor._parse_dimension("100cm") == 100.0
        assert processor._parse_dimension("100in") == 100.0
        assert processor._parse_dimension("  100px  ") == 100.0
