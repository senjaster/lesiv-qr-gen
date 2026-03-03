"""Tests for IDManager."""

import pytest
import tempfile
import time
from pathlib import Path
from src.core.id_manager import IDManager


class TestIDManager:
    """Test suite for IDManager class."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_get_output_path_creates_date_folder(self, temp_output_dir):
        """Test that get_output_path creates a date-based folder."""
        manager = IDManager(temp_output_dir)
        output_path = manager.get_output_path()
        
        assert output_path.exists()
        assert output_path.is_dir()
        # Check that folder name matches YYYY-MM-DD format
        assert len(output_path.name) == 10
        assert output_path.name.count('-') == 2
    
    def test_get_next_page_info_empty_folder(self, temp_output_dir):
        """Test getting page info when folder is empty."""
        manager = IDManager(temp_output_dir)
        page_num, start_id = manager.get_next_page_info()
        
        # First page should be 1
        assert page_num == 1
        # Start ID should be close to current epoch time
        current_time = int(time.time())
        assert abs(start_id - current_time) < 5  # Within 5 seconds
    
    def test_get_next_page_info_with_existing_files(self, temp_output_dir):
        """Test getting page info when files already exist."""
        manager = IDManager(temp_output_dir)
        output_path = manager.get_output_path()
        
        # Create some existing PDF files
        (output_path / "001-1000000-1000004.pdf").touch()
        (output_path / "002-1000005-1000009.pdf").touch()
        (output_path / "003-1000010-1000014.pdf").touch()
        
        page_num, start_id = manager.get_next_page_info()
        
        # Next page should be 4
        assert page_num == 4
        # Next ID should be 1000015 (max_id + 1)
        assert start_id == 1000015
    
    def test_generate_ids(self, temp_output_dir):
        """Test generating sequential IDs."""
        manager = IDManager(temp_output_dir)
        
        # Initialize by calling get_next_page_info
        page_num, start_id = manager.get_next_page_info()
        
        # Generate 5 IDs
        ids = manager.generate_ids(5)
        
        assert len(ids) == 5
        assert ids == list(range(start_id, start_id + 5))
        
        # Generate more IDs - should continue from where we left off
        more_ids = manager.generate_ids(3)
        assert more_ids == list(range(start_id + 5, start_id + 8))
    
    def test_format_filename(self, temp_output_dir):
        """Test filename formatting."""
        manager = IDManager(temp_output_dir)
        
        filename = manager.format_filename(1, 1000, 1005)
        assert filename == "001-1000-1005.pdf"
        
        filename = manager.format_filename(42, 2000000, 2000099)
        assert filename == "042-2000000-2000099.pdf"
        
        filename = manager.format_filename(999, 123, 456)
        assert filename == "999-123-456.pdf"
    
    def test_get_full_output_path(self, temp_output_dir):
        """Test getting full output path."""
        manager = IDManager(temp_output_dir)
        
        full_path = manager.get_full_output_path("001-1000-1005.pdf")
        
        assert full_path.parent == manager.get_output_path()
        assert full_path.name == "001-1000-1005.pdf"
    
    def test_update_page_info(self, temp_output_dir):
        """Test updating page info after generation."""
        manager = IDManager(temp_output_dir)
        
        page_num, start_id = manager.get_next_page_info()
        ids = manager.generate_ids(5)
        
        # Update after generating page 1 with IDs up to start_id+4
        manager.update_page_info(page_num, ids[-1])
        
        # Next page info should be incremented
        next_page, next_id = manager.get_next_page_info()
        assert next_page == page_num + 1
    
    def test_filename_pattern_parsing(self, temp_output_dir):
        """Test that the filename pattern correctly parses valid filenames."""
        manager = IDManager(temp_output_dir)
        output_path = manager.get_output_path()
        
        # Create files with various valid patterns
        (output_path / "001-100-105.pdf").touch()
        (output_path / "010-200-250.pdf").touch()
        (output_path / "999-999999-1000000.pdf").touch()
        
        page_num, start_id = manager.get_next_page_info()
        
        # Should find the highest page number (999) and highest ID (1000000)
        assert page_num == 1000
        assert start_id == 1000001
    
    def test_ignores_invalid_filenames(self, temp_output_dir):
        """Test that invalid filenames are ignored."""
        manager = IDManager(temp_output_dir)
        output_path = manager.get_output_path()
        
        # Create files with invalid patterns
        (output_path / "invalid.pdf").touch()
        (output_path / "001-abc-def.pdf").touch()
        (output_path / "1-100-200.pdf").touch()  # Page number not zero-padded
        (output_path / "001-100-200.txt").touch()  # Wrong extension
        
        page_num, start_id = manager.get_next_page_info()
        
        # Should start from 1 since no valid files exist
        assert page_num == 1
        # Should use epoch timestamp
        current_time = int(time.time())
        assert abs(start_id - current_time) < 5
    
    def test_multiple_calls_same_day(self, temp_output_dir):
        """Test that multiple calls on the same day work correctly."""
        manager = IDManager(temp_output_dir)
        
        # First call
        page1, id1 = manager.get_next_page_info()
        
        # Second call without generating IDs
        page2, id2 = manager.get_next_page_info()
        
        # Should return same values (cached)
        assert page1 == page2
        assert id1 == id2
    
    def test_sequential_id_generation(self, temp_output_dir):
        """Test that IDs are truly sequential across multiple generations."""
        manager = IDManager(temp_output_dir)
        
        page_num, start_id = manager.get_next_page_info()
        
        all_ids = []
        for _ in range(5):
            ids = manager.generate_ids(10)
            all_ids.extend(ids)
        
        # Check that all IDs are sequential
        assert len(all_ids) == 50
        assert all_ids == list(range(start_id, start_id + 50))
