"""
Main Tkinter window for QR Code Embedding Application.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Optional
import threading

from ..core.config_manager import ConfigManager
from ..core.app import QRCodeApp


class MainWindow:
    """Main application window."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the main window.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("QR Code Embedding Application")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Initialize config manager and app
        self.config_manager = ConfigManager()
        self.app = QRCodeApp(self.config_manager)
        
        # Variables for form inputs
        self.svg_path_var = tk.StringVar()
        self.csv_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.page_width_var = tk.StringVar(value="210.0")
        self.num_pages_var = tk.StringVar(value="10")
        
        # Load saved configuration
        self._load_config()
        
        # Build UI
        self._create_widgets()
        
        # Generation state
        self.is_generating = False
        
    def _load_config(self):
        """Load configuration from file."""
        svg_path = self.config_manager.get("svg_path", "")
        csv_path = self.config_manager.get("csv_path", "")
        output_path = self.config_manager.get("output_path", "")
        page_width = self.config_manager.get("page_width", "210.0")
        num_pages = self.config_manager.get("num_pages", "10")
        
        self.svg_path_var.set(svg_path)
        self.csv_path_var.set(csv_path)
        self.output_path_var.set(output_path)
        self.page_width_var.set(str(page_width))
        self.num_pages_var.set(str(num_pages))
        
    def _save_config(self):
        """Save current configuration to file."""
        self.config_manager.set("svg_path", self.svg_path_var.get())
        self.config_manager.set("csv_path", self.csv_path_var.get())
        self.config_manager.set("output_path", self.output_path_var.get())
        self.config_manager.set("page_width", self.page_width_var.get())
        self.config_manager.set("num_pages", self.num_pages_var.get())
        self.config_manager.save()
        
    def _create_widgets(self):
        """Create all UI widgets."""
        # Set background color
        bg_color = "#f0f0f0"
        self.root.configure(bg=bg_color)
        
        # Main container with padding
        main_frame = tk.Frame(self.root, padx=10, pady=10, bg=bg_color)
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="QR Code Embedding Application",
            font=("TkDefaultFont", 14, "bold"),
            bg=bg_color,
            fg="black"
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))
        
        # SVG File selection
        row = 1
        tk.Label(main_frame, text="SVG File:", bg=bg_color, fg="black").grid(
            row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5)
        )
        svg_entry = tk.Entry(main_frame, textvariable=self.svg_path_var, width=50)
        svg_entry.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        tk.Button(main_frame, text="Browse", command=self._browse_svg).grid(
            row=row, column=2, pady=5, padx=5
        )
        
        # CSV File selection
        row += 1
        tk.Label(main_frame, text="CSV File:", bg=bg_color, fg="black").grid(
            row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5)
        )
        csv_entry = tk.Entry(main_frame, textvariable=self.csv_path_var, width=50)
        csv_entry.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        tk.Button(main_frame, text="Browse", command=self._browse_csv).grid(
            row=row, column=2, pady=5, padx=5
        )
        
        # Output Folder selection
        row += 1
        tk.Label(main_frame, text="Output Folder:", bg=bg_color, fg="black").grid(
            row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5)
        )
        output_entry = tk.Entry(main_frame, textvariable=self.output_path_var, width=50)
        output_entry.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        tk.Button(main_frame, text="Browse", command=self._browse_output).grid(
            row=row, column=2, pady=5, padx=5
        )
        
        # Page Width input
        row += 1
        tk.Label(main_frame, text="Page Width (mm):", bg=bg_color, fg="black").grid(
            row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5)
        )
        width_entry = tk.Entry(main_frame, textvariable=self.page_width_var, width=20)
        width_entry.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Number of Pages input
        row += 1
        tk.Label(main_frame, text="Number of Pages:", bg=bg_color, fg="black").grid(
            row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5)
        )
        pages_entry = tk.Entry(main_frame, textvariable=self.num_pages_var, width=20)
        pages_entry.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Generate button
        row += 1
        self.generate_button = tk.Button(
            main_frame,
            text="Generate PDFs",
            command=self._generate_pdfs,
            bg="#4CAF50",
            fg="white",
            font=("TkDefaultFont", 12, "bold"),
            padx=20,
            pady=10
        )
        self.generate_button.grid(row=row, column=0, columnspan=3, pady=20)
        
        # Progress bar
        row += 1
        tk.Label(main_frame, text="Progress:", bg=bg_color, fg="black").grid(
            row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5)
        )
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.grid(row=row, column=1, columnspan=2, sticky="ew", pady=5, padx=5)
        
        # Status log
        row += 1
        tk.Label(main_frame, text="Status Log:", bg=bg_color, fg="black").grid(
            row=row, column=0, sticky="nw", pady=5, padx=(0, 5)
        )
        
        # Create frame for log with scrollbar
        log_frame = tk.Frame(main_frame, bg=bg_color)
        log_frame.grid(row=row+1, column=0, columnspan=3, sticky="nsew", pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.status_log = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            width=80,
            wrap=tk.WORD,
            state='disabled',
            bg="white",
            fg="black"
        )
        self.status_log.grid(row=0, column=0, sticky="nsew")
        
        # Configure main_frame row weight for log expansion
        main_frame.rowconfigure(row+1, weight=1)
        
        # Initial status message
        self._log_status("Ready to generate PDFs...")
        
    def _browse_svg(self):
        """Open file dialog to select SVG file."""
        filename = filedialog.askopenfilename(
            title="Select SVG File",
            filetypes=[("SVG files", "*.svg"), ("All files", "*.*")],
            initialdir=self._get_initial_dir(self.svg_path_var.get())
        )
        if filename:
            self.svg_path_var.set(filename)
            self._log_status(f"Selected SVG: {Path(filename).name}")
            
    def _browse_csv(self):
        """Open file dialog to select CSV file."""
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=self._get_initial_dir(self.csv_path_var.get())
        )
        if filename:
            self.csv_path_var.set(filename)
            self._log_status(f"Selected CSV: {Path(filename).name}")
            
    def _browse_output(self):
        """Open directory dialog to select output folder."""
        dirname = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=self._get_initial_dir(self.output_path_var.get())
        )
        if dirname:
            self.output_path_var.set(dirname)
            self._log_status(f"Selected output folder: {Path(dirname).name}")
            
    def _get_initial_dir(self, path: str) -> str:
        """Get initial directory for file dialog.
        
        Args:
            path: Current path value
            
        Returns:
            Initial directory path
        """
        if path and Path(path).exists():
            if Path(path).is_file():
                return str(Path(path).parent)
            return path
        return str(Path.home())
        
    def _log_status(self, message: str):
        """Add message to status log.
        
        Args:
            message: Status message to log
        """
        self.status_log.configure(state='normal')
        self.status_log.insert(tk.END, f"{message}\n")
        self.status_log.see(tk.END)
        self.status_log.configure(state='disabled')
        self.root.update_idletasks()
        
    def _validate_inputs(self) -> bool:
        """Validate all input fields.
        
        Returns:
            True if all inputs are valid, False otherwise
        """
        # Check SVG file
        svg_path = self.svg_path_var.get()
        if not svg_path:
            messagebox.showerror("Validation Error", "Please select an SVG file.")
            return False
        if not Path(svg_path).exists():
            messagebox.showerror("Validation Error", f"SVG file not found: {svg_path}")
            return False
            
        # Check CSV file
        csv_path = self.csv_path_var.get()
        if not csv_path:
            messagebox.showerror("Validation Error", "Please select a CSV file.")
            return False
        if not Path(csv_path).exists():
            messagebox.showerror("Validation Error", f"CSV file not found: {csv_path}")
            return False
            
        # Check output folder
        output_path = self.output_path_var.get()
        if not output_path:
            messagebox.showerror("Validation Error", "Please select an output folder.")
            return False
            
        # Check page width
        try:
            page_width = float(self.page_width_var.get())
            if page_width <= 0:
                raise ValueError("Page width must be positive")
        except ValueError as e:
            messagebox.showerror("Validation Error", f"Invalid page width: {e}")
            return False
            
        # Check number of pages
        try:
            num_pages = int(self.num_pages_var.get())
            if num_pages <= 0:
                raise ValueError("Number of pages must be positive")
        except ValueError as e:
            messagebox.showerror("Validation Error", f"Invalid number of pages: {e}")
            return False
            
        return True
        
    def _progress_callback(self, current: int, total: int, message: str):
        """Update progress bar.
        
        Args:
            current: Current page number
            total: Total number of pages
            message: Status message
        """
        progress = (current / total) * 100 if total > 0 else 0
        self.progress_var.set(progress)
        self._log_status(message)
        
    def _generate_pdfs(self):
        """Generate PDFs in a separate thread."""
        if self.is_generating:
            return
            
        # Validate inputs
        if not self._validate_inputs():
            return
            
        # Save configuration
        self._save_config()
        
        # Disable generate button
        self.is_generating = True
        self.generate_button.configure(state='disabled')
        
        # Reset progress
        self.progress_var.set(0)
        self._log_status("\n" + "="*50)
        self._log_status("Starting PDF generation...")
        
        # Run generation in separate thread
        thread = threading.Thread(target=self._run_generation, daemon=True)
        thread.start()
        
    def _run_generation(self):
        """Run PDF generation (called in separate thread)."""
        try:
            svg_path = self.svg_path_var.get()
            csv_path = self.csv_path_var.get()
            output_path = self.output_path_var.get()
            page_width = float(self.page_width_var.get())
            num_pages = int(self.num_pages_var.get())
            
            # Generate pages
            generated_files = self.app.generate_pages(
                svg_path=svg_path,
                csv_path=csv_path,
                page_width_mm=page_width,
                num_pages=num_pages,
                output_root=output_path,
                progress_callback=self._progress_callback
            )
            
            # Success message
            self.root.after(0, lambda: self._generation_complete(generated_files))
            
        except Exception as e:
            # Error message
            self.root.after(0, lambda: self._generation_error(str(e)))
            
    def _generation_complete(self, generated_files: list[str]):
        """Handle successful generation completion.
        
        Args:
            generated_files: List of generated file paths
        """
        self._log_status("="*50)
        self._log_status(f"✓ Successfully generated {len(generated_files)} PDF file(s)")
        self._log_status("\nGenerated files:")
        for file_path in generated_files:
            self._log_status(f"  • {file_path}")
        self._log_status("="*50)
        
        messagebox.showinfo(
            "Success",
            f"Successfully generated {len(generated_files)} PDF file(s)!"
        )
        
        # Re-enable generate button
        self.generate_button.configure(state='normal')
        self.is_generating = False
        
    def _generation_error(self, error_message: str):
        """Handle generation error.
        
        Args:
            error_message: Error message
        """
        self._log_status("="*50)
        self._log_status(f"✗ Error: {error_message}")
        self._log_status("="*50)
        
        messagebox.showerror("Generation Error", f"Failed to generate PDFs:\n\n{error_message}")
        
        # Re-enable generate button
        self.generate_button.configure(state='normal')
        self.is_generating = False
        
    def run(self):
        """Start the main event loop."""
        self.root.mainloop()
