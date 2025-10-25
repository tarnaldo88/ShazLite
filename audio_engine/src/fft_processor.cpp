#include "fft_processor.h"
#include "audio_preprocessor.h"
#include <stdexcept>
#include <cmath>
#include <algorithm>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace AudioFingerprint {

FFTProcessor::FFTProcessor(int fft_size) 
    : fft_size_(fft_size) {
    
    // Validate FFT size (should be power of 2)
    if (fft_size <= 0 || (fft_size & (fft_size - 1)) != 0) {
        throw std::invalid_argument("FFT size must be a positive power of 2");
    }
    
#ifndef NO_FFTW
    fft_plan_ = nullptr;
    input_buffer_ = nullptr;
    output_buffer_ = nullptr;
    initialize_fftw();
#else
    input_buffer_.resize(fft_size_);
    output_buffer_.resize(fft_size_ / 2 + 1);
#endif
}

FFTProcessor::~FFTProcessor() {
#ifndef NO_FFTW
    cleanup_fftw();
#endif
}

#ifndef NO_FFTW
void FFTProcessor::initialize_fftw() {
    // Allocate aligned memory for FFTW
    input_buffer_ = fftwf_alloc_real(fft_size_);
    output_buffer_ = fftwf_alloc_complex(fft_size_ / 2 + 1);
    
    if (!input_buffer_ || !output_buffer_) {
        cleanup_fftw();
        throw std::runtime_error("Failed to allocate FFTW buffers");
    }
    
    // Create FFTW plan for real-to-complex FFT
    fft_plan_ = fftwf_plan_dft_r2c_1d(fft_size_, input_buffer_, output_buffer_, FFTW_MEASURE);
    
    if (!fft_plan_) {
        cleanup_fftw();
        throw std::runtime_error("Failed to create FFTW plan");
    }
}

void FFTProcessor::cleanup_fftw() {
    if (fft_plan_) {
        fftwf_destroy_plan(fft_plan_);
        fft_plan_ = nullptr;
    }
    
    if (input_buffer_) {
        fftwf_free(input_buffer_);
        input_buffer_ = nullptr;
    }
    
    if (output_buffer_) {
        fftwf_free(output_buffer_);
        output_buffer_ = nullptr;
    }
}
#endif

Spectrogram FFTProcessor::compute_stft(const std::vector<float>& audio_data, 
                                      int window_size, int hop_size) {
    if (audio_data.empty()) {
        throw std::invalid_argument("Audio data is empty");
    }
    
    if (window_size > fft_size_) {
        throw std::invalid_argument("Window size cannot exceed FFT size");
    }
    
    if (hop_size <= 0 || hop_size > window_size) {
        throw std::invalid_argument("Invalid hop size");
    }
    
    AudioPreprocessor preprocessor;
    
    // Calculate number of frames
    int num_frames = static_cast<int>((audio_data.size() - window_size) / hop_size) + 1;
    int freq_bins = fft_size_ / 2 + 1;  // Number of positive frequency bins
    
    Spectrogram spectrogram;
    spectrogram.time_frames = num_frames;
    spectrogram.frequency_bins = freq_bins;
    spectrogram.time_resolution = static_cast<float>(hop_size) / 11025.0f;  // Assuming 11.025 kHz
    spectrogram.freq_resolution = 11025.0f / static_cast<float>(fft_size_);
    
    // Initialize spectrogram data
    spectrogram.data.resize(num_frames);
    for (int i = 0; i < num_frames; ++i) {
        spectrogram.data[i].resize(freq_bins);
    }
    
    // Process each frame
    for (int frame = 0; frame < num_frames; ++frame) {
        int start_idx = frame * hop_size;
        
        // Extract window of audio data
        std::vector<float> window_data(window_size);
        for (int i = 0; i < window_size; ++i) {
            if (start_idx + i < static_cast<int>(audio_data.size())) {
                window_data[i] = audio_data[start_idx + i];
            } else {
                window_data[i] = 0.0f;  // Zero padding
            }
        }
        
        // Apply Hann window
        auto windowed_data = preprocessor.apply_hann_window(window_data, window_size);
        
        // Compute FFT
        auto fft_result = compute_fft(windowed_data);
        
        // Convert to magnitude spectrum
        auto magnitude_spectrum = compute_magnitude_spectrum(fft_result);
        
        // Store in spectrogram
        for (int bin = 0; bin < freq_bins && bin < static_cast<int>(magnitude_spectrum.size()); ++bin) {
            spectrogram.data[frame][bin] = magnitude_spectrum[bin];
        }
    }
    
    return spectrogram;
}

