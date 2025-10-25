#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include "audio_types.h"
#include "audio_preprocessor.h"
#include "fft_processor.h"
#include "peak_detector.h"
#include "hash_generator.h"

namespace py = pybind11;
using namespace AudioFingerprint;

/**
 * Convert numpy array to AudioSample
 */
AudioSample numpy_to_audio_sample(py::array_t<float> audio_data, int sample_rate, int channels) {
    py::buffer_info buf = audio_data.request();
    
    if (buf.ndim != 1) {
        throw std::runtime_error("Audio data must be 1-dimensional");
    }
    
    std::vector<float> data(static_cast<float*>(buf.ptr), 
                           static_cast<float*>(buf.ptr) + buf.size);
    
    return AudioSample(data, sample_rate, channels);
}

/**
 * Convert AudioSample to numpy array
 */
py::array_t<float> audio_sample_to_numpy(const AudioSample& sample) {
    return py::array_t<float>(
        sample.data.size(),
        sample.data.data(),
        py::cast(sample)  // Keep sample alive
    );
}

/**
 * High-level fingerprinting function for Python interface
 */
py::dict generate_fingerprint_from_audio(py::array_t<float> audio_data, 
                                        int sample_rate, 
                                        int channels = 1) {
    try {
        // Convert numpy array to AudioSample
        AudioSample sample = numpy_to_audio_sample(audio_data, sample_rate, channels);
        
        // Generate fingerprints
        HashGenerator generator;
        auto fingerprints = generator.process_audio_sample(sample);
        
        // Convert to Python-friendly format
        std::vector<uint32_t> hash_values;
        std::vector<int> time_offsets;
        std::vector<float> anchor_frequencies;
        std::vector<float> target_frequencies;
        std::vector<int> time_deltas;
        
        hash_values.reserve(fingerprints.size());
        time_offsets.reserve(fingerprints.size());
        anchor_frequencies.reserve(fingerprints.size());
        target_frequencies.reserve(fingerprints.size());
        time_deltas.reserve(fingerprints.size());
        
        for (const auto& fp : fingerprints) {
            hash_values.push_back(fp.hash_value);
            time_offsets.push_back(fp.time_offset_ms);
            anchor_frequencies.push_back(fp.anchor_freq_hz);
            target_frequencies.push_back(fp.target_freq_hz);
            time_deltas.push_back(fp.time_delta_ms);
        }
        
        py::dict result;
        result["hash_values"] = hash_values;
        result["time_offsets"] = time_offsets;
        result["anchor_frequencies"] = anchor_frequencies;
        result["target_frequencies"] = target_frequencies;
        result["time_deltas"] = time_deltas;
        result["count"] = fingerprints.size();
        
        return result;
        
    } catch (const std::exception& e) {
        throw std::runtime_error(std::string("Fingerprinting failed: ") + e.what());
    }
}

/**
 * Batch processing function for reference songs
 */
py::list batch_process_reference_songs(py::list audio_samples_list, py::list song_ids_list) {
    try {
        std::vector<AudioSample> audio_samples;
        std::vector<std::string> song_ids;
        
        // Convert Python lists to C++ vectors
        for (auto item : audio_samples_list) {
            py::dict sample_dict = item.cast<py::dict>();
            py::array_t<float> data = sample_dict["data"].cast<py::array_t<float>>();
            int sample_rate = sample_dict["sample_rate"].cast<int>();
            int channels = sample_dict["channels"].cast<int>();
            
            audio_samples.push_back(numpy_to_audio_sample(data, sample_rate, channels));
        }
        
        for (auto item : song_ids_list) {
            song_ids.push_back(item.cast<std::string>());
        }
        
        // Process batch
        HashGenerator generator;
        auto results = generator.batch_process_reference_songs(audio_samples, song_ids);
        
        // Convert results to Python format
        py::list py_results;
        for (const auto& result : results) {
            py::dict py_result;
            py_result["song_id"] = result.song_id;
            py_result["success"] = result.success;
            py_result["error_message"] = result.error_message;
            py_result["total_duration_ms"] = result.total_duration_ms;
            py_result["processing_time_ms"] = result.processing_time_ms;
            
            if (result.success) {
                std::vector<uint32_t> hash_values;
                std::vector<int> time_offsets;
                
                for (const auto& fp : result.fingerprints) {
                    hash_values.push_back(fp.hash_value);
                    time_offsets.push_back(fp.time_offset_ms);
                }
                
                py_result["hash_values"] = hash_values;
                py_result["time_offsets"] = time_offsets;
                py_result["fingerprint_count"] = result.fingerprints.size();
            }
            
            py_results.append(py_result);
        }
        
        return py_results;
        
    } catch (const std::exception& e) {
        throw std::runtime_error(std::string("Batch processing failed: ") + e.what());
    }
}

