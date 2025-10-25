#pragma once

#include "peak_detector.h"
#include <vector>
#include <cstdint>
#include <string>

namespace AudioFingerprint {

/**
 * Audio fingerprint structure
 */
struct Fingerprint {
    uint32_t hash_value;        // 32-bit hash of landmark pair
    int time_offset_ms;         // Time position in original audio (ms)
    float anchor_freq_hz;       // Anchor peak frequency
    float target_freq_hz;       // Target peak frequency
    int time_delta_ms;          // Time difference between peaks
    
    Fingerprint() : hash_value(0), time_offset_ms(0), 
                        anchor_freq_hz(0.0f), target_freq_hz(0.0f), time_delta_ms(0) {}
    
    Fingerprint(uint32_t hash, int offset, float anchor_freq, 
                    float target_freq, int delta)
        : hash_value(hash), time_offset_ms(offset), anchor_freq_hz(anchor_freq),
          target_freq_hz(target_freq), time_delta_ms(delta) {}
};

/**
 * Batch processing result for reference songs
 */
struct BatchProcessingResult {
    std::vector<Fingerprint> fingerprints;
    std::string song_id;
    int total_duration_ms;
    int processing_time_ms;
    bool success;
    std::string error_message;
    
    BatchProcessingResult() : total_duration_ms(0), processing_time_ms(0), success(false) {}
};

/**
 * Hash generator for creating audio fingerprints from landmark pairs
 */
class HashGenerator {
public:
    /**
     * Constructor
     * @param freq_quantization Frequency quantization factor (Hz per bin)
     * @param time_quantization Time quantization factor (ms per bin)
     */
    HashGenerator(float freq_quantization = 10.0f, int time_quantization = 50);
    
    ~HashGenerator() = default;
    
    /**
     * Generate fingerprints from landmark pairs
     * @param landmark_pairs Input landmark pairs
     * @return Vector of audio fingerprints
     */
    std::vector<Fingerprint> generate_fingerprints(
        const std::vector<LandmarkPair>& landmark_pairs);
    
    /**
     * Generate hash value from a landmark pair
     * @param pair Input landmark pair
     * @return 32-bit hash value
     */
    uint32_t generate_hash(const LandmarkPair& pair);
    
    /**
     * Process audio sample and generate complete fingerprint set
     * @param audio_sample Input audio sample
     * @return Vector of audio fingerprints
     */
    std::vector<Fingerprint> process_audio_sample(const AudioSample& audio_sample);
    
    /**
     * Batch process multiple audio files for reference database
     * @param audio_samples Vector of audio samples with metadata
     * @param song_ids Corresponding song identifiers
     * @return Batch processing results
     */
    std::vector<BatchProcessingResult> batch_process_reference_songs(
        const std::vector<AudioSample>& audio_samples,
        const std::vector<std::string>& song_ids);
    
    /**
     * Serialize fingerprints to binary format
     * @param fingerprints Input fingerprints
     * @return Serialized binary data
     */
    std::vector<uint8_t> serialize_fingerprints(const std::vector<Fingerprint>& fingerprints);
    
    /**
     * Deserialize fingerprints from binary format
     * @param data Serialized binary data
     * @return Deserialized fingerprints
     */
    std::vector<Fingerprint> deserialize_fingerprints(const std::vector<uint8_t>& data);
    
    /**
     * Set frequency quantization factor
     * @param quantization Frequency quantization in Hz per bin
     */
    void set_frequency_quantization(float quantization);
    
    /**
     * Set time quantization factor
     * @param quantization Time quantization in ms per bin
     */
    void set_time_quantization(int quantization);
    
    /**
     * Get statistics about generated fingerprints
     * @param fingerprints Input fingerprints
     * @return Statistics string
     */
    std::string get_fingerprint_statistics(const std::vector<Fingerprint>& fingerprints);

private:
    float freq_quantization_;
    int time_quantization_;
    
    /**
     * Quantize frequency to discrete bins
     * @param frequency Input frequency in Hz
     * @return Quantized frequency bin
     */
    uint16_t quantize_frequency(float frequency);
    
    /**
     * Quantize time to discrete bins
     * @param time_ms Input time in milliseconds
     * @return Quantized time bin
     */
    uint16_t quantize_time(int time_ms);
    
    /**
     * Combine quantized values into hash
     * @param anchor_freq Quantized anchor frequency
     * @param target_freq Quantized target frequency
     * @param time_delta Quantized time delta
     * @return 32-bit hash value
     */
    uint32_t combine_to_hash(uint16_t anchor_freq, uint16_t target_freq, uint16_t time_delta);
    
    /**
     * Simple hash function for combining values
     * @param a First value
     * @param b Second value
     * @param c Third value
     * @return Combined hash
     */
    uint32_t hash_function(uint32_t a, uint32_t b, uint32_t c);
};

} // namespace AudioFingerprint