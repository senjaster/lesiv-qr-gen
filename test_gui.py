#!/usr/bin/env python3
"""
Quick test script to verify GUI components can be imported and instantiated.
This doesn't actually show the window, just tests that everything loads correctly.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

def test_gui_imports():
    """Test that all GUI components can be imported."""
    print("Testing GUI imports...")
    
    try:
        import tkinter as tk
        print("✓ tkinter imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import tkinter: {e}")
        return False
    
    try:
        from src.gui.main_window import MainWindow
        print("✓ MainWindow imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import MainWindow: {e}")
        return False
    
    try:
        from src.core.config_manager import ConfigManager
        print("✓ ConfigManager imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import ConfigManager: {e}")
        return False
    
    try:
        from src.core.app import QRCodeApp
        print("✓ QRCodeApp imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import QRCodeApp: {e}")
        return False
    
    return True


def test_gui_instantiation():
    """Test that GUI can be instantiated (without showing)."""
    print("\nTesting GUI instantiation...")
    
    try:
        import tkinter as tk
        from src.gui.main_window import MainWindow
        
        # Create root window (but don't show it)
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Create main window
        app = MainWindow(root)
        print("✓ MainWindow instantiated successfully")
        
        # Check that key components exist
        assert hasattr(app, 'svg_path_var'), "Missing svg_path_var"
        assert hasattr(app, 'csv_path_var'), "Missing csv_path_var"
        assert hasattr(app, 'output_path_var'), "Missing output_path_var"
        assert hasattr(app, 'page_width_var'), "Missing page_width_var"
        assert hasattr(app, 'num_pages_var'), "Missing num_pages_var"
        assert hasattr(app, 'generate_button'), "Missing generate_button"
        assert hasattr(app, 'progress_bar'), "Missing progress_bar"
        assert hasattr(app, 'status_log'), "Missing status_log"
        print("✓ All required components present")
        
        # Destroy the window
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to instantiate GUI: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("GUI Component Test")
    print("="*60)
    
    success = True
    
    if not test_gui_imports():
        success = False
    
    if not test_gui_instantiation():
        success = False
    
    print("\n" + "="*60)
    if success:
        print("✓ All GUI tests passed!")
        print("="*60)
        return 0
    else:
        print("✗ Some GUI tests failed")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
