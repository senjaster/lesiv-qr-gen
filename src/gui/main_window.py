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
        self.root.title("Приложение для встраивания QR-кодов")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Set window icon
        self._set_window_icon()
        
        # Initialize config manager and app
        self.config_manager = ConfigManager()
        self.app = QRCodeApp(self.config_manager)
        
        # Variables for form inputs
        self.template_path_var = tk.StringVar()
        self.csv_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.num_pages_var = tk.StringVar(value="10")
        self.qr_base_url_var = tk.StringVar()
        
        # Load saved configuration
        self._load_config()
        
        # Build UI
        self._create_widgets()
        
        # Generation state
        self.is_generating = False
        
        # Register window close handler to save config
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _set_window_icon(self):
        """Set the window icon from PNG file."""
        try:
            # Get the icon path relative to the project root
            icon_path = Path(__file__).parent.parent.parent / "icon_256.png"
            
            if icon_path.exists():
                # Load icon using PhotoImage
                icon = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, icon)
            else:
                # Fallback: try current directory (for packaged app)
                icon_path = Path("icon_256.png")
                if icon_path.exists():
                    icon = tk.PhotoImage(file=str(icon_path))
                    self.root.iconphoto(True, icon)
        except Exception as e:
            # Silently fail if icon cannot be loaded
            print(f"Warning: Could not load window icon: {e}")
        
    def _load_config(self):
        """Load configuration from file."""
        pdf_path = self.config_manager.get("pdf_path", "")
        csv_path = self.config_manager.get("csv_path", "")
        output_path = self.config_manager.get("output_folder", "")
        num_pages = self.config_manager.get("num_pages", "10")
        qr_base_url = self.config_manager.get("qr_base_url", ConfigManager.DEFAULT_QR_BASE_URL)
        
        self.template_path_var.set(pdf_path)
        self.csv_path_var.set(csv_path)
        self.output_path_var.set(output_path)
        self.num_pages_var.set(str(num_pages))
        self.qr_base_url_var.set(qr_base_url)
        
    def _save_config(self):
        """Save current configuration to file."""
        self.config_manager.set("pdf_path", self.template_path_var.get())
        self.config_manager.set("csv_path", self.csv_path_var.get())
        self.config_manager.set("output_folder", self.output_path_var.get())
        self.config_manager.set("num_pages", self.num_pages_var.get())
        self.config_manager.set("qr_base_url", self.qr_base_url_var.get())
        self.config_manager.save()
        
        # Reinitialize app with new QR base URL
        self.app = QRCodeApp(self.config_manager)
        
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
        

        # Template File selection (PDF only)
        row = 1
        tk.Label(main_frame, text="Шаблон:", bg=bg_color, fg="black").grid(
            row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5)
        )
        template_entry = tk.Entry(main_frame, textvariable=self.template_path_var, width=50)
        template_entry.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        tk.Button(main_frame, text="Обзор", command=self._browse_template).grid(
            row=row, column=2, pady=5, padx=5
        )
        
        # CSV File selection
        row += 1
        tk.Label(main_frame, text="Положение QR-кодов:", bg=bg_color, fg="black").grid(
            row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5)
        )
        csv_entry = tk.Entry(main_frame, textvariable=self.csv_path_var, width=50)
        csv_entry.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        tk.Button(main_frame, text="Обзор", command=self._browse_csv).grid(
            row=row, column=2, pady=5, padx=5
        )
        
        # Output Folder selection
        row += 1
        tk.Label(main_frame, text="Готовые файлы:", bg=bg_color, fg="black").grid(
            row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5)
        )
        output_entry = tk.Entry(main_frame, textvariable=self.output_path_var, width=50)
        output_entry.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        tk.Button(main_frame, text="Обзор", command=self._browse_output).grid(
            row=row, column=2, pady=5, padx=5
        )
        
        # Number of Pages input
        row += 1
        tk.Label(main_frame, text="Количество страниц:", bg=bg_color, fg="black").grid(
            row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5)
        )
        pages_entry = tk.Entry(main_frame, textvariable=self.num_pages_var, width=20)
        pages_entry.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        
        # QR Base URL input
        row += 1
        tk.Label(main_frame, text="Базовый URL QR-кода:", bg=bg_color, fg="black").grid(
            row=row, column=0, sticky=tk.W, pady=5, padx=(0, 5)
        )
        qr_url_entry = tk.Entry(main_frame, textvariable=self.qr_base_url_var, width=50)
        qr_url_entry.grid(row=row, column=1, columnspan=2, sticky="ew", pady=5, padx=5)
        
        # Generate button
        row += 1
        self.generate_button = tk.Button(
            main_frame,
            text="Сгенерировать PDF",
            command=self._generate_pdfs,
            font=("TkDefaultFont", 12, "bold"),
            padx=20,
            pady=10
        )
        self.generate_button.grid(row=row, column=0, columnspan=3, pady=20)
        
        # Progress bar
        row += 1
        tk.Label(main_frame, text="Прогресс:", bg=bg_color, fg="black").grid(
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
        tk.Label(main_frame, text="Сообщения:", bg=bg_color, fg="black").grid(
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
        self._log_status("Готов к созданию PDF...")
        
    def _browse_template(self):
        """Open file dialog to select PDF template file."""
        filename = filedialog.askopenfilename(
            title="Выберите файл шаблона PDF",
            filetypes=[
                ("Файлы PDF", "*.pdf"),
                ("Все файлы", "*.*")
            ],
            initialdir=self._get_initial_dir(self.template_path_var.get())
        )
        if filename:
            self.template_path_var.set(filename)
            self._log_status(f"Выбран шаблон PDF: {Path(filename).name}")
            
    def _browse_csv(self):
        """Open file dialog to select CSV file."""
        filename = filedialog.askopenfilename(
            title="Выберите файл CSV",
            filetypes=[("Файлы CSV", "*.csv"), ("Все файлы", "*.*")],
            initialdir=self._get_initial_dir(self.csv_path_var.get())
        )
        if filename:
            self.csv_path_var.set(filename)
            self._log_status(f"Выбран CSV: {Path(filename).name}")
            
    def _browse_output(self):
        """Open directory dialog to select output folder."""
        dirname = filedialog.askdirectory(
            title="Выберите папку для сохранения результатов",
            initialdir=self._get_initial_dir(self.output_path_var.get())
        )
        if dirname:
            self.output_path_var.set(dirname)
            self._log_status(f"Выбрана папка для сохранения результатов: {Path(dirname).name}")
            
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
        # Check template file
        template_path = self.template_path_var.get()
        if not template_path:
            messagebox.showerror("Ошибка валидации", "Пожалуйста, выберите файл шаблона PDF.")
            return False
        if not Path(template_path).exists():
            messagebox.showerror("Ошибка валидации", f"Файл шаблона PDF не найден: {template_path}")
            return False
        if Path(template_path).suffix.lower() != '.pdf':
            messagebox.showerror("Ошибка валидации", f"Шаблон должен быть файлом PDF: {template_path}")
            return False
            
        # Check CSV file
        csv_path = self.csv_path_var.get()
        if not csv_path:
            messagebox.showerror("Ошибка валидации", "Пожалуйста, выберите файл CSV.")
            return False
        if not Path(csv_path).exists():
            messagebox.showerror("Ошибка валидации", f"Файл CSV не найден: {csv_path}")
            return False
            
        # Check output folder
        output_path = self.output_path_var.get()
        if not output_path:
            messagebox.showerror("Ошибка валидации", "Пожалуйста, выберите папку вывода.")
            return False
            
        # Check number of pages
        try:
            num_pages = int(self.num_pages_var.get())
            if num_pages <= 0:
                raise ValueError("Количество страниц должно быть положительным")
        except ValueError as e:
            messagebox.showerror("Ошибка валидации", f"Неверное количество страниц: {e}")
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
        self._log_status("Начало создания PDF...")
        
        # Run generation in separate thread
        thread = threading.Thread(target=self._run_generation, daemon=True)
        thread.start()
        
    def _run_generation(self):
        """Run PDF generation (called in separate thread)."""
        try:
            pdf_path = self.template_path_var.get()
            csv_path = self.csv_path_var.get()
            output_path = self.output_path_var.get()
            num_pages = int(self.num_pages_var.get())
            
            # Generate pages
            generated_files = self.app.generate_pages(
                pdf_path=pdf_path,
                csv_path=csv_path,
                num_pages=num_pages,
                output_root=output_path,
                progress_callback=self._progress_callback
            )
            
            # Success message
            self.root.after(0, lambda: self._generation_complete(generated_files))
            
        except Exception as e:
            # Error message - capture error string immediately
            error_msg = str(e)
            self.root.after(0, lambda: self._generation_error(error_msg))
            
    def _generation_complete(self, generated_files: list[str]):
        """Handle successful generation completion.
        
        Args:
            generated_files: List of generated file paths
        """
        self._log_status("="*50)
        self._log_status(f"✓ Успешно создано {len(generated_files)} PDF файл(ов)")
        self._log_status("="*50)
        
        messagebox.showinfo(
            "Успех",
            f"Успешно создано {len(generated_files)} PDF файл(ов)!"
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
        self._log_status(f"✗ Ошибка: {error_message}")
        self._log_status("="*50)
        
        messagebox.showerror("Ошибка создания", f"Не удалось создать PDF:\n\n{error_message}")
        
        # Re-enable generate button
        self.generate_button.configure(state='normal')
        self.is_generating = False
        
    def _on_closing(self):
        """Handle window close event - save config before closing."""
        # Save current configuration
        self.config_manager.set("pdf_path", self.template_path_var.get())
        self.config_manager.set("csv_path", self.csv_path_var.get())
        self.config_manager.set("output_folder", self.output_path_var.get())
        self.config_manager.set("num_pages", self.num_pages_var.get())
        self.config_manager.set("qr_base_url", self.qr_base_url_var.get())
        self.config_manager.save()
        
        # Close the window
        self.root.destroy()
        
    def run(self):
        """Start the main event loop."""
        self.root.mainloop()
