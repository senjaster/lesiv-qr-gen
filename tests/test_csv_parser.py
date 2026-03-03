"""Tests for CSVParser."""

import pytest
import tempfile
import csv
from pathlib import Path
from src.core.csv_parser import CSVParser, QRPosition


class TestQRPosition:
    """Test suite for QRPosition dataclass."""
    
    def test_valid_position(self):
        """Test creating a valid QR position."""
        pos = QRPosition(x_mm=100.0, y_mm=150.0, size_mm=20.0, rotation_deg=45.0)
        
        assert pos.x_mm == 100.0
        assert pos.y_mm == 150.0
        assert pos.size_mm == 20.0
        assert pos.rotation_deg == 45.0
    
    def test_invalid_size(self):
        """Test that negative or zero size raises ValueError."""
        with pytest.raises(ValueError, match="size must be positive"):
            QRPosition(x_mm=100.0, y_mm=150.0, size_mm=0.0, rotation_deg=0.0)
        
        with pytest.raises(ValueError, match="size must be positive"):
            QRPosition(x_mm=100.0, y_mm=150.0, size_mm=-10.0, rotation_deg=0.0)
    
    def test_invalid_rotation(self):
        """Test that rotation outside 0-360 raises ValueError."""
        with pytest.raises(ValueError, match="Rotation must be between 0 and 360"):
            QRPosition(x_mm=100.0, y_mm=150.0, size_mm=20.0, rotation_deg=-10.0)
        
        with pytest.raises(ValueError, match="Rotation must be between 0 and 360"):
            QRPosition(x_mm=100.0, y_mm=150.0, size_mm=20.0, rotation_deg=361.0)


