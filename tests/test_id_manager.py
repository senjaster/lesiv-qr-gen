"""Tests for IDManager."""

import pytest
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta
from src.core.id_manager import IDManager
from src.core.config_manager import ConfigManager


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
        # Start ID should be the beginning of today (00:00:00)
        now = datetime.now()
        day_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        expected_start = int(day_start.timestamp())
        assert start_id == expected_start
    
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
        # Should use start of day epoch timestamp
        now = datetime.now()
        day_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        expected_start = int(day_start.timestamp())
        assert start_id == expected_start
    
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
    
    def test_overflow_validation(self, temp_output_dir):
        """Test that ID generation validates overflow to next day."""
        manager = IDManager(temp_output_dir)
        output_path = manager.get_output_path()
        
        # Get day boundaries
        now = datetime.now()
        day_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        day_start_epoch = int(day_start.timestamp())
        day_end_epoch = day_start_epoch + manager.SECONDS_PER_DAY - 1
        
        # Create a file with IDs very close to end of day
        # Leave only 10 IDs available for today
        last_valid_id = day_end_epoch - 10
        (output_path / f"001-{day_start_epoch}-{last_valid_id}.pdf").touch()
        
        page_num, start_id = manager.get_next_page_info()
        
        # Should be able to generate 10 IDs (up to day_end_epoch)
        ids = manager.generate_ids(10)
        assert len(ids) == 10
        assert ids[-1] == day_end_epoch
        
        # Trying to generate even 1 more ID should raise ValueError
        with pytest.raises(ValueError, match="overflow to the next day"):
            manager.generate_ids(1)
    
    def test_overflow_validation_message(self, temp_output_dir):
        """Test that overflow error message contains useful information."""
        manager = IDManager(temp_output_dir)
        output_path = manager.get_output_path()
        
        # Get day boundaries
        now = datetime.now()
        day_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        day_start_epoch = int(day_start.timestamp())
        day_end_epoch = day_start_epoch + manager.SECONDS_PER_DAY - 1
        
        # Create a file with IDs very close to end of day (5 IDs left)
        last_valid_id = day_end_epoch - 5
        (output_path / f"001-{day_start_epoch}-{last_valid_id}.pdf").touch()
        
        page_num, start_id = manager.get_next_page_info()
        
        # Try to generate more IDs than available
        with pytest.raises(ValueError) as exc_info:
            manager.generate_ids(10)
        
        error_msg = str(exc_info.value)
        assert "overflow to the next day" in error_msg
        assert "5 IDs available" in error_msg
        assert str(day_end_epoch) in error_msg
    
    def test_previous_day_ids_validation(self, temp_output_dir):
        """Test that IDs from previous day are detected."""
        manager = IDManager(temp_output_dir)
        output_path = manager.get_output_path()
        
        # Get day boundaries
        now = datetime.now()
        day_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        day_start_epoch = int(day_start.timestamp())
        
        # Create a file with IDs from "yesterday" (before today's start)
        yesterday_id = day_start_epoch - 1000
        (output_path / f"001-{yesterday_id}-{yesterday_id + 99}.pdf").touch()
        
        page_num, start_id = manager.get_next_page_info()
        
        # Trying to generate IDs should raise ValueError about previous day
        with pytest.raises(ValueError, match="before today's start epoch"):
            manager.generate_ids(1)
    
    def test_day_start_epoch_calculation(self, temp_output_dir):
        """Test that day start epoch is correctly calculated."""
        manager = IDManager(temp_output_dir)
        
        # Get current day start
        now = datetime.now()
        day_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        expected_epoch = int(day_start.timestamp())
        
        actual_epoch = manager._get_day_start_epoch()
        assert actual_epoch == expected_epoch
        
        # Test with specific date
        specific_date = datetime(2026, 1, 15, 14, 30, 45)
        specific_day_start = datetime(2026, 1, 15, 0, 0, 0)
        expected_specific = int(specific_day_start.timestamp())
        
        actual_specific = manager._get_day_start_epoch(specific_date)
        assert actual_specific == expected_specific
    
    def test_day_end_epoch_calculation(self, temp_output_dir):
        """Test that day end epoch is correctly calculated."""
        manager = IDManager(temp_output_dir)
        
        # Get current day end
        now = datetime.now()
        day_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        expected_end = int(day_start.timestamp()) + manager.SECONDS_PER_DAY - 1
        
        actual_end = manager._get_day_end_epoch()
        assert actual_end == expected_end
        
        # Verify it's exactly 86399 seconds after day start
        day_start_epoch = manager._get_day_start_epoch()
        day_end_epoch = manager._get_day_end_epoch()
        assert day_end_epoch - day_start_epoch == manager.SECONDS_PER_DAY - 1
    
    def test_state_persistence_with_config(self, temp_output_dir):
        """Test that state is saved to config after generating pages."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as config_file:
            config_path = config_file.name
        
        try:
            # Create manager with config
            config_manager = ConfigManager(config_path)
            manager = IDManager(temp_output_dir, config_manager)
            
            # Generate some pages
            page_num, start_id = manager.get_next_page_info()
            ids = manager.generate_ids(5)
            manager.update_page_info(page_num, ids[-1])
            
            # Check that state was saved
            saved_date, saved_id, saved_page_num = config_manager.get_id_state()
            today = datetime.now().strftime("%Y-%m-%d")
            
            assert saved_date == today
            assert saved_id == ids[-1]
            assert saved_page_num == page_num
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_state_restoration_empty_folder(self, temp_output_dir):
        """Test that state is restored from config when folder is empty."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as config_file:
            config_path = config_file.name
        
        try:
            # Create manager and generate some pages
            config_manager = ConfigManager(config_path)
            manager1 = IDManager(temp_output_dir, config_manager)
            
            page_num1, start_id1 = manager1.get_next_page_info()
            ids1 = manager1.generate_ids(10)
            manager1.update_page_info(page_num1, ids1[-1])
            
            # Create output file to simulate real generation
            output_path = manager1.get_output_path()
            filename = manager1.format_filename(page_num1, ids1[0], ids1[-1])
            (output_path / filename).touch()
            
            # Now delete the output folder to simulate clearing
            import shutil
            shutil.rmtree(output_path)
            
            # Create new manager with same config
            manager2 = IDManager(temp_output_dir, config_manager)
            page_num2, start_id2 = manager2.get_next_page_info()
            
            # Should restore from config
            assert page_num2 == page_num1 + 1
            assert start_id2 == ids1[-1] + 1
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_state_restoration_ignores_old_date(self, temp_output_dir):
        """Test that state from previous day is ignored."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as config_file:
            config_path = config_file.name
        
        try:
            config_manager = ConfigManager(config_path)
            
            # Save state for yesterday
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            config_manager.save_id_state(yesterday, 1234567, 5)
            
            # Create new manager
            manager = IDManager(temp_output_dir, config_manager)
            page_num, start_id = manager.get_next_page_info()
            
            # Should NOT restore from config (wrong date)
            # Should start from beginning of today
            assert page_num == 1
            now = datetime.now()
            day_start = datetime(now.year, now.month, now.day, 0, 0, 0)
            expected_start = int(day_start.timestamp())
            assert start_id == expected_start
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_state_restoration_validates_id_range(self, temp_output_dir):
        """Test that saved ID is validated to be within today's range."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as config_file:
            config_path = config_file.name
        
        try:
            config_manager = ConfigManager(config_path)
            
            # Save state for today but with invalid ID (from yesterday)
            today = datetime.now().strftime("%Y-%m-%d")
            now = datetime.now()
            day_start = datetime(now.year, now.month, now.day, 0, 0, 0)
            day_start_epoch = int(day_start.timestamp())
            invalid_id = day_start_epoch - 1000  # ID from yesterday
            
            config_manager.save_id_state(today, invalid_id, 5)
            
            # Create new manager
            manager = IDManager(temp_output_dir, config_manager)
            page_num, start_id = manager.get_next_page_info()
            
            # Should NOT restore from config (invalid ID)
            # Should start from beginning of today
            assert page_num == 1
            assert start_id == day_start_epoch
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_state_without_config_manager(self, temp_output_dir):
        """Test that manager works without config manager (no persistence)."""
        # Create manager without config
        manager = IDManager(temp_output_dir)
        
        page_num, start_id = manager.get_next_page_info()
        ids = manager.generate_ids(5)
        
        # Should work normally, just won't persist
        manager.update_page_info(page_num, ids[-1])
        
        # No errors should occur
        assert page_num == 1
    
    def test_state_restoration_prefers_files_over_config(self, temp_output_dir):
        """Test that existing files take precedence over saved config state."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as config_file:
            config_path = config_file.name
        
        try:
            config_manager = ConfigManager(config_path)
            
            # Save state in config
            today = datetime.now().strftime("%Y-%m-%d")
            config_manager.save_id_state(today, 5000, 10)
            
            # Create manager and add actual files
            manager = IDManager(temp_output_dir, config_manager)
            output_path = manager.get_output_path()
            (output_path / "001-1000-1005.pdf").touch()
            (output_path / "002-1006-1010.pdf").touch()
            
            page_num, start_id = manager.get_next_page_info()
            
            # Should use files, not config
            assert page_num == 3
            assert start_id == 1011
        finally:
            Path(config_path).unlink(missing_ok=True)
