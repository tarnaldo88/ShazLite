#include "audio_preprocessor.h"
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace AudioFingerprint {

AudioPreprocessor::AudioPreprocessor() {
    // Constructor - no initialization needed
}

AudioPreprocessor::~AudioPreprocessor() {
    // Destructor - no cleanup needed
}

std::vector<float> AudioPreprocessor::stereo_to_mono(const std::vector<float>& stereo_data) {
    if (stereo_data.size() % 2 != 0) {
        throw std::invalid_argument("Stereo data size must be even");
    }
    
    std::vector<float> mono_data;
    mono_data.reserve(stereo_data.size() / 2);
    
    // Average left and right channels
    for (size_t i = 0; i < stereo_data.size(); i += 2) {
        float left = stereo_data[i];
        float right = stereo_data[i + 1];
        mono_data.push_back((left + right) * 0.5f);
    }
    
    return mono_data;
}

std::vector<float> AudioPreprocessor::resample_audio(const std::vector<float>& input_data, 
                                                   int input_rate, int target_rate) {
    if (input_rate <= 0 || target_rate <= 0) {
        throw std::invalid_argument("Sample rates must be positive");
    }
    
    if (input_data.empty()) {
        return std::vector<float>();
    }
    
    // If rates are the same, return copy
    if (input_rate == target_rate) {
        return input_data;
    }
    
    // Calculate resampling ratio
    double ratio = static_cast<double>(target_rate) / static_cast<double>(input_rate);
    size_t output_size = static_cast<size_t>(input_data.size() * ratio);
    
    std::vector<float> output_data;
    output_data.reserve(output_size);
    
    // Linear interpolation resampling
    for (size_t i = 0; i < output_size; ++i) {
        double src_index = static_cast<double>(i) / ratio;
        size_t index1 = static_cast<size_t>(std::floor(src_index));
        size_t index2 = std::min(index1 + 1, input_data.size() - 1);
        
        if (index1 >= input_data.size()) {
            break;
        }
        
        // Linear interpolation
        double fraction = src_index - static_cast<double>(index1);
        float sample1 = input_data[index1];
        float sample2 = input_data[index2];
        float interpolated = sample1 + static_cast<float>(fraction) * (sample2 - sample1);
        
        output_data.push_back(interpolated);
    }
    
    return output_data;
}

std::vector<float> AudioPreprocessor::generate_hamming_window(int size) {
    std::vector<float> window(size);
    
    for (int i = 0; i < size; ++i) {
        window[i] = 0.54f - 0.46f * std::cos(2.0f * M_PI * i / (size - 1));
    }
    
    return window;
}

std::vector<float> AudioPreprocessor::generate_hann_window(int size) {
    std::vector<float> window(size);
    
    for (int i = 0; i < size; ++i) {
        window[i] = 0.5f * (1.0f - std::cos(2.0f * M_PI * i / (size - 1)));
    }
    
    return window;
}

std::vector<float> AudioPreprocessor::apply_hamming_window(const std::vector<float>& data, int window_size) {
    if (static_cast<int>(data.size()) != window_size) {
        throw std::invalid_argument("Data size must match window size");
    }
    
    auto window = generate_hamming_window(window_size);
    std::vector<float> windowed_data(window_size);
    
    for (int i = 0; i < window_size; ++i) {
        windowed_data[i] = data[i] * window[i];
    }
    
    return windowed_data;
}

std::vector<float> AudioPreprocessor::apply_hann_window(const std::vector<float>& data, int window_size) {
    if (static_cast<int>(data.size()) != window_size) {
        throw std::invalid_argument("Data size must match window size");
    }
    
    auto window = generate_hann_window(window_size);
    std::vector<float> windowed_data(window_size);
    
    for (int i = 0; i < window_size; ++i) {
        windowed_data[i] = data[i] * window[i];
    }
    
    return windowed_data;
}

std::vector<float> AudioPreprocessor::normalize_audio(const std::vector<float>& data) {
    if (data.empty()) {
        return std::vector<float>();
    }
    
    // Find maximum absolute value
    float max_abs = 0.0f;
    for (float sample : data) {
        max_abs = std::max(max_abs, std::abs(sample));
    }
    
    // Avoid division by zero
    if (max_abs < 1e-10f) {
        return data;  // Return original if all samples are near zero
    }
    
    // Normalize to [-1.0, 1.0] range
    std::vector<float> normalized_data;
    normalized_data.reserve(data.size());
    
    float scale = 1.0f / max_abs;
    for (float sample : data) {
        normalized_data.push_back(sample * scale);
    }
    
    return normalized_data;
}

AudioSample AudioPreprocessor::preprocess_for_fingerprinting(const AudioSample& sample) {
    if (sample.empty()) {
        throw std::invalid_argument("Input audio sample is empty");
    }
    
    std::vector<float> processed_data = sample.data;
    int current_sample_rate = sample.sample_rate;
    int current_channels = sample.channels;
    
    // Convert stereo to mono if necessary
    if (current_channels == 2) {
        processed_data = stereo_to_mono(processed_data);
        current_channels = 1;
    } else if (current_channels > 2) {
        throw std::invalid_argument("Only mono and stereo audio are supported");
    }
    
    // Resample to target rate (11.025 kHz) if necessary
    if (current_sample_rate != TARGET_SAMPLE_RATE) {
        processed_data = resample_audio(processed_data, current_sample_rate, TARGET_SAMPLE_RATE);
        current_sample_rate = TARGET_SAMPLE_RATE;
    }
    
    // Normalize audio
    processed_data = normalize_audio(processed_data);
    
    // Create and return preprocessed sample
    return AudioSample(processed_data, current_sample_rate, 1);
}

} // namespace AudioFingerprint