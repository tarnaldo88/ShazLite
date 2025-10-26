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

# Find FFTW3 using vcpkg or system installation
set(FFTW3_FOUND FALSE)

# Try to find FFTW3f (single precision) using CMake config (vcpkg style)
find_package(FFTW3f CONFIG QUIET)
if(FFTW3f_FOUND)
    message(STATUS "Found FFTW3f via CMake config")
    set(FFTW3_LIBRARIES FFTW3::fftw3f)
    set(FFTW3_FOUND TRUE)
else()
    # Try to find regular FFTW3 using CMake config
    find_package(FFTW3 CONFIG QUIET)
    if(FFTW3_FOUND)
        message(STATUS "Found FFTW3 via CMake config")
        set(FFTW3_LIBRARIES FFTW3::fftw3f)  # Use single precision
    else()
        # Fallback: Try pkg-config
        find_package(PkgConfig QUIET)
        if(PkgConfig_FOUND)
            pkg_check_modules(FFTW3 fftw3f)
            if(FFTW3_FOUND)
                message(STATUS "Found FFTW3f via pkg-config")
            endif()
        endif()
    endif()
endif()

if(NOT FFTW3_FOUND)
    message(WARNING "FFTW3 not found. Audio processing may be limited.")
endif()

# Include directories
include_directories(include)

# Source files
set(SOURCES
    src/audio_preprocessor.cpp
    src/fft_processor.cpp
    src/peak_detector.cpp
    src/hash_generator.cpp
    src/python_bindings.cpp
)

# Create pybind11 module
pybind11_add_module(audio_fingerprint_engine ${SOURCES})

# Link libraries
if(FFTW3_FOUND)
    if(TARGET FFTW3::fftw3)
        # vcpkg style
        target_link_libraries(audio_fingerprint_engine PRIVATE FFTW3::fftw3)
    else()
        # pkg-config style
        target_include_directories(audio_fingerprint_engine PRIVATE ${FFTW3_INCLUDE_DIRS})
        target_link_libraries(audio_fingerprint_engine PRIVATE ${FFTW3_LIBRARIES})
    endif()
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