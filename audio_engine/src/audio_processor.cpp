#include "audio_preprocessor.h"
#include "fft_processor.h"
#include <stdexcept>
#include <memory>

namespace AudioFingerprint {

/**
 * Main audio processor class that coordinates preprocessing and FFT operations
 */
class AudioProcessor {
public:
    AudioProcessor() 
        : preprocessor_(std::make_unique<AudioPreprocessor>()),
          fft_processor_(std::make_unique<FFTProcessor>(2048)) {
    }
    
    ~AudioProcessor() = default;
    
    /**
     * Process audio sample for fingerprinting
     * @param sample Input audio sample
     * @return Spectrogram ready for peak detection
     */
    Spectrogram process_audio_sample(const AudioSample& sample) {
        if (sample.empty()) {
            throw std::invalid_argument("Input audio sample is empty");
        }
        
        // Preprocess audio (convert to mono, resample, normalize)
        auto preprocessed = preprocessor_->preprocess_for_fingerprinting(sample);
        
        // Compute STFT with 50% overlap
        const int window_size = 2048;
        const int hop_size = window_size / 2;  // 50% overlap
        
        return fft_processor_->compute_stft(preprocessed.data, window_size, hop_size);
    }
    
    /**
     * Get FFT processor for direct access
     */
    FFTProcessor* get_fft_processor() {
        return fft_processor_.get();
    }
    
    /**
     * Get audio preprocessor for direct access
     */
    AudioPreprocessor* get_preprocessor() {
        return preprocessor_.get();
    }

private:
    std::unique_ptr<AudioPreprocessor> preprocessor_;
    std::unique_ptr<FFTProcessor> fft_processor_;
};

} // namespace AudioFingerprint