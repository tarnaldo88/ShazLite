#include "peak_detector.h"
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace AudioFingerprint {

PeakDetector::PeakDetector(int min_peak_distance, float adaptive_factor, float min_magnitude_threshold)
    : min_peak_distance_(min_peak_distance), 
      adaptive_factor_(adaptive_factor),
      min_magnitude_threshold_(min_magnitude_threshold) {
    
    if (min_peak_distance <= 0) {
        throw std::invalid_argument("Minimum peak distance must be positive");
    }
    
    if (adaptive_factor < 0.0f || adaptive_factor > 1.0f) {
        throw std::invalid_argument("Adaptive factor must be between 0.0 and 1.0");
    }
    
    if (min_magnitude_threshold < 0.0f) {
        throw std::invalid_argument("Minimum magnitude threshold must be non-negative");
    }
}

ConstellationMap PeakDetector::detect_peaks(const Spectrogram& spectrogram) {
    if (spectrogram.data.empty()) {
        throw std::invalid_argument("Spectrogram is empty");
    }
    
    ConstellationMap constellation;
    constellation.total_time_frames = spectrogram.time_frames;
    constellation.total_frequency_bins = spectrogram.frequency_bins;
    constellation.time_resolution = spectrogram.time_resolution;
    constellation.freq_resolution = spectrogram.freq_resolution;
    
    std::vector<SpectralPeak> candidate_peaks;
    
    // Scan through spectrogram to find local maxima
    for (int t = 1; t < spectrogram.time_frames - 1; ++t) {
        for (int f = 1; f < spectrogram.frequency_bins - 1; ++f) {
            float magnitude = spectrogram.data[t][f];
            
            // Skip if below minimum threshold
            if (magnitude < min_magnitude_threshold_) {
                continue;
            }
            
            // Check if it's a local maximum
            if (is_local_maximum(spectrogram, t, f)) {
                // Calculate adaptive threshold for this region
                float adaptive_threshold = calculate_adaptive_threshold(spectrogram, t, f);
                
                // Check if magnitude exceeds adaptive threshold
                if (magnitude >= adaptive_threshold) {
                    SpectralPeak peak(t, f, magnitude, 0.0f, 0.0f);
                    peak = convert_to_physical_units(peak, spectrogram);
                    candidate_peaks.push_back(peak);
                }
            }
        }
    }
    
    // Filter peaks that are too close together
    auto filtered_peaks = filter_nearby_peaks(candidate_peaks);
    
    // Add filtered peaks to constellation
    for (const auto& peak : filtered_peaks) {
        constellation.add_peak(peak);
    }
    
    return constellation;
}

bool PeakDetector::is_local_maximum(const Spectrogram& spectrogram, 
                                   int time_frame, int freq_bin, 
                                   int neighborhood_size) const {
    float center_value = spectrogram.data[time_frame][freq_bin];
    
    // Check neighborhood around the point
    int half_size = neighborhood_size / 2;
    
    for (int dt = -half_size; dt <= half_size; ++dt) {
        for (int df = -half_size; df <= half_size; ++df) {
            // Skip center point
            if (dt == 0 && df == 0) continue;
            
            int t = time_frame + dt;
            int f = freq_bin + df;
            
            // Check bounds
            if (t < 0 || t >= spectrogram.time_frames || 
                f < 0 || f >= spectrogram.frequency_bins) {
                continue;
            }
            
            // If any neighbor is greater or equal, not a local maximum
            if (spectrogram.data[t][f] >= center_value) {
                return false;
            }
        }
    }
    
    return true;
}

float PeakDetector::calculate_adaptive_threshold(const Spectrogram& spectrogram,
                                               int time_frame, int freq_bin,
                                               int region_size) const {
    int half_size = region_size / 2;
    float sum = 0.0f;
    int count = 0;
    
    // Calculate mean magnitude in the region
    for (int dt = -half_size; dt <= half_size; ++dt) {
        for (int df = -half_size; df <= half_size; ++df) {
            int t = time_frame + dt;
            int f = freq_bin + df;
            
            // Check bounds
            if (t >= 0 && t < spectrogram.time_frames && 
                f >= 0 && f < spectrogram.frequency_bins) {
                sum += spectrogram.data[t][f];
                count++;
            }
        }
    }
    
    if (count == 0) {
        return min_magnitude_threshold_;
    }
    
    float mean_magnitude = sum / static_cast<float>(count);
    
    // Adaptive threshold is a factor of the local mean
    float adaptive_threshold = mean_magnitude * (1.0f + adaptive_factor_);
    
    // Ensure it's at least the minimum threshold
    return std::max(adaptive_threshold, min_magnitude_threshold_);
}

std::vector<SpectralPeak> PeakDetector::filter_nearby_peaks(const std::vector<SpectralPeak>& peaks) const {
    if (peaks.empty()) {
        return std::vector<SpectralPeak>();
    }
    
    // Sort peaks by magnitude (descending)
    std::vector<SpectralPeak> sorted_peaks = peaks;
    std::sort(sorted_peaks.begin(), sorted_peaks.end(), 
              [](const SpectralPeak& a, const SpectralPeak& b) {
                  return a.magnitude > b.magnitude;
              });
    
    std::vector<SpectralPeak> filtered_peaks;
    
    for (const auto& peak : sorted_peaks) {
        bool too_close = false;
        
        // Check if this peak is too close to any already selected peak
        for (const auto& selected_peak : filtered_peaks) {
            int time_diff = std::abs(peak.time_frame - selected_peak.time_frame);
            int freq_diff = std::abs(peak.frequency_bin - selected_peak.frequency_bin);
            
            // Use Euclidean distance in time-frequency space
            float distance = std::sqrt(static_cast<float>(time_diff * time_diff + freq_diff * freq_diff));
            
            if (distance < static_cast<float>(min_peak_distance_)) {
                too_close = true;
                break;
            }
        }
        
        if (!too_close) {
            filtered_peaks.push_back(peak);
        }
    }
    
    return filtered_peaks;
}

SpectralPeak PeakDetector::convert_to_physical_units(const SpectralPeak& peak, 
                                                   const Spectrogram& spectrogram) const {
    SpectralPeak converted_peak = peak;
    
    // Convert time frame to seconds
    converted_peak.time_seconds = static_cast<float>(peak.time_frame) * spectrogram.time_resolution;
    
    // Convert frequency bin to Hz
    converted_peak.frequency_hz = static_cast<float>(peak.frequency_bin) * spectrogram.freq_resolution;
    
    return converted_peak;
}

std::vector<LandmarkPair> PeakDetector::extract_landmark_pairs(
    const ConstellationMap& constellation,
    int max_time_delta, 
    float max_freq_delta) {
    
    if (constellation.empty()) {
        return std::vector<LandmarkPair>();
    }
    
    std::vector<LandmarkPair> landmark_pairs;
    
    // Sort peaks by time for efficient pairing
    std::vector<SpectralPeak> sorted_peaks = constellation.peaks;
    std::sort(sorted_peaks.begin(), sorted_peaks.end(),
              [](const SpectralPeak& a, const SpectralPeak& b) {
                  return a.time_seconds < b.time_seconds;
              });
    
    // Generate pairs from each anchor peak
    for (size_t i = 0; i < sorted_peaks.size(); ++i) {
        const SpectralPeak& anchor = sorted_peaks[i];
        
        // Look for target peaks within time and frequency constraints
        for (size_t j = i + 1; j < sorted_peaks.size(); ++j) {
            const SpectralPeak& target = sorted_peaks[j];
            
            // Check time constraint
            float time_diff_ms = (target.time_seconds - anchor.time_seconds) * 1000.0f;
            if (time_diff_ms > static_cast<float>(max_time_delta)) {
                break;  // No more valid targets (sorted by time)
            }
            
            // Check frequency constraint
            float freq_diff = std::abs(target.frequency_hz - anchor.frequency_hz);
            if (freq_diff <= max_freq_delta) {
                landmark_pairs.emplace_back(anchor, target);
            }
        }
    }
    
    return landmark_pairs;
}

void PeakDetector::set_adaptive_factor(float factor) {
    if (factor < 0.0f || factor > 1.0f) {
        throw std::invalid_argument("Adaptive factor must be between 0.0 and 1.0");
    }
    adaptive_factor_ = factor;
}

void PeakDetector::set_min_peak_distance(int distance) {
    if (distance <= 0) {
        throw std::invalid_argument("Minimum peak distance must be positive");
    }
    min_peak_distance_ = distance;
}

void PeakDetector::set_min_magnitude_threshold(float threshold) {
    if (threshold < 0.0f) {
        throw std::invalid_argument("Minimum magnitude threshold must be non-negative");
    }
    min_magnitude_threshold_ = threshold;
}

} // namespace AudioFingerprint