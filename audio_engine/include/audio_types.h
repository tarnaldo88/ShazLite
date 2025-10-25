#pragma once

#include <vector>
#include <cstdint>
#include <memory>

namespace AudioFingerprint {

/**
 * Audio sample data structure
 */
struct AudioSample {
    std::vector<float> data;
    int sample_rate;
    int channels;
    int duration_ms;
    
    AudioSample() : sample_rate(0), channels(0), duration_ms(0) {}
    
    AudioSample(const std::vector<float>& audio_data, int sr, int ch) 
        : data(audio_data), sample_rate(sr), channels(ch) {
        duration_ms = static_cast<int>((data.size() * 1000.0) / (sample_rate * channels));
    }
    
    size_t size() const { return data.size(); }
    bool empty() const { return data.empty(); }
};

/**
 * Complex number for FFT operations
 */
struct Complex {
    float real;
    float imag;
    
    Complex() : real(0.0f), imag(0.0f) {}
    Complex(float r, float i) : real(r), imag(i) {}
    
    float magnitude() const {
        return std::sqrt(real * real + imag * imag);
    }
    
    float phase() const {
        return std::atan2(imag, real);
    }
};

/**
 * Spectrogram data structure
 */
struct Spectrogram {
    std::vector<std::vector<float>> data;  // [time][frequency]
    int time_frames;
    int frequency_bins;
    float time_resolution;  // seconds per frame
    float freq_resolution;  // Hz per bin
    
    Spectrogram() : time_frames(0), frequency_bins(0), time_resolution(0.0f), freq_resolution(0.0f) {}
    
    float& operator()(int time, int freq) {
        return data[time][freq];
    }
    
    const float& operator()(int time, int freq) const {
        return data[time][freq];
    }
};

} // namespace AudioFingerprint