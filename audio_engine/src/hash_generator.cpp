#include "hash_generator.h"
#include "audio_preprocessor.h"
#include "fft_processor.h"
#include "peak_detector.h"
#include <stdexcept>
#include <algorithm>
#include <chrono>
#include <sstream>
#include <cstring>

namespace AudioFingerprint {

HashGenerator::HashGenerator(float freq_quantization, int time_quantization)
    : freq_quantization_(freq_quantization), time_quantization_(time_quantization) {
    
    if (freq_quantization <= 0.0f) {
        throw std::invalid_argument("Frequency quantization must be positive");
    }
    
    if (time_quantization <= 0) {
        throw std::invalid_argument("Time quantization must be positive");
    }
}

std::vector<Fingerprint> HashGenerator::generate_fingerprints(
    const std::vector<LandmarkPair>& landmark_pairs) {
    
    std::vector<Fingerprint> fingerprints;
    fingerprints.reserve(landmark_pairs.size());
    
    for (const auto& pair : landmark_pairs) {
        uint32_t hash_value = generate_hash(pair);
        int time_offset_ms = static_cast<int>(pair.anchor.time_seconds * 1000.0f);
        
        Fingerprint fingerprint(
            hash_value,
            time_offset_ms,
            pair.anchor.frequency_hz,
            pair.target.frequency_hz,
            pair.time_delta_ms
        );
        
        fingerprints.push_back(fingerprint);
    }
    
    return fingerprints;
}

uint32_t HashGenerator::generate_hash(const LandmarkPair& pair) {
    // Quantize frequencies and time delta
    uint16_t anchor_freq_bin = quantize_frequency(pair.anchor.frequency_hz);
    uint16_t target_freq_bin = quantize_frequency(pair.target.frequency_hz);
    uint16_t time_delta_bin = quantize_time(pair.time_delta_ms);
    
    // Combine into hash
    return combine_to_hash(anchor_freq_bin, target_freq_bin, time_delta_bin);
}

std::vector<Fingerprint> HashGenerator::process_audio_sample(const AudioSample& audio_sample) {
    if (audio_sample.empty()) {
        throw std::invalid_argument("Audio sample is empty");
    }
    
    // Create processing components
    AudioPreprocessor preprocessor;
    FFTProcessor fft_processor(2048);
    PeakDetector peak_detector;
    
    // Preprocess audio
    auto preprocessed = preprocessor.preprocess_for_fingerprinting(audio_sample);
    
    // Compute spectrogram
    auto spectrogram = fft_processor.compute_stft(preprocessed.data, 2048, 1024);
    
    // Detect peaks
    auto constellation = peak_detector.detect_peaks(spectrogram);
    
    // Extract landmark pairs
    auto landmark_pairs = peak_detector.extract_landmark_pairs(constellation, 2000, 2000.0f);
    
    // Generate fingerprints
    return generate_fingerprints(landmark_pairs);
}

std::vector<BatchProcessingResult> HashGenerator::batch_process_reference_songs(
    const std::vector<AudioSample>& audio_samples,
    const std::vector<std::string>& song_ids) {
    
    if (audio_samples.size() != song_ids.size()) {
        throw std::invalid_argument("Audio samples and song IDs must have same size");
    }
    
    std::vector<BatchProcessingResult> results;
    results.reserve(audio_samples.size());
    
    for (size_t i = 0; i < audio_samples.size(); ++i) {
        BatchProcessingResult result;
        result.song_id = song_ids[i];
        
        auto start_time = std::chrono::high_resolution_clock::now();
        
        try {
            // Process the audio sample
            result.fingerprints = process_audio_sample(audio_samples[i]);
            result.total_duration_ms = audio_samples[i].duration_ms;
            result.success = true;
            
        } catch (const std::exception& e) {
            result.success = false;
            result.error_message = e.what();
        }
        
        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
        result.processing_time_ms = static_cast<int>(duration.count());
        
        results.push_back(result);
    }
    
    return results;
}

std::vector<uint8_t> HashGenerator::serialize_fingerprints(const std::vector<Fingerprint>& fingerprints) {
    std::vector<uint8_t> data;
    
    // Calculate total size needed
    size_t header_size = sizeof(uint32_t);  // Number of fingerprints
    size_t fingerprint_size = sizeof(uint32_t) + sizeof(int32_t) + 3 * sizeof(float);
    size_t total_size = header_size + fingerprints.size() * fingerprint_size;
    
    data.reserve(total_size);
    
    // Write number of fingerprints
    uint32_t count = static_cast<uint32_t>(fingerprints.size());
    const uint8_t* count_bytes = reinterpret_cast<const uint8_t*>(&count);
    data.insert(data.end(), count_bytes, count_bytes + sizeof(uint32_t));
    
    // Write each fingerprint
    for (const auto& fp : fingerprints) {
        // Hash value
        const uint8_t* hash_bytes = reinterpret_cast<const uint8_t*>(&fp.hash_value);
        data.insert(data.end(), hash_bytes, hash_bytes + sizeof(uint32_t));
        
        // Time offset
        const uint8_t* time_bytes = reinterpret_cast<const uint8_t*>(&fp.time_offset_ms);
        data.insert(data.end(), time_bytes, time_bytes + sizeof(int32_t));
        
        // Anchor frequency
        const uint8_t* anchor_bytes = reinterpret_cast<const uint8_t*>(&fp.anchor_freq_hz);
        data.insert(data.end(), anchor_bytes, anchor_bytes + sizeof(float));
        
        // Target frequency
        const uint8_t* target_bytes = reinterpret_cast<const uint8_t*>(&fp.target_freq_hz);
        data.insert(data.end(), target_bytes, target_bytes + sizeof(float));
        
        // Time delta
        const uint8_t* delta_bytes = reinterpret_cast<const uint8_t*>(&fp.time_delta_ms);
        data.insert(data.end(), delta_bytes, delta_bytes + sizeof(int32_t));
    }
    
    return data;
}

std::vector<Fingerprint> HashGenerator::deserialize_fingerprints(const std::vector<uint8_t>& data) {
    if (data.size() < sizeof(uint32_t)) {
        throw std::invalid_argument("Data too small to contain fingerprint count");
    }
    
    std::vector<Fingerprint> fingerprints;
    
    // Read number of fingerprints
    uint32_t count;
    std::memcpy(&count, data.data(), sizeof(uint32_t));
    
    fingerprints.reserve(count);
    
    size_t offset = sizeof(uint32_t);
    size_t fingerprint_size = sizeof(uint32_t) + sizeof(int32_t) + 3 * sizeof(float);
    
    for (uint32_t i = 0; i < count; ++i) {
        if (offset + fingerprint_size > data.size()) {
            throw std::invalid_argument("Data truncated while reading fingerprints");
        }
        
        Fingerprint fp;
        
        // Read hash value
        std::memcpy(&fp.hash_value, data.data() + offset, sizeof(uint32_t));
        offset += sizeof(uint32_t);
        
        // Read time offset
        std::memcpy(&fp.time_offset_ms, data.data() + offset, sizeof(int32_t));
        offset += sizeof(int32_t);
        
        // Read anchor frequency
        std::memcpy(&fp.anchor_freq_hz, data.data() + offset, sizeof(float));
        offset += sizeof(float);
        
        // Read target frequency
        std::memcpy(&fp.target_freq_hz, data.data() + offset, sizeof(float));
        offset += sizeof(float);
        
        // Read time delta
        std::memcpy(&fp.time_delta_ms, data.data() + offset, sizeof(int32_t));
        offset += sizeof(int32_t);
        
        fingerprints.push_back(fp);
    }
    
    return fingerprints;
}

uint16_t HashGenerator::quantize_frequency(float frequency) {
    if (frequency < 0.0f) {
        return 0;
    }
    
    uint16_t bin = static_cast<uint16_t>(frequency / freq_quantization_);
    return std::min(bin, static_cast<uint16_t>(65535));  // Clamp to 16-bit range
}

uint16_t HashGenerator::quantize_time(int time_ms) {
    if (time_ms < 0) {
        return 0;
    }
    
    uint16_t bin = static_cast<uint16_t>(time_ms / time_quantization_);
    return std::min(bin, static_cast<uint16_t>(65535));  // Clamp to 16-bit range
}

uint32_t HashGenerator::combine_to_hash(uint16_t anchor_freq, uint16_t target_freq, uint16_t time_delta) {
    // Use a simple but effective hash combination
    return hash_function(
        static_cast<uint32_t>(anchor_freq),
        static_cast<uint32_t>(target_freq),
        static_cast<uint32_t>(time_delta)
    );
}

uint32_t HashGenerator::hash_function(uint32_t a, uint32_t b, uint32_t c) {
    // Jenkins hash-like function for combining three values
    a = (a + 0x7ed55d16) + (a << 12);
    a = (a ^ 0xc761c23c) ^ (a >> 19);
    a = (a + 0x165667b1) + (a << 5);
    a = (a + 0xd3a2646c) ^ (a << 9);
    a = (a + 0xfd7046c5) + (a << 3);
    a = (a ^ 0xb55a4f09) ^ (a >> 16);
    
    b = (b + 0x7ed55d16) + (b << 12);
    b = (b ^ 0xc761c23c) ^ (b >> 19);
    b = (b + 0x165667b1) + (b << 5);
    b = (b + 0xd3a2646c) ^ (b << 9);
    b = (b + 0xfd7046c5) + (b << 3);
    b = (b ^ 0xb55a4f09) ^ (b >> 16);
    
    c = (c + 0x7ed55d16) + (c << 12);
    c = (c ^ 0xc761c23c) ^ (c >> 19);
    c = (c + 0x165667b1) + (c << 5);
    c = (c + 0xd3a2646c) ^ (c << 9);
    c = (c + 0xfd7046c5) + (c << 3);
    c = (c ^ 0xb55a4f09) ^ (c >> 16);
    
    return a ^ b ^ c;
}

void HashGenerator::set_frequency_quantization(float quantization) {
    if (quantization <= 0.0f) {
        throw std::invalid_argument("Frequency quantization must be positive");
    }
    freq_quantization_ = quantization;
}

void HashGenerator::set_time_quantization(int quantization) {
    if (quantization <= 0) {
        throw std::invalid_argument("Time quantization must be positive");
    }
    time_quantization_ = quantization;
}

std::string HashGenerator::get_fingerprint_statistics(const std::vector<Fingerprint>& fingerprints) {
    if (fingerprints.empty()) {
        return "No fingerprints to analyze";
    }
    
    std::ostringstream stats;
    stats << "Fingerprint Statistics:\n";
    stats << "  Total fingerprints: " << fingerprints.size() << "\n";
    
    // Calculate time span
    int min_time = fingerprints[0].time_offset_ms;
    int max_time = fingerprints[0].time_offset_ms;
    
    // Calculate frequency range
    float min_freq = fingerprints[0].anchor_freq_hz;
    float max_freq = fingerprints[0].anchor_freq_hz;
    
    for (const auto& fp : fingerprints) {
        min_time = std::min(min_time, fp.time_offset_ms);
        max_time = std::max(max_time, fp.time_offset_ms);
        
        min_freq = std::min(min_freq, std::min(fp.anchor_freq_hz, fp.target_freq_hz));
        max_freq = std::max(max_freq, std::max(fp.anchor_freq_hz, fp.target_freq_hz));
    }
    
    stats << "  Time span: " << min_time << " - " << max_time << " ms\n";
    stats << "  Frequency range: " << min_freq << " - " << max_freq << " Hz\n";
    stats << "  Density: " << static_cast<float>(fingerprints.size()) / (max_time - min_time) * 1000.0f 
          << " fingerprints/second\n";
    
    return stats.str();
}

} // namespace AudioFingerprint