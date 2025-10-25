#pragma once

#include "audio_types.h"
#include <vector>

namespace AudioFingerprint {

/**
 * Spectral peak structure
 */
struct SpectralPeak {
    int time_frame;      // Time frame index
    int frequency_bin;   // Frequency bin index
    float magnitude;     // Peak magnitude
    float frequency_hz;  // Actual frequency in Hz
    float time_seconds;  // Actual time in seconds
    
    SpectralPeak() : time_frame(0), frequency_bin(0), magnitude(0.0f), 
                    frequency_hz(0.0f), time_seconds(0.0f) {}
    
    SpectralPeak(int t_frame, int f_bin, float mag, float freq, float time)
        : time_frame(t_frame), frequency_bin(f_bin), magnitude(mag), 
          frequency_hz(freq), time_seconds(time) {}
};

/**
 * Landmark pair structure for fingerprint generation
 */
struct LandmarkPair {
    SpectralPeak anchor;     // Anchor peak (earlier in time)
    SpectralPeak target;     // Target peak (later in time)
    int time_delta_ms;       // Time difference in milliseconds
    float freq_delta_hz;     // Frequency difference in Hz
    
    LandmarkPair() : time_delta_ms(0), freq_delta_hz(0.0f) {}
    
    LandmarkPair(const SpectralPeak& a, const SpectralPeak& t)
        : anchor(a), target(t) {
        time_delta_ms = static_cast<int>((target.time_seconds - anchor.time_seconds) * 1000.0f);
        freq_delta_hz = target.frequency_hz - anchor.frequency_hz;
    }
};

/**
 * Constellation map containing all detected peaks
 */
struct ConstellationMap {
    std::vector<SpectralPeak> peaks;
    int total_time_frames;
    int total_frequency_bins;
    float time_resolution;
    float freq_resolution;
    
    ConstellationMap() : total_time_frames(0), total_frequency_bins(0),
                        time_resolution(0.0f), freq_resolution(0.0f) {}
    
    void add_peak(const SpectralPeak& peak) {
        peaks.push_back(peak);
    }
    
    size_t size() const { return peaks.size(); }
    bool empty() const { return peaks.empty(); }
};

/**
 * Peak detector for spectral analysis
 */
class PeakDetector {
public:
    /**
     * Constructor with configurable parameters
     * @param min_peak_distance Minimum distance between peaks (bins)
     * @param adaptive_factor Factor for adaptive threshold (0.0-1.0)
     * @param min_magnitude_threshold Minimum absolute magnitude threshold
     */
    PeakDetector(int min_peak_distance = 3, 
                float adaptive_factor = 0.7f,
                float min_magnitude_threshold = 0.01f);
    
    ~PeakDetector() = default;
    
    /**
     * Detect spectral peaks in a spectrogram using adaptive thresholding
     * @param spectrogram Input spectrogram data
     * @return Constellation map with detected peaks
     */
    ConstellationMap detect_peaks(const Spectrogram& spectrogram);
    
    /**
     * Extract landmark pairs from constellation map
     * @param constellation Input constellation map
     * @param max_time_delta Maximum time difference for pairs (ms)
     * @param max_freq_delta Maximum frequency difference for pairs (Hz)
     * @return Vector of landmark pairs
     */
    std::vector<LandmarkPair> extract_landmark_pairs(
        const ConstellationMap& constellation,
        int max_time_delta = 2000,
        float max_freq_delta = 2000.0f);
    
    /**
     * Set adaptive threshold factor
     * @param factor Threshold factor (0.0-1.0)
     */
    void set_adaptive_factor(float factor);
    
    /**
     * Set minimum peak distance
     * @param distance Minimum distance in frequency bins
     */
    void set_min_peak_distance(int distance);
    
    /**
     * Set minimum magnitude threshold
     * @param threshold Minimum absolute magnitude
     */
    void set_min_magnitude_threshold(float threshold);

private:
    int min_peak_distance_;
    float adaptive_factor_;
    float min_magnitude_threshold_;
    
    /**
     * Check if a point is a local maximum in the spectrogram
     * @param spectrogram Input spectrogram
     * @param time_frame Time frame index
     * @param freq_bin Frequency bin index
     * @param neighborhood_size Size of neighborhood to check
     * @return True if point is local maximum
     */
    bool is_local_maximum(const Spectrogram& spectrogram, 
                         int time_frame, int freq_bin, 
                         int neighborhood_size = 3) const;
    
    /**
     * Calculate adaptive threshold for a region
     * @param spectrogram Input spectrogram
     * @param time_frame Center time frame
     * @param freq_bin Center frequency bin
     * @param region_size Size of region for threshold calculation
     * @return Adaptive threshold value
     */
    float calculate_adaptive_threshold(const Spectrogram& spectrogram,
                                     int time_frame, int freq_bin,
                                     int region_size = 10) const;
    
    /**
     * Filter peaks to remove those too close together
     * @param peaks Input peaks
     * @return Filtered peaks
     */
    std::vector<SpectralPeak> filter_nearby_peaks(const std::vector<SpectralPeak>& peaks) const;
    
    /**
     * Convert bin indices to actual frequency and time values
     * @param peak Peak with bin indices
     * @param spectrogram Source spectrogram for resolution info
     * @return Peak with actual frequency and time values
     */
    SpectralPeak convert_to_physical_units(const SpectralPeak& peak, 
                                          const Spectrogram& spectrogram) const;
};

} // namespace AudioFingerprint