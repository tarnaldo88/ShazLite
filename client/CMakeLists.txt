cmake_minimum_required(VERSION 3.21)

project(AudioFingerprintingClient VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# MSVC specific settings for C++17
if(MSVC)
    add_compile_options(/Zc:__cplusplus /permissive-)
endif()

# Find Qt6 components
find_package(Qt6 REQUIRED COMPONENTS Core Quick QuickControls2 Multimedia Network)

# Enable automatic MOC, UIC, and RCC processing
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# Set up Qt6 QML module
qt_standard_project_setup()

# Define the executable
qt_add_executable(AudioFingerprintingClient
    src/main.cpp
    src/audiorecorder.cpp
    src/audiorecorder.h
    src/apiclient.cpp
    src/apiclient.h
)

# Add QML module
qt_add_qml_module(AudioFingerprintingClient
    URI AudioFingerprinting
    VERSION 1.0
    QML_FILES
        qml/Main.qml
        qml/RecordingView.qml
        qml/ResultsView.qml
        qml/components/RecordButton.qml
        qml/components/LoadingIndicator.qml
        qml/components/ConfidenceIndicator.qml
        qml/components/ErrorDisplay.qml
        qml/components/ProcessingAnimation.qml
    RESOURCES
        resources/icons/microphone.svg
        resources/icons/loading.svg
        public/ShazLiteTorres.png
)

# Link Qt6 libraries
target_link_libraries(AudioFingerprintingClient PRIVATE
    Qt6::Core
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::Multimedia
    Qt6::Network
)

# Platform-specific configurations
if(WIN32)
    set_target_properties(AudioFingerprintingClient PROPERTIES
        WIN32_EXECUTABLE TRUE
    )
elseif(APPLE)
    set_target_properties(AudioFingerprintingClient PROPERTIES
        MACOSX_BUNDLE TRUE
        MACOSX_BUNDLE_INFO_PLIST ${CMAKE_CURRENT_SOURCE_DIR}/Info.plist.in
    )
endif()

# Install configuration
install(TARGETS AudioFingerprintingClient
    BUNDLE DESTINATION .
    RUNTIME DESTINATION bin
)

# Optional: Build tests if Qt6Test is available
find_package(Qt6 QUIET COMPONENTS Test)
if(Qt6Test_FOUND)
    enable_testing()
    
    qt_add_executable(test_apiclient
        src/test_apiclient.cpp
        src/apiclient.cpp
        src/apiclient.h
    )
    
    target_link_libraries(test_apiclient PRIVATE
        Qt6::Core
        Qt6::Network
        Qt6::Test
    )
    
    add_test(NAME ApiClientTest COMMAND test_apiclient)
endif()

# Optional: Build demo application
option(BUILD_DEMO "Build API client demo" OFF)
if(BUILD_DEMO)
    qt_add_executable(apiclient_demo
        src/apiclient_demo.cpp
        src/apiclient.cpp
        src/apiclient.h
    )
    
    target_link_libraries(apiclient_demo PRIVATE
        Qt6::Core
        Qt6::Network
    )
endif()

# CPack configuration for packaging
include(CPack)
set(CPACK_PACKAGE_NAME "Audio Fingerprinting Client")
set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Cross-platform audio fingerprinting client")

if(WIN32)
    set(CPACK_GENERATOR "NSIS")
elseif(APPLE)
    set(CPACK_GENERATOR "DragNDrop")
else()
    set(CPACK_GENERATOR "DEB;RPM")
endif()