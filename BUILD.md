# Building QR-Gen Windows Executable

This guide explains how to build a standalone Windows executable (.exe) for the QR-Gen application.

## Prerequisites

- Windows operating system
- Python 3.8 or higher installed
- Git (optional, for cloning the repository)

## Quick Build

### Option 1: Using the Build Script (Recommended)

1. Open Command Prompt or PowerShell in the project directory
2. Run the build script:
   ```batch
   build.bat
   ```
3. Wait for the build process to complete
4. Find the executable in `dist\QR-Gen.exe`

### Option 2: Manual Build

1. Install dependencies:
   ```batch
   pip install -r requirements.txt
   pip install -r requirements-build.txt
   ```

2. Clean previous builds (if any):
   ```batch
   rmdir /s /q build dist
   ```

3. Build the executable:
   ```batch
   pyinstaller qr-gen.spec --clean
   ```

4. The executable will be created in the `dist` folder

## Build Output

After a successful build, you will find:
- `dist\QR-Gen.exe` - The standalone executable (can be distributed)
- `build\` - Temporary build files (can be deleted)

## Distribution

The `QR-Gen.exe` file in the `dist` folder is a standalone executable that can be:
- Copied to any Windows computer
- Run without installing Python or any dependencies
- Distributed to end users

## Customization

### Adding an Icon

1. Create or obtain a `.ico` file for your application
2. Place it in the project directory (e.g., `icon.ico`)
3. Edit `qr-gen.spec` and update the icon line:
   ```python
   icon='icon.ico',
   ```
4. Rebuild using `build.bat`

### Console Window

By default, the application runs without a console window (GUI mode). To show a console window for debugging:

1. Edit `qr-gen.spec`
2. Change `console=False` to `console=True`
3. Rebuild

### File Size Optimization

The executable includes all dependencies and may be large (50-100 MB). To reduce size:

1. Use UPX compression (already enabled in the spec file)
2. Remove unused dependencies from `requirements.txt`
3. Consider using PyInstaller's `--onedir` mode instead of `--onefile`

## Troubleshooting

### Build Fails

- Ensure all dependencies are installed: `pip install -r requirements.txt -r requirements-build.txt`
- Try cleaning build artifacts: `rmdir /s /q build dist`
- Check Python version: `python --version` (should be 3.8+)

### Executable Doesn't Run

- Check Windows Defender or antivirus (may flag PyInstaller executables)
- Run from Command Prompt to see error messages
- Rebuild with `console=True` in the spec file for debugging

### Missing Files or Resources

- Ensure the `examples` folder is included in the build
- Check the `datas` section in `qr-gen.spec`
- Add any missing data files to the spec file

### Import Errors

- Add missing modules to `hiddenimports` in `qr-gen.spec`
- Common missing imports: tkinter modules, PIL modules, reportlab components

## Testing the Executable

1. Copy `QR-Gen.exe` to a test directory
2. Copy the `examples` folder (if needed for testing)
3. Run the executable
4. Test all features:
   - Load CSV file
   - Select PDF template
   - Generate QR codes
   - Save output

## Advanced Configuration

For advanced PyInstaller options, refer to:
- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- Edit `qr-gen.spec` for custom configurations

## Notes

- The first run may be slower as Windows scans the executable
- The executable is platform-specific (Windows only)
- For cross-platform distribution, build on each target OS
- Consider code signing for production distribution
