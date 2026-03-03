from setuptools import setup, find_packages

setup(
    name="qr-gen",
    version="0.1.0",
    description="QR Code Embedding Application for SVG to PDF conversion",
    author="QR-Gen Team",
    packages=find_packages(),
    install_requires=[
        "fpdf2>=2.7.0",
        "qrcode[pil]>=7.4.0",
        "Pillow>=10.0.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "qr-gen=src.main:main",
        ],
    },
)
