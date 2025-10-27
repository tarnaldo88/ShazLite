#!/usr/bin/env python3
"""
Verification script for Qt6 Audio Fingerprinting Client setup
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and report status"""
    if Path(filepath).exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} (MISSING)")
        return False

def check_directory_structure():
    """Verify the project directory structure"""
    print("Checking Qt6 project structure...")
    
    required_files = [
        ("CMakeLists.txt", "Main CMake configuration"),
        ("src/main.cpp", "Application entry point"),
        ("src/audiorecorder.h", "Audio recorder header"),
        ("src/audiorecorder.cpp", "Audio recorder implementation"),
        ("src/apiclient.h", "API client header"),
        ("src/apiclient.cpp", "API client implementation"),
        ("qml/Main.qml", "Main QML interface"),
        ("qml/RecordingView.qml", "Recording view QML"),
        ("qml/ResultsView.qml", "Results view QML"),
        ("qml/components/RecordButton.qml", "Record button component"),
        ("qml/components/LoadingIndicator.qml", "Loading indicator component"),
        ("resources/icons/microphone.svg", "Microphone icon"),
        ("resources/icons/loading.svg", "Loading icon"),
        ("Info.plist.in", "macOS bundle info template"),
        ("build.sh", "Unix build script"),
        ("build.bat", "Windows build script"),
        ("README.md", "Project documentation"),
    ]
    
    all_exist = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def check_cmake_structure():
    """Check CMakeLists.txt for required components"""
    print("\nChecking CMake configuration...")
    
    try:
        with open("CMakeLists.txt", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_components = [
            "cmake_minimum_required(VERSION 3.21)",
            "find_package(Qt6 REQUIRED COMPONENTS Core Quick Multimedia Network)",
            "qt_add_executable(AudioFingerprintingClient",
            "qt_add_qml_module(AudioFingerprintingClient",
            "target_link_libraries(AudioFingerprintingClient",
        ]
        
        for component in required_components:
            if component in content:
                print(f"✓ CMake component: {component}")
            else:
                print(f"✗ CMake component: {component} (MISSING)")
                return False
        
        return True
        
    except FileNotFoundError:
        print("✗ CMakeLists.txt not found")
        return False

def check_qml_structure():
    """Check QML file structure"""
    print("\nChecking QML structure...")
    
    qml_checks = [
        ("qml/Main.qml", "ApplicationWindow"),
        ("qml/RecordingView.qml", "RecordButton"),
        ("qml/ResultsView.qml", "result"),
        ("qml/components/RecordButton.qml", "isRecording"),
        ("qml/components/LoadingIndicator.qml", "running"),
    ]
    
    all_valid = True
    for filepath, expected_content in qml_checks:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            if expected_content in content:
                print(f"✓ QML file: {filepath} contains {expected_content}")
            else:
                print(f"✗ QML file: {filepath} missing {expected_content}")
                all_valid = False
        except FileNotFoundError:
            print(f"✗ QML file: {filepath} not found")
            all_valid = False
        except UnicodeDecodeError:
            print(f"✗ QML file: {filepath} has encoding issues")
            all_valid = False
    
    return all_valid

def main():
    """Main verification function"""
    print("Qt6 Audio Fingerprinting Client Setup Verification")
    print("=" * 50)
    
    # Change to client directory if not already there
    if not Path("CMakeLists.txt").exists():
        if Path("client/CMakeLists.txt").exists():
            os.chdir("client")
        else:
            print("Error: Could not find CMakeLists.txt in current or client directory")
            return False
    
    structure_ok = check_directory_structure()
    cmake_ok = check_cmake_structure()
    qml_ok = check_qml_structure()
    
    print("\n" + "=" * 50)
    if structure_ok and cmake_ok and qml_ok:
        print("✓ All checks passed! Qt6 project structure is complete.")
        print("\nNext steps:")
        print("1. Install Qt6 with Core, Quick, Multimedia, and Network components")
        print("2. Run build script: ./build.sh (Unix) or build.bat (Windows)")
        print("3. Test the application with a running backend server")
        return True
    else:
        print("✗ Some checks failed. Please review the missing components above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)