/**
 * CAIEDIT Native VFX Engine (libcaiedit_fx.so)
 * High-performance frame-level effects for viral edits:
 * - Chromatic Aberration / RGB Split
 * - Exponential Decay White Impact Flash
 * - Sub-pixel Reflective Camera Shake
 * - Anime / Phonk Color Contrast & Saturation Boost
 * - Frame Motion Blur Blending
 *
 * Optimized for aarch64 ARM NEON SIMD & multi-threading.
 */

#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <algorithm>

#if defined(__ARM_NEON) || defined(__ARM_NEON__)
#include <arm_neon.h>
#define HAS_NEON 1
#else
#define HAS_NEON 0
#endif

extern "C" {

/**
 * 1. RGB Split (Chromatic Aberration)
 * Shifts Red channel right by +shift_x, Blue channel left by -shift_x.
 * Green channel remains anchored.
 */
void caiedit_rgb_split(uint8_t* frame, int width, int height, int shift_x) {
    if (!frame || shift_x <= 0 || width <= 0 || height <= 0) return;
    int stride = width * 3;

    for (int y = 0; y < height; ++y) {
        uint8_t* row = frame + y * stride;
        // Make a lightweight copy of the row to read unshifted values
        // Dynamic row buffer
        uint8_t* temp_row = (uint8_t*)malloc(stride);
        if (!temp_row) return;
        memcpy(temp_row, row, stride);

        for (int x = 0; x < width; ++x) {
            int r_src_x = x - shift_x; // Red from left
            int b_src_x = x + shift_x; // Blue from right

            if (r_src_x >= 0 && r_src_x < width) {
                row[x * 3 + 2] = temp_row[r_src_x * 3 + 2]; // Red
            }
            if (b_src_x >= 0 && b_src_x < width) {
                row[x * 3 + 0] = temp_row[b_src_x * 3 + 0]; // Blue
            }
        }
        free(temp_row);
    }
}

/**
 * 2. White Impact Flash
 * Blends pixel buffer towards pure white (255, 255, 255) by intensity [0.0, 1.0].
 * Uses NEON vectorization when compiled on ARM64.
 */
void caiedit_white_flash(uint8_t* frame, int width, int height, float intensity) {
    if (!frame || intensity <= 0.0f) return;
    if (intensity > 1.0f) intensity = 1.0f;

    int total_bytes = width * height * 3;
    uint32_t alpha = static_cast<uint32_t>(intensity * 256.0f);
    uint32_t inv_alpha = 256 - alpha;

    int i = 0;
#if HAS_NEON
    uint8x8_t v_alpha = vdup_n_u8(static_cast<uint8_t>(alpha > 255 ? 255 : alpha));
    uint8x8_t v_inv_alpha = vdup_n_u8(static_cast<uint8_t>(inv_alpha > 255 ? 255 : inv_alpha));
    uint8x8_t v_255 = vdup_n_u8(255);

    for (; i <= total_bytes - 8; i += 8) {
        uint8x8_t src = vld1_u8(frame + i);
        // (src * inv_alpha + 255 * alpha) / 256
        uint16x8_t term1 = vmull_u8(src, v_inv_alpha);
        uint16x8_t term2 = vmull_u8(v_255, v_alpha);
        uint16x8_t sum = vaddq_u16(term1, term2);
        uint8x8_t result = vshrn_n_u16(sum, 8);
        vst1_u8(frame + i, result);
    }
#endif

    for (; i < total_bytes; ++i) {
        frame[i] = static_cast<uint8_t>((frame[i] * inv_alpha + 255 * alpha) >> 8);
    }
}

/**
 * 3. Sub-pixel Reflective Camera Shake
 * Translates frame by (dx, dy) with border reflection to prevent black bars.
 */
void caiedit_camera_shake(const uint8_t* src, uint8_t* dst, int width, int height, int dx, int dy) {
    if (!src || !dst) return;
    int stride = width * 3;

    for (int y = 0; y < height; ++y) {
        int sy = y + dy;
        // Reflective edge boundary
        if (sy < 0) sy = -sy;
        if (sy >= height) sy = 2 * (height - 1) - sy;
        sy = std::clamp(sy, 0, height - 1);

        int src_row_offset = sy * stride;
        int dst_row_offset = y * stride;

        for (int x = 0; x < width; ++x) {
            int sx = x + dx;
            if (sx < 0) sx = -sx;
            if (sx >= width) sx = 2 * (width - 1) - sx;
            sx = std::clamp(sx, 0, width - 1);

            int dst_px = dst_row_offset + x * 3;
            int src_px = src_row_offset + sx * 3;

            dst[dst_px + 0] = src[src_px + 0];
            dst[dst_px + 1] = src[src_px + 1];
            dst[dst_px + 2] = src[src_px + 2];
        }
    }
}

/**
 * 4. Phonk / Anime Color Grading (Contrast + Saturation + Black Crush)
 * contrast: [0.5, 2.5] (1.0 = normal)
 * saturation: [0.0, 2.5] (1.0 = normal, 1.4 = anime punch)
 * crush_black: [0, 30] (lifts or crushes deep shadows)
 */
void caiedit_color_grade(uint8_t* frame, int width, int height, float contrast, float saturation, int crush_black) {
    if (!frame) return;
    int total_pixels = width * height;

    for (int i = 0; i < total_pixels; ++i) {
        int idx = i * 3;
        float b = frame[idx + 0];
        float g = frame[idx + 1];
        float r = frame[idx + 2];

        // 1. Contrast adjustment around midpoint 128
        r = (r - 128.0f) * contrast + 128.0f;
        g = (g - 128.0f) * contrast + 128.0f;
        b = (b - 128.0f) * contrast + 128.0f;

        // 2. Black crush
        if (crush_black > 0) {
            r = (r < crush_black) ? 0.0f : r;
            g = (g < crush_black) ? 0.0f : g;
            b = (b < crush_black) ? 0.0f : b;
        }

        // 3. Saturation boost
        float gray = 0.299f * r + 0.587f * g + 0.114f * b;
        r = gray + (r - gray) * saturation;
        g = gray + (g - gray) * saturation;
        b = gray + (b - gray) * saturation;

        frame[idx + 0] = static_cast<uint8_t>(std::clamp(b, 0.0f, 255.0f));
        frame[idx + 1] = static_cast<uint8_t>(std::clamp(g, 0.0f, 255.0f));
        frame[idx + 2] = static_cast<uint8_t>(std::clamp(r, 0.0f, 255.0f));
    }
}

/**
 * 5. Motion Blur Blend
 * Blends two consecutive frames: dst = f1 * (1 - alpha) + f2 * alpha
 */
void caiedit_motion_blur_blend(const uint8_t* f1, const uint8_t* f2, uint8_t* dst, int width, int height, float alpha) {
    if (!f1 || !f2 || !dst) return;
    int total_bytes = width * height * 3;
    uint32_t a = static_cast<uint32_t>(std::clamp(alpha, 0.0f, 1.0f) * 256.0f);
    uint32_t inv_a = 256 - a;

    int i = 0;
#if HAS_NEON
    uint8x8_t v_a = vdup_n_u8(static_cast<uint8_t>(a > 255 ? 255 : a));
    uint8x8_t v_inv_a = vdup_n_u8(static_cast<uint8_t>(inv_a > 255 ? 255 : inv_a));

    for (; i <= total_bytes - 8; i += 8) {
        uint8x8_t v1 = vld1_u8(f1 + i);
        uint8x8_t v2 = vld1_u8(f2 + i);
        uint16x8_t term1 = vmull_u8(v1, v_inv_a);
        uint16x8_t term2 = vmull_u8(v2, v_a);
        uint16x8_t sum = vaddq_u16(term1, term2);
        uint8x8_t result = vshrn_n_u16(sum, 8);
        vst1_u8(dst + i, result);
    }
#endif

    for (; i < total_bytes; ++i) {
        dst[i] = static_cast<uint8_t>((f1[i] * inv_a + f2[i] * a) >> 8);
    }
}

/**
 * 6. High-Speed Bilinear Resizer
 * Scales src (src_w x src_h) into dst (dst_w x dst_h) with smooth bilinear filtering.
 */
void caiedit_resize_bilinear(const uint8_t* src, int src_w, int src_h, uint8_t* dst, int dst_w, int dst_h) {
    if (!src || !dst || src_w <= 0 || src_h <= 0 || dst_w <= 0 || dst_h <= 0) return;

    float x_ratio = (src_w > 1) ? ((float)(src_w - 1) / (float)dst_w) : 0.0f;
    float y_ratio = (src_h > 1) ? ((float)(src_h - 1) / (float)dst_h) : 0.0f;

    for (int y = 0; y < dst_h; ++y) {
        int sy = (int)(y_ratio * y);
        float y_diff = (y_ratio * y) - sy;
        int sy1 = std::min(sy + 1, src_h - 1);

        int dst_row = y * dst_w * 3;
        int src_row0 = sy * src_w * 3;
        int src_row1 = sy1 * src_w * 3;

        for (int x = 0; x < dst_w; ++x) {
            int sx = (int)(x_ratio * x);
            float x_diff = (x_ratio * x) - sx;
            int sx1 = std::min(sx + 1, src_w - 1);

            int dst_idx = dst_row + x * 3;
            int a_idx = src_row0 + sx * 3;
            int b_idx = src_row0 + sx1 * 3;
            int c_idx = src_row1 + sx * 3;
            int d_idx = src_row1 + sx1 * 3;

            for (int c = 0; c < 3; ++c) {
                float a = src[a_idx + c];
                float b = src[b_idx + c];
                float c_val = src[c_idx + c];
                float d = src[d_idx + c];

                float val = a * (1.0f - x_diff) * (1.0f - y_diff) +
                            b * x_diff * (1.0f - y_diff) +
                            c_val * y_diff * (1.0f - x_diff) +
                            d * (x_diff * y_diff);

                dst[dst_idx + c] = static_cast<uint8_t>(std::clamp(val, 0.0f, 255.0f));
            }
        }
    }
}

} // extern "C"

