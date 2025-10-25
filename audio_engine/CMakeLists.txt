cmake_minimum_required(VERSION 3.12)
project(audio_fingerprint_engine)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(pybind11 REQUIRED)
find_package(PkgConfig REQUIRED)

# Find FFTW3
pkg_check_modules(FFTW3 REQUIRED fftw3)

# Include directories
include_directories(include)
include_directories(${FFTW3_INCLUDE_DIRS})

# Source files
set(SOURCES
    src/audio_processor.cpp
    src/fft_processor.cpp
    src/peak_detector.cpp
    src/hash_generator.cpp
    src/python_bindings.cpp
)

# Create pybind11 module
pybind11_add_module(audio_fingerprint_engine ${SOURCES})

# Link libraries
target_link_libraries(audio_fingerprint_engine PRIVATE ${FFTW3_LIBRARIES})
target_compile_definitions(audio_fingerprint_engine PRIVATE VERSION_INFO=${EXAMPLE_VERSION_INFO})

# Compiler-specific options
if(MSVC)
    target_compile_options(audio_fingerprint_engine PRIVATE /W4)
else()
    target_compile_options(audio_fingerprint_engine PRIVATE -Wall -Wextra -O3)
endif()

# Platform-specific configurations
if(WIN32)
    # Windows-specific settings
    target_compile_definitions(audio_fingerprint_engine PRIVATE _WIN32_WINNT=0x0601)
elseif(APPLE)
    # macOS-specific settings
    set_target_properties(audio_fingerprint_engine PROPERTIES
        MACOSX_RPATH ON
        INSTALL_RPATH_USE_LINK_PATH ON
    )
endif()