/**
 * Preprocess audio function
 */
py::dict preprocess_audio(py::array_t<float> audio_data, int sample_rate, int channels) {
    try {
        AudioSample sample = numpy_to_audio_sample(audio_data, sample_rate, channels);
        
        AudioPreprocessor preprocessor;
        auto processed = preprocessor.preprocess_for_fingerprinting(sample);
        
        py::dict result;
        result["data"] = audio_sample_to_numpy(processed);
        result["sample_rate"] = processed.sample_rate;
        result["channels"] = processed.channels;
        result["duration_ms"] = processed.duration_ms;
        
        return result;
        
    } catch (const std::exception& e) {
        throw std::runtime_error(std::string("Audio preprocessing failed: ") + e.what());
    }
}

/**
 * Compute spectrogram function
 */
py::dict compute_spectrogram(py::array_t<float> audio_data, int fft_size = 2048, int hop_size = 1024) {
    try {
        py::buffer_info buf = audio_data.request();
        std::vector<float> data(static_cast<float*>(buf.ptr), 
                               static_cast<float*>(buf.ptr) + buf.size);
        
        FFTProcessor fft_processor(fft_size);
        auto spectrogram = fft_processor.compute_stft(data, fft_size, hop_size);
        
        // Convert spectrogram to numpy array
        py::array_t<float> spec_array = py::array_t<float>(
            {spectrogram.time_frames, spectrogram.frequency_bins}
        );
        
        py::buffer_info spec_buf = spec_array.request();
        float* spec_ptr = static_cast<float*>(spec_buf.ptr);
        
        for (int t = 0; t < spectrogram.time_frames; ++t) {
            for (int f = 0; f < spectrogram.frequency_bins; ++f) {
                spec_ptr[t * spectrogram.frequency_bins + f] = spectrogram.data[t][f];
            }
        }
        
        py::dict result;
        result["data"] = spec_array;
        result["time_frames"] = spectrogram.time_frames;
        result["frequency_bins"] = spectrogram.frequency_bins;
        result["time_resolution"] = spectrogram.time_resolution;
        result["freq_resolution"] = spectrogram.freq_resolution;
        
        return result;
        
    } catch (const std::exception& e) {
        throw std::runtime_error(std::string("Spectrogram computation failed: ") + e.what());
    }
}

