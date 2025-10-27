# Qt6 Installation Guide for Audio Fingerprinting Client

## Current Issue

The project requires Qt6 with proper compiler compatibility. The current Qt 6.9.3 installation has compatibility issues with both MSVC and MinGW compilers.

## Recommended Solutions

### Option 1: Install Qt6 with MSVC (Recommended)

1. **Download Qt Online Installer**

   - Go to https://www.qt.io/download-qt-installer
   - Download the Qt Online Installer

2. **Install Qt6 with MSVC**

   - Run the installer
   - Select Qt 6.5.x or 6.6.x (more stable than 6.9.3)
   - Choose components:
     - Qt 6.x.x → MSVC 2019 64-bit (or MSVC 2022 64-bit)
     - Qt 6.x.x → Qt Quick
     - Qt 6.x.x → Qt Multimedia
     - Developer and Designer Tools → CMake (if not already installed)

3. **Configure CMake**
   ```powershell
   # Replace X.X.X with your Qt version (e.g., 6.5.3)
   cmake -B client/build -S client -DCMAKE_BUILD_TYPE=Debug -DCMAKE_PREFIX_PATH="C:\Qt\X.X.X\msvc2019_64"
   ```

### Option 2: Use vcpkg (Alternative)

1. **Install vcpkg**

   ```powershell
   git clone https://github.com/Microsoft/vcpkg.git
   cd vcpkg
   .\bootstrap-vcpkg.bat
   ```

2. **Install Qt6 via vcpkg**

   ```powershell
   .\vcpkg install qt6-base qt6-multimedia qt6-quick
   ```

3. **Configure CMake with vcpkg**
   ```powershell
   cmake -B client/build -S client -DCMAKE_TOOLCHAIN_FILE=path/to/vcpkg/scripts/buildsystems/vcpkg.cmake
   ```

### Option 3: Fix Current MinGW Installation

If you prefer to use the current installation, try these fixes:

1. **Update CMakeLists.txt for MinGW compatibility**

   ```cmake
   # Add this after find_package(Qt6...)
   if(MINGW)
       target_link_libraries(AudioFingerprintingClient PRIVATE -static-libgcc -static-libstdc++)
   endif()
   ```

2. **Use older Qt version**
   - Qt 6.5.x has better MinGW compatibility than 6.9.x

## Current Build Configuration

The project is configured to build with:

- **Qt Components**: Core, Quick, Multimedia, Network
- **C++ Standard**: C++17
- **Build System**: CMake 3.21+

## Testing the Installation

After installing Qt6, test the configuration:

```powershell
# Configure
cmake -B client/build -S client -DCMAKE_PREFIX_PATH="path/to/qt6"

# Build
cmake --build client/build --config Debug

# Run (if build succeeds)
./client/build/AudioFingerprintingClient.exe
```

## Troubleshooting

### Common Issues:

1. **"Qt6 not found"**

   - Ensure CMAKE_PREFIX_PATH points to the correct Qt installation
   - Example: `C:\Qt\6.5.3\msvc2019_64`

2. **Compiler compatibility errors**

   - Use MSVC compiler with MSVC Qt build
   - Use MinGW compiler with MinGW Qt build
   - Don't mix compilers

3. **Linking errors**
   - Ensure all required Qt modules are installed
   - Check that the Qt version supports your compiler

### Verification Commands:

```powershell
# Check Qt installation
dir "C:\Qt"

# Check CMake can find Qt
cmake -B temp_build -S client -DCMAKE_PREFIX_PATH="C:\Qt\6.5.3\msvc2019_64" --debug-find

# Check compiler
where cl.exe  # For MSVC
where gcc.exe # For MinGW
```

## Next Steps

1. Choose one of the installation options above
2. Install Qt6 with proper compiler support
3. Configure the build with the correct CMAKE_PREFIX_PATH
4. Build and test the application

The results display interface implementation is complete and ready to test once Qt6 is properly configured.
