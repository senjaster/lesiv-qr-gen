"""Configuration manager for persisting application settings."""

import configparser
from pathlib import Path
from typing import Any, Optional
import threading


class ConfigManager:
    """Manages application configuration using INI files.
    
    Provides thread-safe read/write operations for persisting user settings
    across application restarts.
    """
    
    # Default QR base URL - single source of truth
    DEFAULT_QR_BASE_URL = "https://qr.thermoelectrica.com?id="
    
    DEFAULT_CONFIG = {
        "paths": {
            "last_svg_path": "",
            "last_csv_path": "",
            "last_output_folder": "",
        },
        "settings": {
            "num_pages": "10",
            "qr_base_url": DEFAULT_QR_BASE_URL,
        },
        "id_state": {
            "last_date": "",
            "last_id": "",
            "last_page_num": "",
        }
    }
    
    def __init__(self, config_path: str = "config.ini"):
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to the INI configuration file
        """
        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser()
        self._lock = threading.Lock()
        self.load()
    
    def load(self) -> None:
        """Load configuration from file or create with defaults."""
        with self._lock:
            if self.config_path.exists() and self.config_path.stat().st_size > 0:
                # File exists and is not empty, load it
                self.config.read(self.config_path)
            else:
                # File doesn't exist or is empty, initialize with defaults
                for section, options in self.DEFAULT_CONFIG.items():
                    if not self.config.has_section(section):
                        self.config.add_section(section)
                    for key, value in options.items():
                        self.config.set(section, key, value)
                self._save_unlocked()
    
    def get(self, key: str, default: Any = None, section: str = "settings") -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            section: Configuration section (default: "settings")
            
        Returns:
            Configuration value or default
        """
        with self._lock:
            if not self.config.has_section(section):
                return default
            
            if not self.config.has_option(section, key):
                return default
            
            return self.config.get(section, key)
    
    def set(self, key: str, value: Any, section: str = "settings") -> None:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
            section: Configuration section (default: "settings")
        """
        with self._lock:
            if not self.config.has_section(section):
                self.config.add_section(section)
            
            self.config.set(section, key, str(value))
    
    def save(self) -> None:
        """Save configuration to file (thread-safe)."""
        with self._lock:
            self._save_unlocked()
    
    def _save_unlocked(self) -> None:
        """Save configuration to file (internal, not thread-safe)."""
        with open(self.config_path, 'w') as f:
            self.config.write(f)
    
    def get_path(self, key: str, default: str = "") -> str:
        """Get a path configuration value.
        
        Args:
            key: Configuration key (e.g., "last_svg_path")
            default: Default value if key doesn't exist
            
        Returns:
            Path string
        """
        return self.get(key, default, section="paths")
    
    def set_path(self, key: str, value: str) -> None:
        """Set a path configuration value.
        
        Args:
            key: Configuration key (e.g., "last_svg_path")
            value: Path string to set
        """
        self.set(key, value, section="paths")
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get a float configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist or conversion fails
            
        Returns:
            Float value
        """
        value = self.get(key, str(default))
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist or conversion fails
            
        Returns:
            Integer value
        """
        value = self.get(key, str(default))
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def save_id_state(self, date: str, last_id: int, last_page_num: int) -> None:
        """Save the last generated ID state for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format
            last_id: Last generated ID
            last_page_num: Last generated page number
        """
        self.set("last_date", date, section="id_state")
        self.set("last_id", str(last_id), section="id_state")
        self.set("last_page_num", str(last_page_num), section="id_state")
        self.save()
    
    def get_id_state(self) -> tuple[Optional[str], Optional[int], Optional[int]]:
        """Get the last saved ID state.
        
        Returns:
            Tuple of (date, last_id, last_page_num) or (None, None, None) if not set
        """
        date = self.get("last_date", "", section="id_state")
        last_id_str = self.get("last_id", "", section="id_state")
        last_page_num_str = self.get("last_page_num", "", section="id_state")
        
        if not date or not last_id_str or not last_page_num_str:
            return None, None, None
        
        try:
            last_id = int(last_id_str)
            last_page_num = int(last_page_num_str)
            return date, last_id, last_page_num
        except (ValueError, TypeError):
            return None, None, None
