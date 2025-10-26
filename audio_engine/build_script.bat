@echo off
echo Building Audio Fingerprint Engine...
echo =====================================

REM Add CMake to PATH
set PATH=%PATH%;C:\Program Files\CMake\bin

REM Clean previous build
if exist build rmdir /s /q build

REM Configure with vcpkg
echo Configuring CMake...
cmake -B build -S . -DCMAKE_PREFIX_PATH=..\vcpkg\installed\x64-windows
if %ERRORLEVEL% neq 0 (
    echo Configuration failed!
    pause
    exit /b 1
)

REM Build the project
echo Building project...
cmake --build build --config Release
if %ERRORLEVEL% neq 0 (
    echo Build failed!
    pause
    exit /b 1
)

REM Copy built module and DLL
echo Copying built files...
copy "build\Release\audio_fingerprint_engine.cp312-win_amd64.pyd" "."
copy "..\vcpkg\installed\x64-windows\bin\fftw3f.dll" "."

REM Test the module
echo Testing module...
python -c "import audio_fingerprint_engine; print('✓ Module imported successfully')"
if %ERRORLEVEL% neq 0 (
    echo Module test failed!
    pause
    exit /b 1
)

echo =====================================
echo ✓ Build completed successfully!
echo ✓ Module is ready to use
pause