class TestCSVParser:
    """Test suite for CSVParser class."""
    
    @pytest.fixture
    def temp_csv_file(self):
        """Create a temporary CSV file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            csv_path = f.name
        yield csv_path
        Path(csv_path).unlink(missing_ok=True)
    
    def create_csv(self, path, data):
        """Helper to create a CSV file with given data."""
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSVParser.REQUIRED_HEADERS)
            writer.writeheader()
            writer.writerows(data)
    
    def test_parse_valid_csv(self, temp_csv_file):
        """Test parsing a valid CSV file."""
        data = [
            {"x_mm": "105.0", "y_mm": "148.5", "size_mm": "20.0", "rotation_deg": "0"},
            {"x_mm": "50.0", "y_mm": "50.0", "size_mm": "15.0", "rotation_deg": "90"},
        ]
        self.create_csv(temp_csv_file, data)
        
        positions = CSVParser.parse(temp_csv_file)
        
        assert len(positions) == 2
        assert positions[0].x_mm == 105.0
        assert positions[0].y_mm == 148.5
        assert positions[0].size_mm == 20.0
        assert positions[0].rotation_deg == 0.0
        
        assert positions[1].x_mm == 50.0
        assert positions[1].y_mm == 50.0
        assert positions[1].size_mm == 15.0
        assert positions[1].rotation_deg == 90.0
    
    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            CSVParser.parse("/nonexistent/path/file.csv")
    
    def test_parse_empty_csv(self, temp_csv_file):
        """Test parsing an empty CSV file."""
        Path(temp_csv_file).write_text("")
        
        with pytest.raises(ValueError, match="empty or has no headers"):
            CSVParser.parse(temp_csv_file)
    
    def test_parse_missing_headers(self, temp_csv_file):
        """Test parsing CSV with missing required headers."""
        with open(temp_csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["x_mm", "y_mm"])  # Missing size_mm and rotation_deg
            writer.writeheader()
            writer.writerow({"x_mm": "100", "y_mm": "100"})
        
        with pytest.raises(ValueError, match="missing required headers"):
            CSVParser.parse(temp_csv_file)
    
    def test_parse_invalid_float_values(self, temp_csv_file):
        """Test parsing CSV with invalid float values."""
        data = [
            {"x_mm": "not_a_number", "y_mm": "148.5", "size_mm": "20.0", "rotation_deg": "0"},
        ]
        self.create_csv(temp_csv_file, data)
        
        with pytest.raises(ValueError, match="Error parsing CSV row"):
            CSVParser.parse(temp_csv_file)
    
    def test_parse_no_data_rows(self, temp_csv_file):
        """Test parsing CSV with headers but no data."""
        with open(temp_csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSVParser.REQUIRED_HEADERS)
            writer.writeheader()
        
        with pytest.raises(ValueError, match="contains no position data"):
            CSVParser.parse(temp_csv_file)
    
    def test_validate_positions_within_bounds(self, temp_csv_file):
        """Test validating positions that are within page bounds."""
        data = [
            {"x_mm": "105.0", "y_mm": "148.5", "size_mm": "20.0", "rotation_deg": "0"},
            {"x_mm": "50.0", "y_mm": "50.0", "size_mm": "15.0", "rotation_deg": "90"},
        ]
        self.create_csv(temp_csv_file, data)
        
        positions = CSVParser.parse(temp_csv_file)
        
        # A4 page dimensions
        result = CSVParser.validate(positions, page_width_mm=210.0, page_height_mm=297.0)
        assert result is True
    
    def test_validate_position_outside_width(self, temp_csv_file):
        """Test validating position that extends outside page width."""
        data = [
            {"x_mm": "200.0", "y_mm": "100.0", "size_mm": "30.0", "rotation_deg": "0"},
        ]
        self.create_csv(temp_csv_file, data)
        
        positions = CSVParser.parse(temp_csv_file)
        
        with pytest.raises(ValueError, match="extends outside page width"):
            CSVParser.validate(positions, page_width_mm=210.0, page_height_mm=297.0)
    
    def test_validate_position_outside_height(self, temp_csv_file):
        """Test validating position that extends outside page height."""
        data = [
            {"x_mm": "100.0", "y_mm": "290.0", "size_mm": "20.0", "rotation_deg": "0"},
        ]
        self.create_csv(temp_csv_file, data)
        
        positions = CSVParser.parse(temp_csv_file)
        
        with pytest.raises(ValueError, match="extends outside page height"):
            CSVParser.validate(positions, page_width_mm=210.0, page_height_mm=297.0)
    
    def test_validate_position_negative_coordinates(self, temp_csv_file):
        """Test validating position with negative coordinates after size adjustment."""
        data = [
            {"x_mm": "5.0", "y_mm": "5.0", "size_mm": "20.0", "rotation_deg": "0"},
        ]
        self.create_csv(temp_csv_file, data)
        
        positions = CSVParser.parse(temp_csv_file)
        
        # QR code would extend from -5 to 15 in both dimensions
        with pytest.raises(ValueError, match="extends outside"):
            CSVParser.validate(positions, page_width_mm=210.0, page_height_mm=297.0)
    
    def test_validate_multiple_positions(self, temp_csv_file):
        """Test validating multiple positions."""
        data = [
            {"x_mm": "50.0", "y_mm": "50.0", "size_mm": "20.0", "rotation_deg": "0"},
            {"x_mm": "105.0", "y_mm": "148.5", "size_mm": "20.0", "rotation_deg": "0"},
            {"x_mm": "160.0", "y_mm": "250.0", "size_mm": "15.0", "rotation_deg": "45"},
        ]
        self.create_csv(temp_csv_file, data)
        
        positions = CSVParser.parse(temp_csv_file)
        
        result = CSVParser.validate(positions, page_width_mm=210.0, page_height_mm=297.0)
        assert result is True
    
    def test_create_example_csv(self, temp_csv_file):
        """Test creating an example CSV file."""
        CSVParser.create_example_csv(temp_csv_file)
        
        assert Path(temp_csv_file).exists()
        
        # Parse the created file to verify it's valid
        positions = CSVParser.parse(temp_csv_file)
        assert len(positions) > 0
        
        # Verify all positions are valid
        for pos in positions:
            assert pos.size_mm > 0
            assert 0 <= pos.rotation_deg <= 360
    
    def test_parse_with_extra_columns(self, temp_csv_file):
        """Test parsing CSV with extra columns (should be ignored)."""
        with open(temp_csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = CSVParser.REQUIRED_HEADERS + ["extra_column"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({
                "x_mm": "100.0",
                "y_mm": "100.0",
                "size_mm": "20.0",
                "rotation_deg": "0",
                "extra_column": "ignored"
            })
        
        positions = CSVParser.parse(temp_csv_file)
        assert len(positions) == 1
        assert positions[0].x_mm == 100.0
