#pragma once

#include "audio_types.h"
#include <vector>
#include <memory>

namespace AudioFingerprint {

/**
 * Audio preprocessing module for format conversion and resampling
 */
class AudioPreprocessor {
public:
    AudioPreprocessor();
    ~AudioPreprocessor();
    
    /**
     * Convert stereo audio to mono by averaging channels
     * @param stereo_data Input stereo audio data (interleaved L/R samples)
     * @param sample_count Number of stereo sample pairs
     * @return Mono audio data
     */
    std::vector<float> stereo_to_mono(const std::vector<float>& stereo_data);
    
    /**
     * Resample audio to target sample rate using linear interpolation
     * @param input_data Input audio samples
     * @param input_rate Original sample rate
     * @param target_rate Desired sample rate
     * @return Resampled audio data
     */
    std::vector<float> resample_audio(const std::vector<float>& input_data, 
                                     int input_rate, int target_rate);
    
    /**
     * Apply Hamming window to audio data
     * @param data Audio data to window
     * @param window_size Size of the window
     * @return Windowed audio data
     */
    std::vector<float> apply_hamming_window(const std::vector<float>& data, int window_size);
    
    /**
     * Apply Hann window to audio data
     * @param data Audio data to window
     * @param window_size Size of the window
     * @return Windowed audio data
     */
    std::vector<float> apply_hann_window(const std::vector<float>& data, int window_size);
    
    /**
     * Normalize audio data to [-1.0, 1.0] range
     * @param data Audio data to normalize
     * @return Normalized audio data
     */
    std::vector<float> normalize_audio(const std::vector<float>& data);
    
    /**
     * Preprocess raw audio for fingerprinting
     * Converts to mono, resamples to 11.025kHz, and normalizes
     * @param sample Input audio sample
     * @return Preprocessed audio ready for STFT
     */
    AudioSample preprocess_for_fingerprinting(const AudioSample& sample);

private:
    // Target sample rate for fingerprinting (11.025 kHz)
    static constexpr int TARGET_SAMPLE_RATE = 11025;
    
    /**
     * Generate Hamming window coefficients
     * @param size Window size
     * @return Window coefficients
     */
    std::vector<float> generate_hamming_window(int size);
    
    /**
     * Generate Hann window coefficients
     * @param size Window size
     * @return Window coefficients
     */
    std::vector<float> generate_hann_window(int size);
};

} // namespace AudioFingerprint