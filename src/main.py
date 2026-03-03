"""
Main entry point for QR Code Embedding Application.
"""

import tkinter as tk
import sys
import logging
from pathlib import Path

from .gui.main_window import MainWindow


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('qr_gen.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Main entry point."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting QR Code Embedding Application")
    
    try:
        # Create root window
        root = tk.Tk()
        
        # Create and run main window
        app = MainWindow(root)
        app.run()
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
