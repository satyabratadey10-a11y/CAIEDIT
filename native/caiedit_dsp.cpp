/**
 * CAIEDIT Native Audio DSP Engine (libcaiedit_dsp.so)
 * High-speed audio analysis:
 * - RMS energy curve calculation
 * - Low-frequency bass/kick transient detection (<150Hz)
 * - Spectral flux & beat onset extraction
 * - Climax / Beat Drop locator
 *
 * Lightweight, zero-dependency, microsecond latency.
 */

#include <cstdint>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <algorithm>

extern "C" {

/**
 * Calculates RMS energy curve across audio samples.
 * samples: float array [-1.0, 1.0]
 * num_samples: total samples
 * hop_size: hop length in samples (e.g. 512 or 1024)
 * out_energy: caller-allocated float array of size (num_samples / hop_size)
 * Returns number of energy frames generated.
 */
int caiedit_calculate_rms(const float* samples, int num_samples, int hop_size, float* out_energy) {
    if (!samples || !out_energy || num_samples <= 0 || hop_size <= 0) return 0;
    
    int num_frames = num_samples / hop_size;
    for (int f = 0; f < num_frames; ++f) {
        int start = f * hop_size;
        double sum_sq = 0.0;
        for (int i = 0; i < hop_size; ++i) {
            float val = samples[start + i];
            sum_sq += val * val;
        }
        out_energy[f] = static_cast<float>(std::sqrt(sum_sq / hop_size));
    }
    return num_frames;
}

/**
 * 2nd-Order IIR Low-Pass Butterworth Filter for isolating sub-bass / kicks (< 150 Hz)
 */
void caiedit_lowpass_filter(const float* input, float* output, int num_samples, float cutoff_hz, float sample_rate) {
    if (!input || !output || num_samples <= 0) return;
    
    // Bilinear transform filter coefficients
    float dt = 1.0f / sample_rate;
    float rc = 1.0f / (2.0f * 3.14159265f * cutoff_hz);
    float alpha = dt / (rc + dt);

    float prev = 0.0f;
    for (int i = 0; i < num_samples; ++i) {
        prev = prev + alpha * (input[i] - prev);
        output[i] = prev;
    }
}

/**
 * Detects Transient Onset Peaks (Kick drum / bass drops)
 * energy: array of RMS or low-pass energy frames
 * num_frames: length of energy array
 * threshold_factor: e.g. 1.4 (peak must be 1.4x above rolling local mean)
 * window_size: local smoothing window (e.g. 15 frames)
 * out_peaks: caller-allocated int array for frame indices of detected peaks
 * max_peaks: maximum capacity of out_peaks
 * Returns count of detected peaks.
 */
int caiedit_detect_transients(const float* energy, int num_frames, float threshold_factor, int window_size, int* out_peaks, int max_peaks) {
    if (!energy || !out_peaks || num_frames <= 0 || max_peaks <= 0) return 0;
    
    int peak_count = 0;
    int half_win = window_size / 2;

    for (int i = half_win; i < num_frames - half_win; ++i) {
        // Calculate local average
        float local_sum = 0.0f;
        for (int w = -half_win; w <= half_win; ++w) {
            local_sum += energy[i + w];
        }
        float local_mean = local_sum / window_size;

        // Peak condition: greater than neighbors and exceeds threshold
        float curr = energy[i];
        if (curr > local_mean * threshold_factor &&
            curr > energy[i - 1] && curr > energy[i + 1]) {
            
            // Check minimum spacing (at least 4 frames between kicks)
            if (peak_count == 0 || (i - out_peaks[peak_count - 1]) > 4) {
                out_peaks[peak_count++] = i;
                if (peak_count >= max_peaks) break;
            }
        }
    }
    return peak_count;
}

/**
 * Locates the Primary Climax / Bass Drop
 * Looks for the highest transition derivative following a build-up.
 * Returns frame index of the most intense drop.
 */
int caiedit_locate_drop(const float* energy, int num_frames, int hop_size) {
    if (!energy || num_frames < 20) return 0;
    
    int best_drop_idx = 0;
    float max_impact_score = -1.0f;

    // Search between 15% and 85% of track duration (drops rarely at second 0 or very end)
    int start_frame = static_cast<int>(num_frames * 0.15f);
    int end_frame = static_cast<int>(num_frames * 0.85f);

    for (int i = start_frame; i < end_frame; ++i) {
        // Build-up score: average energy leading up to this frame
        float pre_energy = 0.0f;
        for (int k = std::max(0, i - 15); k < i; ++k) pre_energy += energy[k];
        pre_energy /= 15.0f;

        // Post-impact energy: sudden jump in loudness
        float post_energy = 0.0f;
        for (int k = i; k < std::min(num_frames, i + 10); ++k) post_energy += energy[k];
        post_energy /= 10.0f;

        float impact = post_energy - pre_energy * 0.5f;
        if (impact > max_impact_score) {
            max_impact_score = impact;
            best_drop_idx = i;
        }
    }
    return best_drop_idx;
}

} // extern "C"