std::vector<Complex> FFTProcessor::compute_fft(const std::vector<float>& windowed_data) {
    if (windowed_data.empty()) {
        throw std::invalid_argument("Windowed data is empty");
    }
    
#ifndef NO_FFTW
    // Clear input buffer
    std::fill(input_buffer_, input_buffer_ + fft_size_, 0.0f);
    
    // Copy windowed data to input buffer (with zero padding if necessary)
    int copy_size = std::min(static_cast<int>(windowed_data.size()), fft_size_);
    for (int i = 0; i < copy_size; ++i) {
        input_buffer_[i] = windowed_data[i];
    }
    
    // Execute FFT
    fftwf_execute(fft_plan_);
    
    // Convert FFTW output to Complex vector
    std::vector<Complex> result;
    int output_size = fft_size_ / 2 + 1;
    result.reserve(output_size);
    
    for (int i = 0; i < output_size; ++i) {
        result.emplace_back(output_buffer_[i][0], output_buffer_[i][1]);
    }
    
    return result;
#else
    // Simple DFT implementation for Windows (slower but works)
    return compute_dft(windowed_data);
#endif
}

#ifdef NO_FFTW
std::vector<Complex> FFTProcessor::compute_dft(const std::vector<float>& windowed_data) {
    int N = std::min(static_cast<int>(windowed_data.size()), fft_size_);
    int output_size = fft_size_ / 2 + 1;
    std::vector<Complex> result(output_size);
    
    // Compute DFT for positive frequencies only
    for (int k = 0; k < output_size; ++k) {
        float real_sum = 0.0f;
        float imag_sum = 0.0f;
        
        for (int n = 0; n < N; ++n) {
            float angle = -2.0f * M_PI * k * n / fft_size_;
            real_sum += windowed_data[n] * std::cos(angle);
            imag_sum += windowed_data[n] * std::sin(angle);
        }
        
        result[k] = Complex(real_sum, imag_sum);
    }
    
    return result;
}
#endif

std::vector<float> FFTProcessor::compute_magnitude_spectrum(const std::vector<Complex>& fft_result) {
    std::vector<float> magnitude_spectrum;
    magnitude_spectrum.reserve(fft_result.size());
    
    for (const auto& complex_val : fft_result) {
        magnitude_spectrum.push_back(complex_val.magnitude());
    }
    
    return magnitude_spectrum;
}

int FFTProcessor::frequency_to_bin(float frequency, int sample_rate) const {
    if (frequency < 0 || sample_rate <= 0) {
        return -1;
    }
    
    float bin_width = static_cast<float>(sample_rate) / static_cast<float>(fft_size_);
    int bin = static_cast<int>(std::round(frequency / bin_width));
    
    // Clamp to valid range
    return std::max(0, std::min(bin, fft_size_ / 2));
}

float FFTProcessor::bin_to_frequency(int bin, int sample_rate) const {
    if (bin < 0 || bin > fft_size_ / 2 || sample_rate <= 0) {
        return -1.0f;
    }
    
    float bin_width = static_cast<float>(sample_rate) / static_cast<float>(fft_size_);
    return static_cast<float>(bin) * bin_width;
}

} // namespace AudioFingerprint