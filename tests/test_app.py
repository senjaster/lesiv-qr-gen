"""Tests for main application core."""

import pytest
from pathlib import Path
from src.core.app import QRCodeApp, ValidationError, GenerationError
from src.core.config_manager import ConfigManager


class TestQRCodeApp:
    """Test QRCodeApp class."""
    
    @pytest.fixture
    def sample_svg(self, tmp_path):
        """Create a sample SVG file."""
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 210 297">
    <rect width="210" height="297" fill="#f0f0f0"/>
</svg>'''
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)
        return str(svg_file)
    
    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create a sample CSV file."""
        csv_content = """x_mm,y_mm,size_mm,rotation_deg
50.0,50.0,20.0,0
160.0,50.0,20.0,0"""
        csv_file = tmp_path / "positions.csv"
        csv_file.write_text(csv_content)
        return str(csv_file)
    
    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create output directory."""
        output = tmp_path / "output"
        output.mkdir()
        return str(output)
    
    @pytest.fixture
    def config_manager(self, tmp_path):
        """Create config manager."""
        config_path = tmp_path / "test_config.ini"
        return ConfigManager(str(config_path))
    
    def test_init_default(self):
        """Test initialization with default config."""
        app = QRCodeApp()
        assert app.config_manager is not None
        assert app.qr_generator is not None
    
    def test_init_with_config(self, config_manager):
        """Test initialization with custom config."""
        app = QRCodeApp(config_manager)
        assert app.config_manager == config_manager
    
    def test_validate_inputs_valid(self, sample_svg, sample_csv, output_dir):
        """Test validation with valid inputs."""
        app = QRCodeApp()
        # Should not raise
        app.validate_inputs(sample_svg, sample_csv, 210.0, 5, output_dir)
    
    def test_validate_inputs_svg_not_found(self, sample_csv, output_dir):
        """Test validation with non-existent SVG."""
        app = QRCodeApp()
        with pytest.raises(ValidationError, match="SVG file not found"):
            app.validate_inputs("nonexistent.svg", sample_csv, 210.0, 5, output_dir)
    
    def test_validate_inputs_svg_not_svg_extension(self, sample_csv, output_dir, tmp_path):
        """Test validation with non-SVG file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not an svg")
        
        app = QRCodeApp()
        with pytest.raises(ValidationError, match="File is not an SVG"):
            app.validate_inputs(str(txt_file), sample_csv, 210.0, 5, output_dir)
    
    def test_validate_inputs_csv_not_found(self, sample_svg, output_dir):
        """Test validation with non-existent CSV."""
        app = QRCodeApp()
        with pytest.raises(ValidationError, match="CSV file not found"):
            app.validate_inputs(sample_svg, "nonexistent.csv", 210.0, 5, output_dir)
    
    def test_validate_inputs_csv_not_csv_extension(self, sample_svg, output_dir, tmp_path):
        """Test validation with non-CSV file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a csv")
        
        app = QRCodeApp()
        with pytest.raises(ValidationError, match="File is not a CSV"):
            app.validate_inputs(sample_svg, str(txt_file), 210.0, 5, output_dir)
    
    def test_validate_inputs_invalid_page_width(self, sample_svg, sample_csv, output_dir):
        """Test validation with invalid page width."""
        app = QRCodeApp()
        
        with pytest.raises(ValidationError, match="Page width must be positive"):
            app.validate_inputs(sample_svg, sample_csv, 0, 5, output_dir)
        
        with pytest.raises(ValidationError, match="Page width must be positive"):
            app.validate_inputs(sample_svg, sample_csv, -10, 5, output_dir)
        
        with pytest.raises(ValidationError, match="Page width too large"):
            app.validate_inputs(sample_svg, sample_csv, 2000, 5, output_dir)
    
    def test_validate_inputs_invalid_num_pages(self, sample_svg, sample_csv, output_dir):
        """Test validation with invalid number of pages."""
        app = QRCodeApp()
        
        with pytest.raises(ValidationError, match="Number of pages must be positive"):
            app.validate_inputs(sample_svg, sample_csv, 210.0, 0, output_dir)
        
        with pytest.raises(ValidationError, match="Number of pages must be positive"):
            app.validate_inputs(sample_svg, sample_csv, 210.0, -5, output_dir)
        
        with pytest.raises(ValidationError, match="Number of pages too large"):
            app.validate_inputs(sample_svg, sample_csv, 210.0, 20000, output_dir)
    
    def test_validate_inputs_creates_output_dir(self, sample_svg, sample_csv, tmp_path):
        """Test that validation creates output directory if it doesn't exist."""
        app = QRCodeApp()
        output_dir = tmp_path / "new_output"
        
        assert not output_dir.exists()
        app.validate_inputs(sample_svg, sample_csv, 210.0, 5, str(output_dir))
        assert output_dir.exists()
    
    def test_generate_pages_single_page(self, sample_svg, sample_csv, output_dir, config_manager):
        """Test generating a single page."""
        app = QRCodeApp(config_manager)
        
        files = app.generate_pages(sample_svg, sample_csv, 210.0, 1, output_dir)
        
        assert len(files) == 1
        assert Path(files[0]).exists()
        assert files[0].endswith('.pdf')
    
    def test_generate_pages_multiple_pages(self, sample_svg, sample_csv, output_dir, config_manager):
        """Test generating multiple pages."""
        app = QRCodeApp(config_manager)
        
        files = app.generate_pages(sample_svg, sample_csv, 210.0, 3, output_dir)
        
        assert len(files) == 3
        for file_path in files:
            assert Path(file_path).exists()
            assert file_path.endswith('.pdf')
    
    def test_generate_pages_with_progress_callback(self, sample_svg, sample_csv, output_dir, config_manager):
        """Test generation with progress callback."""
        app = QRCodeApp(config_manager)
        
        progress_calls = []
        
        def progress_callback(current, total, message):
            progress_calls.append((current, total, message))
        
        files = app.generate_pages(
            sample_svg, sample_csv, 210.0, 2, output_dir,
            progress_callback=progress_callback
        )
        
        assert len(files) == 2
        assert len(progress_calls) > 0
        
        # Check that progress was reported
        assert any(call[0] == 2 and call[1] == 2 for call in progress_calls)
    
    def test_generate_pages_saves_config(self, sample_svg, sample_csv, output_dir, config_manager):
        """Test that generation saves configuration."""
        app = QRCodeApp(config_manager)
        
        app.generate_pages(sample_svg, sample_csv, 210.0, 1, output_dir)
        
        # Check config was saved
        assert config_manager.get("svg_path") == sample_svg
        assert config_manager.get("csv_path") == sample_csv
        assert config_manager.get("output_folder") == output_dir
        assert float(config_manager.get("page_width_mm")) == 210.0
        assert int(config_manager.get("num_pages")) == 1
    
    def test_generate_pages_invalid_svg(self, sample_csv, output_dir, tmp_path, config_manager):
        """Test generation with invalid SVG."""
        # Create invalid SVG
        invalid_svg = tmp_path / "invalid.svg"
        invalid_svg.write_text("not valid svg content")
        
        app = QRCodeApp(config_manager)
        
        with pytest.raises(ValidationError, match="Failed to process SVG"):
            app.generate_pages(str(invalid_svg), sample_csv, 210.0, 1, output_dir)
    
    def test_generate_pages_invalid_csv(self, sample_svg, output_dir, tmp_path, config_manager):
        """Test generation with invalid CSV."""
        # Create invalid CSV
        invalid_csv = tmp_path / "invalid.csv"
        invalid_csv.write_text("not,valid,csv\n1,2,3")
        
        app = QRCodeApp(config_manager)
        
        with pytest.raises(ValidationError, match="Failed to parse CSV"):
            app.generate_pages(sample_svg, str(invalid_csv), 210.0, 1, output_dir)
    
    def test_generate_pages_empty_csv(self, sample_svg, output_dir, tmp_path, config_manager):
        """Test generation with empty CSV."""
        # Create empty CSV
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("x_mm,y_mm,size_mm,rotation_deg\n")
        
        app = QRCodeApp(config_manager)
        
        with pytest.raises(ValidationError, match="Failed to parse CSV"):
            app.generate_pages(sample_svg, str(empty_csv), 210.0, 1, output_dir)
    
    def test_generate_pages_qr_outside_bounds(self, sample_svg, output_dir, tmp_path, config_manager):
        """Test generation with QR positions outside page bounds."""
        # Create CSV with out-of-bounds position
        csv_content = """x_mm,y_mm,size_mm,rotation_deg
500.0,500.0,20.0,0"""
        csv_file = tmp_path / "out_of_bounds.csv"
        csv_file.write_text(csv_content)
        
        app = QRCodeApp(config_manager)
        
        with pytest.raises((ValidationError, GenerationError)):
            app.generate_pages(sample_svg, str(csv_file), 210.0, 1, output_dir)
    
    def test_get_last_config(self, config_manager):
        """Test getting last configuration."""
        config_manager.set("svg_path", "/path/to/file.svg")
        config_manager.set("csv_path", "/path/to/positions.csv")
        config_manager.set("output_folder", "/path/to/output")
        config_manager.set("page_width_mm", 210.0)
        config_manager.set("num_pages", 10)
        config_manager.save()
        
        app = QRCodeApp(config_manager)
        config = app.get_last_config()
        
        assert config["svg_path"] == "/path/to/file.svg"
        assert config["csv_path"] == "/path/to/positions.csv"
        assert config["output_folder"] == "/path/to/output"
        assert float(config["page_width_mm"]) == 210.0
        assert int(config["num_pages"]) == 10
    
    def test_get_last_config_defaults(self, tmp_path):
        """Test getting configuration with defaults."""
        # Create a fresh config manager with no saved values
        config_path = tmp_path / "fresh_config.ini"
        fresh_config = ConfigManager(str(config_path))
        app = QRCodeApp(fresh_config)
        config = app.get_last_config()
        
        # Check that defaults are returned for empty config
        assert config["svg_path"] == ""
        assert config["csv_path"] == ""
        assert config["output_folder"] == ""
        # page_width_mm and num_pages will have default values
        assert "page_width_mm" in config
        assert "num_pages" in config
