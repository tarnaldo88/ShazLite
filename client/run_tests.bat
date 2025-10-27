@echo off
echo Building and running Qt application tests...
echo.

cd /d "%~dp0"

if not exist "build" (
    echo Creating build directory...
    mkdir build
)

cd build

echo Configuring CMake...
cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Debug
if %errorlevel% neq 0 (
    echo CMake configuration failed!
    pause
    exit /b 1
)

echo Building project...
cmake --build . --config Debug
if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Running tests...
echo ================

echo.
echo Running API Client Test...
test_apiclient.exe
echo API Client Test completed with exit code: %errorlevel%

echo.
echo Running Extended API Client Test...
test_apiclient_extended.exe
echo Extended API Client Test completed with exit code: %errorlevel%

echo.
echo Running Audio Recorder Test...
test_audiorecorder.exe
echo Audio Recorder Test completed with exit code: %errorlevel%

if exist "test_qml_components.exe" (
    echo.
    echo Running QML Components Test...
    test_qml_components.exe
    echo QML Components Test completed with exit code: %errorlevel%
) else (
    echo QML Components Test not available (Qt6Qml/Qt6Quick not found)
)

echo.
echo Running CTest...
ctest --verbose
echo CTest completed with exit code: %errorlevel%

echo.
echo All tests completed!
pause