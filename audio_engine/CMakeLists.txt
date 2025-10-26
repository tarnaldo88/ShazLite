cmake_minimum_required(VERSION 3.12)
project(audio_fingerprint_engine)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Try multiple methods to find pybind11
set(PYBIND11_FOUND FALSE)

# Method 1: Use pybind11's Python module to get CMake directory
execute_process(
    COMMAND python -m pybind11 --cmakedir
    OUTPUT_VARIABLE pybind11_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE pybind11_result
)

if(pybind11_result EQUAL 0 AND pybind11_DIR)
    message(STATUS "Found pybind11 CMake directory: ${pybind11_DIR}")
    set(pybind11_DIR ${pybind11_DIR})
    find_package(pybind11 REQUIRED)
    set(PYBIND11_FOUND TRUE)
endif()

# Method 2: Try standard find_package
if(NOT PYBIND11_FOUND)
    find_package(pybind11 QUIET)
    if(pybind11_FOUND)
        set(PYBIND11_FOUND TRUE)
    endif()
endif()

# Method 3: Use pybind11's Python module directly
if(NOT PYBIND11_FOUND)
    execute_process(
        COMMAND python -c "import pybind11; print(pybind11.get_cmake_dir())"
        OUTPUT_VARIABLE pybind11_cmake_dir
        OUTPUT_STRIP_TRAILING_WHITESPACE
        RESULT_VARIABLE pybind11_python_result
    )
    
    if(pybind11_python_result EQUAL 0 AND pybind11_cmake_dir)
        message(STATUS "Found pybind11 via Python: ${pybind11_cmake_dir}")
        set(pybind11_DIR ${pybind11_cmake_dir})
        find_package(pybind11 REQUIRED)
        set(PYBIND11_FOUND TRUE)
    endif()
endif()

# Final check
if(NOT PYBIND11_FOUND)
    message(FATAL_ERROR "Could not find pybind11. Please install it with: pip install pybind11")
endif()

# Optional: Find FFTW3 (comment out if not available)
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(FFTW3 fftw3)
    if(FFTW3_FOUND)
        message(STATUS "Found FFTW3")
    else()
        message(WARNING "FFTW3 not found. Audio processing may be limited.")
    endif()
else()
    message(WARNING "PkgConfig not found. Skipping FFTW3 detection.")
endif()

# Include directories
include_directories(include)
if(FFTW3_FOUND)
    include_directories(${FFTW3_INCLUDE_DIRS})
endif()

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
if(FFTW3_FOUND)
    target_link_libraries(audio_fingerprint_engine PRIVATE ${FFTW3_LIBRARIES})
    target_compile_definitions(audio_fingerprint_engine PRIVATE HAVE_FFTW3)
endif()
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