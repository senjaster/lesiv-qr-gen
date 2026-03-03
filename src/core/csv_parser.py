"""CSV parser for QR code position definitions."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class QRPosition:
    """Represents a QR code position on the page.
    
    Attributes:
        x_mm: Center X position in millimeters from page top-left
        y_mm: Center Y position in millimeters from page top-left
        size_mm: QR code size (square) in millimeters
        rotation_deg: Rotation angle in degrees (0-360)
    """
    x_mm: float
    y_mm: float
    size_mm: float
    rotation_deg: float
    
    def __post_init__(self):
        """Validate position values after initialization."""
        if self.size_mm <= 0:
            raise ValueError(f"QR code size must be positive, got {self.size_mm}")
        
        if not 0 <= self.rotation_deg <= 360:
            raise ValueError(f"Rotation must be between 0 and 360 degrees, got {self.rotation_deg}")


class CSVParser:
    """Parser for QR code position CSV files.
    
    Expected CSV format:
        x_mm,y_mm,size_mm,rotation_deg
        105.0,148.5,20.0,0
        50.0,50.0,15.0,90
    """
    
    REQUIRED_HEADERS = ["x_mm", "y_mm", "size_mm", "rotation_deg"]
    
    @staticmethod
    def parse(csv_path: str) -> List[QRPosition]:
        """Parse a CSV file containing QR code positions.
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            List of QRPosition objects
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid or values are out of range
        """
        path = Path(csv_path)
        
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        positions = []
        
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate headers
            if reader.fieldnames is None:
                raise ValueError("CSV file is empty or has no headers")
            
            missing_headers = set(CSVParser.REQUIRED_HEADERS) - set(reader.fieldnames)
            if missing_headers:
                raise ValueError(
                    f"CSV file missing required headers: {', '.join(missing_headers)}"
                )
            
            # Parse rows
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                try:
                    position = QRPosition(
                        x_mm=float(row["x_mm"]),
                        y_mm=float(row["y_mm"]),
                        size_mm=float(row["size_mm"]),
                        rotation_deg=float(row["rotation_deg"])
                    )
                    positions.append(position)
                except (ValueError, KeyError) as e:
                    raise ValueError(
                        f"Error parsing CSV row {row_num}: {e}"
                    ) from e
        
        if not positions:
            raise ValueError("CSV file contains no position data")
        
        return positions
    
    @staticmethod
    def validate(
        positions: List[QRPosition],
        page_width_mm: float,
        page_height_mm: float
    ) -> bool:
        """Validate that QR positions are within page bounds.
        
        Args:
            positions: List of QR positions to validate
            page_width_mm: Page width in millimeters
            page_height_mm: Page height in millimeters
            
        Returns:
            True if all positions are valid
            
        Raises:
            ValueError: If any position is outside page bounds
        """
        for i, pos in enumerate(positions):
            # Calculate QR code bounds (center ± half size)
            half_size = pos.size_mm / 2
            
            min_x = pos.x_mm - half_size
            max_x = pos.x_mm + half_size
            min_y = pos.y_mm - half_size
            max_y = pos.y_mm + half_size
            
            # Check if QR code is within page bounds
            if min_x < 0 or max_x > page_width_mm:
                raise ValueError(
                    f"QR position {i+1} (x={pos.x_mm}mm, size={pos.size_mm}mm) "
                    f"extends outside page width ({page_width_mm}mm)"
                )
            
            if min_y < 0 or max_y > page_height_mm:
                raise ValueError(
                    f"QR position {i+1} (y={pos.y_mm}mm, size={pos.size_mm}mm) "
                    f"extends outside page height ({page_height_mm}mm)"
                )
        
        return True
    
    @staticmethod
    def create_example_csv(output_path: str) -> None:
        """Create an example CSV file with sample QR positions.
        
        Args:
            output_path: Path where to create the example CSV file
        """
        example_data = [
            {"x_mm": "105.0", "y_mm": "148.5", "size_mm": "20.0", "rotation_deg": "0"},
            {"x_mm": "50.0", "y_mm": "50.0", "size_mm": "15.0", "rotation_deg": "90"},
            {"x_mm": "160.0", "y_mm": "50.0", "size_mm": "15.0", "rotation_deg": "0"},
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSVParser.REQUIRED_HEADERS)
            writer.writeheader()
            writer.writerows(example_data)
