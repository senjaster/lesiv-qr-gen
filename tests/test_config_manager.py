"""Tests for ConfigManager."""

import pytest
import tempfile
from pathlib import Path
from src.core.config_manager import ConfigManager


class TestConfigManager:
    """Test suite for ConfigManager class."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            config_path = f.name
        yield config_path
        # Cleanup
        Path(config_path).unlink(missing_ok=True)
    
    def test_init_creates_default_config(self, temp_config_file):
        """Test that initialization creates a config file with defaults."""
        config = ConfigManager(temp_config_file)
        
        assert Path(temp_config_file).exists()
        # Check that default values are set in the config
        assert config.get("num_pages") == "10"
        assert config.get("qr_base_url") == ConfigManager.DEFAULT_QR_BASE_URL
    
    def test_get_with_default(self, temp_config_file):
        """Test getting a value with a default."""
        config = ConfigManager(temp_config_file)
        
        # Non-existent key should return default
        assert config.get("nonexistent", "default_value") == "default_value"
    
    def test_set_and_get(self, temp_config_file):
        """Test setting and getting values."""
        config = ConfigManager(temp_config_file)
        
        config.set("test_key", "test_value")
        assert config.get("test_key") == "test_value"
    
    def test_save_and_load(self, temp_config_file):
        """Test that values persist after save and reload."""
        config1 = ConfigManager(temp_config_file)
        config1.set("persistent_key", "persistent_value")
        config1.save()
        
        # Create new instance to load from file
        config2 = ConfigManager(temp_config_file)
        assert config2.get("persistent_key") == "persistent_value"
    
    def test_get_path(self, temp_config_file):
        """Test getting path values."""
        config = ConfigManager(temp_config_file)
        
        config.set_path("last_svg_path", "/path/to/file.svg")
        assert config.get_path("last_svg_path") == "/path/to/file.svg"
    
    def test_set_path(self, temp_config_file):
        """Test setting path values."""
        config = ConfigManager(temp_config_file)
        
        config.set_path("last_csv_path", "/path/to/positions.csv")
        assert config.get_path("last_csv_path") == "/path/to/positions.csv"
    
    def test_get_float(self, temp_config_file):
        """Test getting float values."""
        config = ConfigManager(temp_config_file)
        
        config.set("float_value", "123.45")
        assert config.get_float("float_value") == 123.45
        
        # Test default for non-existent key
        assert config.get_float("nonexistent", 99.9) == 99.9
        
        # Test default for invalid float
        config.set("invalid_float", "not_a_number")
        assert config.get_float("invalid_float", 50.0) == 50.0
    
    def test_get_int(self, temp_config_file):
        """Test getting integer values."""
        config = ConfigManager(temp_config_file)
        
        config.set("int_value", "42")
        assert config.get_int("int_value") == 42
        
        # Test default for non-existent key
        assert config.get_int("nonexistent", 100) == 100
        
        # Test default for invalid int
        config.set("invalid_int", "not_a_number")
        assert config.get_int("invalid_int", 25) == 25
    
    def test_default_config_values(self, temp_config_file):
        """Test that default configuration values are set correctly."""
        config = ConfigManager(temp_config_file)
        
        # Check default paths (empty strings)
        assert config.get_path("last_svg_path") == ""
        assert config.get_path("last_csv_path") == ""
        assert config.get_path("last_output_folder") == ""
        
        # Check default settings
        assert config.get_int("num_pages") == 10
        assert config.get("qr_base_url") == ConfigManager.DEFAULT_QR_BASE_URL
    
    def test_thread_safety(self, temp_config_file):
        """Test that operations are thread-safe."""
        import threading
        
        config = ConfigManager(temp_config_file)
        results = []
        
        def set_value(key, value):
            config.set(key, value)
            results.append(config.get(key))
        
        threads = []
        for i in range(10):
            t = threading.Thread(target=set_value, args=(f"key_{i}", f"value_{i}"))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All values should be set correctly
        assert len(results) == 10
        for i in range(10):
            assert config.get(f"key_{i}") == f"value_{i}"
