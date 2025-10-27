@echo off
REM Windows build script for Qt6 Audio Fingerprinting Client

setlocal enabledelayedexpansion

REM Configuration
set BUILD_TYPE=%1
if "%BUILD_TYPE%"=="" set BUILD_TYPE=Release
set BUILD_DIR=build
set INSTALL_DIR=install

echo Building Audio Fingerprinting Client...
echo Build type: %BUILD_TYPE%

REM Create build directory
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
cd "%BUILD_DIR%"

REM Configure with CMake
cmake .. ^
    -DCMAKE_BUILD_TYPE=%BUILD_TYPE% ^
    -DCMAKE_INSTALL_PREFIX=../%INSTALL_DIR%

if %ERRORLEVEL% neq 0 (
    echo CMake configuration failed!
    exit /b 1
)

REM Build
cmake --build . --config %BUILD_TYPE% --parallel

if %ERRORLEVEL% neq 0 (
    echo Build failed!
    exit /b 1
)

REM Install
cmake --install . --config %BUILD_TYPE%

if %ERRORLEVEL% neq 0 (
    echo Install failed!
    exit /b 1
)

echo Build completed successfully!
echo Executable location: %INSTALL_DIR%\bin\

REM Windows-specific post-build
echo Windows: You may need to run windeployqt for distribution
echo Example: windeployqt --qmldir ../qml %INSTALL_DIR%\bin\AudioFingerprintingClient.exe

endlocal