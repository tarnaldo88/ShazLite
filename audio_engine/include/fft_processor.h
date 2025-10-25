#pragma once

#include "audio_types.h"
#include <memory>

#ifndef NO_FFTW
#include <fftw3.h>
#endif

namespace AudioFingerprint {

/**
 * FFT processor using FFTW3 library for spectral analysis
 */
class FFTProcessor {
public:
    /**
     * Constructor
     * @param fft_size Size of FFT window (must be power of 2)
     */
    explicit FFTProcessor(int fft_size = 2048);
    
    /**
     * Destructor - cleans up FFTW plans and memory
     */
    ~FFTProcessor();
    
    // Disable copy constructor and assignment
    FFTProcessor(const FFTProcessor&) = delete;
    FFTProcessor& operator=(const FFTProcessor&) = delete;
    
    /**
     * Compute Short-Time Fourier Transform (STFT)
     * @param audio_data Input audio samples
     * @param window_size Size of each FFT window
     * @param hop_size Number of samples between windows (overlap = window_size - hop_size)
     * @return Spectrogram containing magnitude values
     */
    Spectrogram compute_stft(const std::vector<float>& audio_data, 
                            int window_size = 2048, 
                            int hop_size = 1024);
    
    /**
     * Compute single FFT of windowed audio data
     * @param windowed_data Input audio data (should be windowed)
     * @return Complex FFT result
     */
    std::vector<Complex> compute_fft(const std::vector<float>& windowed_data);
    
    /**
     * Convert complex FFT result to magnitude spectrum
     * @param fft_result Complex FFT output
     * @return Magnitude spectrum
     */
    std::vector<float> compute_magnitude_spectrum(const std::vector<Complex>& fft_result);
    
    /**
     * Get frequency bin for given frequency
     * @param frequency Frequency in Hz
     * @param sample_rate Sample rate in Hz
     * @return Frequency bin index
     */
    int frequency_to_bin(float frequency, int sample_rate) const;
    
    /**
     * Get frequency for given bin
     * @param bin Frequency bin index
     * @param sample_rate Sample rate in Hz
     * @return Frequency in Hz
     */
    float bin_to_frequency(int bin, int sample_rate) const;

private:
    int fft_size_;
    
#ifndef NO_FFTW
    fftwf_plan fft_plan_;
    float* input_buffer_;
    fftwf_complex* output_buffer_;
    
    /**
     * Initialize FFTW plan and buffers
     */
    void initialize_fftw();
    
    /**
     * Cleanup FFTW resources
     */
    void cleanup_fftw();
#else
    std::vector<float> input_buffer_;
    std::vector<Complex> output_buffer_;
    
    /**
     * Simple DFT implementation when FFTW is not available
     */
    std::vector<Complex> compute_dft(const std::vector<float>& windowed_data);
#endif
};

} // namespace AudioFingerprint