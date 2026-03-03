"""Integration tests for the complete workflow."""

import pytest
from pathlib import Path
from src.core.config_manager import ConfigManager
from src.core.id_manager import IDManager
from src.core.csv_parser import CSVParser, QRPosition
from src.core.qr_generator import QRGenerator
from src.core.pdf_processor import PDFProcessor
from src.core.pdf_generator import PDFGenerator


class TestIntegration:
    """Integration tests for complete workflow."""
    
    @pytest.fixture
    def sample_pdf(self, tmp_path):
        """Create a sample PDF file."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        
        pdf_file = tmp_path / "sample.pdf"
        c = canvas.Canvas(str(pdf_file), pagesize=A4)
        c.drawString(100, 750, "Sample Document")
        c.save()
        return str(pdf_file)
    
    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create a sample CSV file."""
        csv_content = """x_mm,y_mm,size_mm,rotation_deg
50.0,50.0,20.0,0
160.0,50.0,20.0,0
105.0,247.0,20.0,0"""
        csv_file = tmp_path / "positions.csv"
        csv_file.write_text(csv_content)
        return str(csv_file)
    
    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create output directory."""
        output = tmp_path / "output"
        output.mkdir()
        return str(output)
    
    def test_complete_single_page_workflow(self, sample_pdf, sample_csv, output_dir):
        """Test complete workflow for generating a single page."""
        # Parse CSV
        positions = CSVParser.parse(sample_csv)
        assert len(positions) == 3
        
        # Process PDF
        pdf_processor = PDFProcessor(sample_pdf)
        page_width, page_height = pdf_processor.get_page_dimensions_mm()
        assert page_width > 0
        assert page_height > 0
        
        # Initialize ID manager
        id_manager = IDManager(output_dir)
        page_num, start_id = id_manager.get_next_page_info()
        assert page_num == 1
        assert start_id > 0
        
        # Generate QR codes
        qr_generator = QRGenerator(base_url=ConfigManager.DEFAULT_QR_BASE_URL)
        qr_ids = id_manager.generate_ids(len(positions))
        qr_images = {}
        for idx, (qr_id, pos) in enumerate(zip(qr_ids, positions)):
            qr_images[idx] = qr_generator.generate(qr_id, pos.size_mm)
        
        # Generate filename
        filename = id_manager.format_filename(page_num, min(qr_ids), max(qr_ids))
        output_path = id_manager.get_output_path() / filename
        
        # Create PDF
        pdf_generator = PDFGenerator(pdf_processor)
        pdf_generator.create_page(positions, qr_images, str(output_path))
        
        # Verify output
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        
        # Verify filename format
        assert output_path.name.startswith("001-")
        assert ".pdf" in output_path.name
    
    def test_complete_multiple_pages_workflow(self, sample_pdf, sample_csv, output_dir):
        """Test complete workflow for generating multiple pages."""
        num_pages = 3
        
        # Parse CSV
        positions = CSVParser.parse(sample_csv)
        
        # Process PDF
        pdf_processor = PDFProcessor(sample_pdf)
        
        # Initialize components
        id_manager = IDManager(output_dir)
        qr_generator = QRGenerator(base_url=ConfigManager.DEFAULT_QR_BASE_URL)
        pdf_generator = PDFGenerator(pdf_processor)
        
        created_files = []
        
        # Generate multiple pages
        for page_idx in range(num_pages):
            # Get next page info
            page_num, start_id = id_manager.get_next_page_info()
            
            # Generate QR codes
            qr_ids = id_manager.generate_ids(len(positions))
            qr_images = {}
            for idx, (qr_id, pos) in enumerate(zip(qr_ids, positions)):
                qr_images[idx] = qr_generator.generate(qr_id, pos.size_mm)
            
            # Generate filename
            filename = id_manager.format_filename(page_num, min(qr_ids), max(qr_ids))
            output_path = id_manager.get_output_path() / filename
            
            # Create PDF
            pdf_generator.create_page(positions, qr_images, str(output_path))
            created_files.append(output_path)
            
            # Update page info for next iteration
            id_manager.update_page_info(page_num, max(qr_ids))
        
        # Verify all files created
        assert len(created_files) == num_pages
        for idx, file_path in enumerate(created_files, 1):
            assert file_path.exists()
            assert file_path.name.startswith(f"{idx:03d}-")
    
    def test_id_continuity_across_runs(self, sample_pdf, sample_csv, output_dir):
        """Test that IDs continue correctly across multiple runs."""
        positions = CSVParser.parse(sample_csv)
        pdf_processor = PDFProcessor(sample_pdf)
        qr_generator = QRGenerator(base_url=ConfigManager.DEFAULT_QR_BASE_URL)
        pdf_generator = PDFGenerator(pdf_processor)
        
        # First run - create 2 pages
        id_manager1 = IDManager(output_dir)
        last_id = 0
        
        for _ in range(2):
            page_num, start_id = id_manager1.get_next_page_info()
            qr_ids = id_manager1.generate_ids(len(positions))
            last_id = max(qr_ids)
            
            qr_images = {}
            for idx, (qr_id, pos) in enumerate(zip(qr_ids, positions)):
                qr_images[idx] = qr_generator.generate(qr_id, pos.size_mm)
            
            filename = id_manager1.format_filename(page_num, min(qr_ids), max(qr_ids))
            output_path = id_manager1.get_output_path() / filename
            pdf_generator.create_page(positions, qr_images, str(output_path))
            
            # Update page info for next iteration
            id_manager1.update_page_info(page_num, max(qr_ids))
        
        # Second run - create 1 more page (simulating restart)
        id_manager2 = IDManager(output_dir)
        page_num, start_id = id_manager2.get_next_page_info()
        
        # Start ID should be after last ID from first run
        assert start_id == last_id + 1
        assert page_num == 3
    
    def test_config_persistence(self, tmp_path, sample_pdf, sample_csv, output_dir):
        """Test configuration persistence across runs."""
        config_path = tmp_path / "test_config.ini"
        
        # First run - save config
        config1 = ConfigManager(str(config_path))
        config1.set("pdf_path", sample_pdf)
        config1.set("csv_path", sample_csv)
        config1.set("output_folder", output_dir)
        config1.set("num_pages", 5)
        config1.save()
        
        # Second run - load config
        config2 = ConfigManager(str(config_path))
        config2.load()
        
        assert config2.get("pdf_path") == sample_pdf
        assert config2.get("csv_path") == sample_csv
        assert config2.get("output_folder") == output_dir
        assert int(config2.get("num_pages")) == 5
    
    def test_workflow_with_rotation(self, sample_pdf, tmp_path, output_dir):
        """Test workflow with rotated QR codes."""
        # Create CSV with rotation
        csv_content = """x_mm,y_mm,size_mm,rotation_deg
50.0,50.0,20.0,45
160.0,50.0,20.0,90
105.0,247.0,20.0,180"""
        csv_file = tmp_path / "positions_rotated.csv"
        csv_file.write_text(csv_content)
        
        # Parse and process
        positions = CSVParser.parse(str(csv_file))
        pdf_processor = PDFProcessor(sample_pdf)
        id_manager = IDManager(output_dir)
        qr_generator = QRGenerator(base_url=ConfigManager.DEFAULT_QR_BASE_URL)
        pdf_generator = PDFGenerator(pdf_processor)
        
        # Generate page
        page_num, start_id = id_manager.get_next_page_info()
        qr_ids = id_manager.generate_ids(len(positions))
        
        qr_images = {}
        for idx, (qr_id, pos) in enumerate(zip(qr_ids, positions)):
            qr_images[idx] = qr_generator.generate(qr_id, pos.size_mm)
        
        filename = id_manager.format_filename(page_num, min(qr_ids), max(qr_ids))
        output_path = id_manager.get_output_path() / filename
        
        pdf_generator.create_page(positions, qr_images, str(output_path))
        
        # Verify
        assert output_path.exists()