PYBIND11_MODULE(audio_fingerprint_engine, m) {
    m.doc() = "Audio fingerprinting engine for music identification";
    
    // Main fingerprinting function
    m.def("generate_fingerprint", &generate_fingerprint_from_audio,
          "Generate audio fingerprint from numpy array",
          py::arg("audio_data"), py::arg("sample_rate"), py::arg("channels") = 1);
    
    // Batch processing function
    m.def("batch_process_songs", &batch_process_reference_songs,
          "Batch process reference songs for database population",
          py::arg("audio_samples"), py::arg("song_ids"));
    
    // Preprocessing function
    m.def("preprocess_audio", &preprocess_audio,
          "Preprocess audio for fingerprinting",
          py::arg("audio_data"), py::arg("sample_rate"), py::arg("channels"));
    
    // Spectrogram computation
    m.def("compute_spectrogram", &compute_spectrogram,
          "Compute spectrogram from audio data",
          py::arg("audio_data"), py::arg("fft_size") = 2048, py::arg("hop_size") = 1024);
    
    // AudioSample class
    py::class_<AudioSample>(m, "AudioSample")
        .def(py::init<>())
        .def(py::init<const std::vector<float>&, int, int>())
        .def_readwrite("data", &AudioSample::data)
        .def_readwrite("sample_rate", &AudioSample::sample_rate)
        .def_readwrite("channels", &AudioSample::channels)
        .def_readwrite("duration_ms", &AudioSample::duration_ms)
        .def("size", &AudioSample::size)
        .def("empty", &AudioSample::empty);
    
    // Fingerprint class  
    py::class_<Fingerprint>(m, "AudioFingerprint")
        .def(py::init<>())
        .def(py::init<uint32_t, int, float, float, int>())
        .def_readwrite("hash_value", &Fingerprint::hash_value)
        .def_readwrite("time_offset_ms", &Fingerprint::time_offset_ms)
        .def_readwrite("anchor_freq_hz", &Fingerprint::anchor_freq_hz)
        .def_readwrite("target_freq_hz", &Fingerprint::target_freq_hz)
        .def_readwrite("time_delta_ms", &Fingerprint::time_delta_ms);
    
    // SpectralPeak class
    py::class_<SpectralPeak>(m, "SpectralPeak")
        .def(py::init<>())
        .def(py::init<int, int, float, float, float>())
        .def_readwrite("time_frame", &SpectralPeak::time_frame)
        .def_readwrite("frequency_bin", &SpectralPeak::frequency_bin)
        .def_readwrite("magnitude", &SpectralPeak::magnitude)
        .def_readwrite("frequency_hz", &SpectralPeak::frequency_hz)
        .def_readwrite("time_seconds", &SpectralPeak::time_seconds);
    
    // AudioPreprocessor class
    py::class_<AudioPreprocessor>(m, "AudioPreprocessor")
        .def(py::init<>())
        .def("stereo_to_mono", &AudioPreprocessor::stereo_to_mono)
        .def("resample_audio", &AudioPreprocessor::resample_audio)
        .def("normalize_audio", &AudioPreprocessor::normalize_audio)
        .def("preprocess_for_fingerprinting", &AudioPreprocessor::preprocess_for_fingerprinting);
    
    // FFTProcessor class
    py::class_<FFTProcessor>(m, "FFTProcessor")
        .def(py::init<int>(), py::arg("fft_size") = 2048)
        .def("frequency_to_bin", &FFTProcessor::frequency_to_bin)
        .def("bin_to_frequency", &FFTProcessor::bin_to_frequency);
    
    // PeakDetector class
    py::class_<PeakDetector>(m, "PeakDetector")
        .def(py::init<int, float, float>(), 
             py::arg("min_peak_distance") = 3,
             py::arg("adaptive_factor") = 0.7f,
             py::arg("min_magnitude_threshold") = 0.01f)
        .def("set_adaptive_factor", &PeakDetector::set_adaptive_factor)
        .def("set_min_peak_distance", &PeakDetector::set_min_peak_distance)
        .def("set_min_magnitude_threshold", &PeakDetector::set_min_magnitude_threshold);
    
    // HashGenerator class
    py::class_<HashGenerator>(m, "HashGenerator")
        .def(py::init<float, int>(), 
             py::arg("freq_quantization") = 10.0f,
             py::arg("time_quantization") = 50)
        .def("process_audio_sample", &HashGenerator::process_audio_sample)
        .def("serialize_fingerprints", &HashGenerator::serialize_fingerprints)
        .def("deserialize_fingerprints", &HashGenerator::deserialize_fingerprints)
        .def("set_frequency_quantization", &HashGenerator::set_frequency_quantization)
        .def("set_time_quantization", &HashGenerator::set_time_quantization)
        .def("get_fingerprint_statistics", &HashGenerator::get_fingerprint_statistics);
    
    // Version information
    m.attr("__version__") = "0.1.0";
}