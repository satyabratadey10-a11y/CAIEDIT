/**
 * CAIEDIT Native Audio DSP Engine (libcaiedit_dsp.so)
 * High-speed musical intelligence & semantic perception:
 * - 4-Band Musical Spectrum Separation (Sub-Bass, Snare/Mid, Synth/Melody, Air)
 * - Melodic Brightness / Spectral Centroid (Saw, Cowbell, Synth tracking)
 * - Musical Tension & Buildup Acceleration
 * - Drop & Climax Detection
 * - Microsecond execution latency on ARM NEON
 */

#include <cstdint>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <algorithm>

extern "C" {

/**
 * 1. RMS Energy Curve
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
 * 2. 1st-Order Low-Pass IIR Filter (Sub-Bass < cutoff_hz)
 */
void caiedit_lowpass_filter(const float* input, float* output, int num_samples, float cutoff_hz, float sample_rate) {
    if (!input || !output || num_samples <= 0) return;
    
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
 * 3. Band-Pass Filter (Isolates Melodic Synths, Saws, Cowbells, Snares)
 */
void caiedit_bandpass_filter(const float* input, float* output, int num_samples, float low_hz, float high_hz, float sample_rate) {
    if (!input || !output || num_samples <= 0) return;

    // Low-pass at high_hz
    float dt = 1.0f / sample_rate;
    float rc_high = 1.0f / (2.0f * 3.14159265f * high_hz);
    float alpha_high = dt / (rc_high + dt);

    // High-pass at low_hz
    float rc_low = 1.0f / (2.0f * 3.14159265f * low_hz);
    float alpha_low = rc_low / (rc_low + dt);

    float prev_lp = 0.0f;
    float prev_hp_in = 0.0f;
    float prev_hp_out = 0.0f;

    for (int i = 0; i < num_samples; ++i) {
        // Step 1: Low-pass filter to remove ultrasonic frequencies above high_hz
        prev_lp = prev_lp + alpha_high * (input[i] - prev_lp);
        
        // Step 2: High-pass filter to remove sub-bass below low_hz
        float hp_out = alpha_low * (prev_hp_out + prev_lp - prev_hp_in);
        prev_hp_in = prev_lp;
        prev_hp_out = hp_out;

        output[i] = hp_out;
    }
}

/**
 * 4. Melodic Brightness / Spectral Centroid Tracker
 * Tracks how high/sharp the active instruments are (detects synth leads vs dull bass).
 */
int caiedit_spectral_centroid(const float* samples, int num_samples, int hop_size, float sample_rate, float* out_brightness) {
    if (!samples || !out_brightness || num_samples <= 0 || hop_size <= 0) return 0;
    
    int num_frames = num_samples / hop_size;
    for (int f = 0; f < num_frames; ++f) {
        int start = f * hop_size;
        // Zero-crossing rate + absolute derivative as an ultra-fast proxy for spectral centroid
        int zero_crossings = 0;
        float energy_diff = 0.0f;
        float total_amp = 0.0f;

        for (int i = 1; i < hop_size; ++i) {
            float curr = samples[start + i];
            float prev = samples[start + i - 1];
            if ((curr >= 0.0f && prev < 0.0f) || (curr < 0.0f && prev >= 0.0f)) {
                zero_crossings++;
            }
            energy_diff += std::abs(curr - prev);
            total_amp += std::abs(curr);
        }

        float zcr = static_cast<float>(zero_crossings) / hop_size;
        float brightness = (zcr * 0.5f) + ((energy_diff / (total_amp + 1e-5f)) * 0.5f);
        out_brightness[f] = std::clamp(brightness, 0.0f, 1.0f);
    }
    return num_frames;
}

/**
 * 5. Musical Tension & Buildup Detector
 * Identifies rising tension in buildups (rising mid/high frequencies while sub-bass cuts out)
 */
int caiedit_calculate_tension(const float* sub_energy, const float* mid_energy, const float* high_energy, int num_frames, float* out_tension) {
    if (!sub_energy || !mid_energy || !high_energy || !out_tension || num_frames <= 0) return 0;

    for (int i = 0; i < num_frames; ++i) {
        // High tension = strong mids/highs (snare rolls, synth risers) with low sub-bass (anticipation)
        float melodic_presence = mid_energy[i] * 1.5f + high_energy[i] * 2.0f;
        float bass_weight = sub_energy[i] + 0.01f;
        
        // Tension ratio
        float ratio = melodic_presence / bass_weight;
        out_tension[i] = std::clamp(ratio * 0.2f, 0.0f, 1.0f);
    }
    return num_frames;
}

/**
 * 6. Transient Peak Detection
 */
int caiedit_detect_transients(const float* energy, int num_frames, float threshold_factor, int window_size, int* out_peaks, int max_peaks) {
    if (!energy || !out_peaks || num_frames <= 0 || max_peaks <= 0) return 0;
    
    int peak_count = 0;
    int half_win = window_size / 2;

    for (int i = half_win; i < num_frames - half_win; ++i) {
        float local_sum = 0.0f;
        for (int w = -half_win; w <= half_win; ++w) {
            local_sum += energy[i + w];
        }
        float local_mean = local_sum / window_size;

        float curr = energy[i];
        if (curr > local_mean * threshold_factor &&
            curr > energy[i - 1] && curr > energy[i + 1]) {
            
            if (peak_count == 0 || (i - out_peaks[peak_count - 1]) > 4) {
                out_peaks[peak_count++] = i;
                if (peak_count >= max_peaks) break;
            }
        }
    }
    return peak_count;
}

/**
 * 7. Climax / Primary Drop Locator
 */
int caiedit_locate_drop(const float* energy, int num_frames, int /*hop_size*/) {
    if (!energy || num_frames < 20) return 0;
    
    int best_drop_idx = 0;
    float max_impact_score = -1.0f;

    int start_frame = static_cast<int>(num_frames * 0.05f);
    int end_frame = static_cast<int>(num_frames * 0.90f);

    for (int i = start_frame; i < end_frame; ++i) {
        float pre_energy = 0.0f;
        for (int k = std::max(0, i - 15); k < i; ++k) pre_energy += energy[k];
        pre_energy /= 15.0f;

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
