"""
Setup script for building the C++ audio fingerprinting engine with pybind11.
"""
from pybind11.setup_helpers import Pybind11Extension, build_ext
from pybind11 import get_cmake_dir
import pybind11
from setuptools import setup, Extension
import os
import platform

# Define the extension module
ext_modules = [
    Pybind11Extension(
        "audio_fingerprint_engine",
        [
            "src/audio_processor.cpp",
            "src/audio_preprocessor.cpp",
            "src/fft_processor.cpp", 
            "src/peak_detector.cpp",
            "src/hash_generator.cpp",
            "src/python_bindings.cpp",
        ],
        include_dirs=[
            "include",
            pybind11.get_include(),
        ],
        libraries=["fftw3", "fftw3f"],
        library_dirs=[],
        cxx_std=17,
        define_macros=[("VERSION_INFO", '"dev"')],
    ),
]

# Platform-specific configurations
if platform.system() == "Windows":
    # Windows-specific library paths and flags
    for ext in ext_modules:
        # For Windows, build without FFTW initially and use a simpler FFT implementation
        ext.libraries = []  # Remove FFTW dependency for now
        ext.library_dirs = []  # Clear library dirs to avoid conflicts
        ext.define_macros.append(("NO_FFTW", "1"))
elif platform.system() == "Darwin":
    # macOS-specific configurations
    for ext in ext_modules:
        ext.library_dirs.extend([
            "/usr/local/lib",
            "/opt/homebrew/lib",
        ])
        ext.include_dirs.extend([
            "/usr/local/include",
            "/opt/homebrew/include",
        ])
else:
    # Linux-specific configurations
    for ext in ext_modules:
        ext.library_dirs.extend([
            "/usr/lib",
            "/usr/local/lib",
        ])
        ext.include_dirs.extend([
            "/usr/include",
            "/usr/local/include",
        ])

setup(
    name="audio_fingerprint_engine",
    version="0.1.0",
    author="Audio Fingerprinting Team",
    description="C++ audio fingerprinting engine with Python bindings",
    long_description="""
    High-performance audio fingerprinting engine for music identification.
    
    This package provides Python bindings for a C++ audio fingerprinting engine
    that can generate unique fingerprints from audio samples for music identification
    applications similar to Shazam.
    
    Features:
    - Fast C++ implementation with Python bindings
    - Support for mono and stereo audio
    - Automatic preprocessing (resampling, normalization)
    - Batch processing for reference song databases
    - Cross-platform compatibility (Windows, macOS, Linux)
    """,
    long_description_content_type="text/plain",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "pybind11>=2.6.0",
        "numpy>=1.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: C++",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    keywords="audio fingerprinting music identification signal processing",
)