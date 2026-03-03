"""ID manager for generating unique sequential IDs and managing output folders."""

import re
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple, Optional


class IDManager:
    """Manages unique ID generation and output folder structure.
    
    Creates date-based folder structure (YYYY-MM-DD) and generates sequential
    IDs for QR codes. Uses Linux epoch timestamp (00:00:00 of the day) as starting ID for new days.
    Validates that IDs don't overflow to the next day.
    """
    
    # Regex pattern for parsing filenames: NNN-min_id-max_id.pdf
    FILENAME_PATTERN = re.compile(r'^(\d{3})-(\d+)-(\d+)\.pdf$')
    
    # Seconds in a day for overflow validation
    SECONDS_PER_DAY = 86400
    
    def __init__(self, output_root: str):
        """Initialize the ID manager.
        
        Args:
            output_root: Root directory for output files
        """
        self.output_root = Path(output_root)
        self._current_date = None
        self._next_page_num = None
        self._next_id = None
    
    def _get_day_start_epoch(self, date: Optional[datetime] = None) -> int:
        """Get the epoch timestamp for the start of a day (00:00:00).
        
        Args:
            date: Date to get start epoch for. If None, uses current date.
            
        Returns:
            Unix epoch timestamp for 00:00:00 of the specified date
        """
        if date is None:
            date = datetime.now()
        
        # Create datetime for start of day (00:00:00)
        day_start = datetime(date.year, date.month, date.day, 0, 0, 0)
        return int(day_start.timestamp())
    
    def _get_day_end_epoch(self, date: Optional[datetime] = None) -> int:
        """Get the epoch timestamp for the end of a day (23:59:59).
        
        Args:
            date: Date to get end epoch for. If None, uses current date.
            
        Returns:
            Unix epoch timestamp for 23:59:59 of the specified date
        """
        day_start = self._get_day_start_epoch(date)
        return day_start + self.SECONDS_PER_DAY - 1
    
    def get_output_path(self) -> Path:
        """Get the output path for today's date.
        
        Returns:
            Path object for today's output folder (YYYY-MM-DD)
        """
        today = datetime.now().strftime("%Y-%m-%d")
        output_path = self.output_root / today
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path
    
    def get_next_page_info(self) -> Tuple[int, int]:
        """Get the next page number and starting ID.
        
        Scans existing files in today's folder to determine the next page
        number and ID. If no files exist, uses current epoch timestamp as
        starting ID.
        
        Returns:
            Tuple of (page_number, start_id)
        """
        output_path = self.get_output_path()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Check if we need to rescan (date changed or first call)
        if self._current_date != today or self._next_page_num is None:
            self._scan_existing_files(output_path)
            self._current_date = today
        
        # Return current values (guaranteed to be set by _scan_existing_files)
        assert self._next_page_num is not None
        assert self._next_id is not None
        
        page_num = self._next_page_num
        start_id = self._next_id
        
        return page_num, start_id
    
    def _scan_existing_files(self, output_path: Path) -> None:
        """Scan existing PDF files to determine next page number and ID.
        
        Args:
            output_path: Path to scan for existing PDF files
        """
        max_page_num = 0
        max_id = None
        
        if output_path.exists():
            # Find all PDF files matching our pattern
            for file_path in output_path.glob("*.pdf"):
                match = self.FILENAME_PATTERN.match(file_path.name)
                if match:
                    page_num = int(match.group(1))
                    file_max_id = int(match.group(3))
                    
                    if page_num > max_page_num:
                        max_page_num = page_num
                    
                    if max_id is None or file_max_id > max_id:
                        max_id = file_max_id
        
        # Set next page number and ID
        self._next_page_num = max_page_num + 1
        
        if max_id is None:
            # No existing files, use start of day epoch timestamp
            self._next_id = self._get_day_start_epoch()
        else:
            # Continue from last ID
            self._next_id = max_id + 1
    
    def generate_ids(self, count: int) -> list[int]:
        """Generate a list of sequential IDs.
        
        Args:
            count: Number of IDs to generate
            
        Returns:
            List of sequential integer IDs
            
        Raises:
            ValueError: If generating IDs would overflow to the next day
        """
        if self._next_id is None:
            # Initialize if not already done
            self.get_next_page_info()
        
        # After get_next_page_info(), _next_id is guaranteed to be set
        assert self._next_id is not None
        
        # Sanity check: validate that IDs won't overflow to next day
        day_start = self._get_day_start_epoch()
        day_end = self._get_day_end_epoch()
        last_id = self._next_id + count - 1
        
        if self._next_id < day_start:
            raise ValueError(
                f"Starting ID {self._next_id} is before today's start epoch {day_start}. "
                f"This indicates IDs from a previous day."
            )
        
        if last_id > day_end:
            available_ids = day_end - self._next_id + 1
            raise ValueError(
                f"Generating {count} IDs would overflow to the next day. "
                f"Current ID: {self._next_id}, Last ID would be: {last_id}, "
                f"Day ends at: {day_end}. Only {available_ids} IDs available for today."
            )
        
        ids = list(range(self._next_id, self._next_id + count))
        self._next_id += count
        
        return ids
    
    def format_filename(self, page_num: int, min_id: int, max_id: int) -> str:
        """Format a filename according to the pattern NNN-min_id-max_id.pdf.
        
        Args:
            page_num: Page number (will be zero-padded to 3 digits)
            min_id: Minimum QR code ID in this file
            max_id: Maximum QR code ID in this file
            
        Returns:
            Formatted filename string
        """
        return f"{page_num:03d}-{min_id}-{max_id}.pdf"
    
    def get_full_output_path(self, filename: str) -> Path:
        """Get the full output path for a filename.
        
        Args:
            filename: Name of the file
            
        Returns:
            Full path including date folder
        """
        return self.get_output_path() / filename
    
    def update_page_info(self, page_num: int, max_id: int) -> None:
        """Update internal state after generating a page.
        
        This is called after successfully generating a page to update
        the next page number.
        
        Args:
            page_num: Page number that was just generated
            max_id: Maximum ID used in that page
        """
        self._next_page_num = page_num + 1
        # _next_id is already updated by generate_ids()
