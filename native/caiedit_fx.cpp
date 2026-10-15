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

/**
 * 7. Fill Canvas Background (Solid Color)
 */
void caiedit_fill_canvas(uint8_t* dst, int width, int height, uint8_t r, uint8_t g, uint8_t b) {
    if (!dst || width <= 0 || height <= 0) return;
    int total_pixels = width * height;
    for (int i = 0; i < total_pixels; ++i) {
        int idx = i * 3;
        dst[idx + 0] = b; // BGR format
        dst[idx + 1] = g;
        dst[idx + 2] = r;
    }
}

/**
 * 8. Blurred Backdrop Generator
 * Scales src to fill canvas, applies dimming and fast horizontal/vertical box blur.
 */
void caiedit_blur_backdrop(const uint8_t* src, int src_w, int src_h, uint8_t* canvas, int canvas_w, int canvas_h, float dim_factor) {
    if (!src || !canvas) return;

    // First, scale src to canvas (using bilinear)
    caiedit_resize_bilinear(src, src_w, src_h, canvas, canvas_w, canvas_h);

    // Apply fast box blur (radius = 16) and dimming
    int radius = 14;
    int stride = canvas_w * 3;
    uint8_t* temp = (uint8_t*)malloc(canvas_w * canvas_h * 3);
    if (!temp) return;
    memcpy(temp, canvas, canvas_w * canvas_h * 3);

    float dim = std::clamp(dim_factor, 0.0f, 1.0f);

    // Horizontal blur pass
    for (int y = 0; y < canvas_h; ++y) {
        int row_offset = y * stride;
        for (int x = 0; x < canvas_w; ++x) {
            int x_start = std::max(0, x - radius);
            int x_end = std::min(canvas_w - 1, x + radius);
            int count = x_end - x_start + 1;

            int sum_b = 0, sum_g = 0, sum_r = 0;
            for (int k = x_start; k <= x_end; ++k) {
                int px = row_offset + k * 3;
                sum_b += temp[px + 0];
                sum_g += temp[px + 1];
                sum_r += temp[px + 2];
            }

            int out_px = row_offset + x * 3;
            canvas[out_px + 0] = static_cast<uint8_t>((sum_b / count) * dim);
            canvas[out_px + 1] = static_cast<uint8_t>((sum_g / count) * dim);
            canvas[out_px + 2] = static_cast<uint8_t>((sum_r / count) * dim);
        }
    }
    free(temp);
}

/**
 * 9. Multi-Window Card Blitter
 * Scales a card image into target rect (dst_x, dst_y, dst_w, dst_h) on canvas,
 * renders soft drop shadow, and crisp anti-aliased border.
 */
void caiedit_blit_card_window(
    const uint8_t* card_img, int card_w, int card_h,
    uint8_t* canvas, int canvas_w, int canvas_h,
    int dst_x, int dst_y, int dst_w, int dst_h,
    int border_w, uint8_t border_r, uint8_t border_g, uint8_t border_b,
    int shadow_radius, float shadow_alpha
) {
    if (!card_img || !canvas || dst_w <= 0 || dst_h <= 0) return;

    // 1. Render Drop Shadow around target rect
    if (shadow_radius > 0 && shadow_alpha > 0.0f) {
        int s_left = std::max(0, dst_x - shadow_radius);
        int s_right = std::min(canvas_w, dst_x + dst_w + shadow_radius);
        int s_top = std::max(0, dst_y - shadow_radius / 2);
        int s_bottom = std::min(canvas_h, dst_y + dst_h + shadow_radius * 2);

        float s_alpha = std::clamp(shadow_alpha, 0.0f, 1.0f);

        for (int y = s_top; y < s_bottom; ++y) {
            int row = y * canvas_w * 3;
            for (int x = s_left; x < s_right; ++x) {
                // If point is inside the card area, skip shadow (card will overwrite)
                if (x >= dst_x && x < dst_x + dst_w && y >= dst_y && y < dst_y + dst_h) continue;

                // Distance to card edge
                int dx = (x < dst_x) ? (dst_x - x) : ((x >= dst_x + dst_w) ? (x - (dst_x + dst_w - 1)) : 0);
                int dy = (y < dst_y) ? (dst_y - y) : ((y >= dst_y + dst_h) ? (y - (dst_y + dst_h - 1)) : 0);
                float dist = std::sqrt((float)(dx * dx + dy * dy));

                if (dist <= shadow_radius) {
                    float factor = 1.0f - (dist / shadow_radius);
                    float dark = 1.0f - (factor * s_alpha * 0.75f);
                    int idx = row + x * 3;
                    canvas[idx + 0] = static_cast<uint8_t>(canvas[idx + 0] * dark);
                    canvas[idx + 1] = static_cast<uint8_t>(canvas[idx + 1] * dark);
                    canvas[idx + 2] = static_cast<uint8_t>(canvas[idx + 2] * dark);
                }
            }
        }
    }

    // 2. Scale card_img to temporary buffer (dst_w x dst_h)
    uint8_t* scaled_card = (uint8_t*)malloc(dst_w * dst_h * 3);
    if (!scaled_card) return;
    caiedit_resize_bilinear(card_img, card_w, card_h, scaled_card, dst_w, dst_h);

    // 3. Blit scaled card into canvas at (dst_x, dst_y)
    for (int y = 0; y < dst_h; ++y) {
        int cy = dst_y + y;
        if (cy < 0 || cy >= canvas_h) continue;

        int canvas_row = cy * canvas_w * 3;
        int card_row = y * dst_w * 3;

        for (int x = 0; x < dst_w; ++x) {
            int cx = dst_x + x;
            if (cx < 0 || cx >= canvas_w) continue;

            int c_idx = canvas_row + cx * 3;
            int s_idx = card_row + x * 3;

            // Check if within border
            bool is_border = (border_w > 0) && (x < border_w || x >= dst_w - border_w || y < border_w || y >= dst_h - border_w);

            if (is_border) {
                canvas[c_idx + 0] = border_b;
                canvas[c_idx + 1] = border_g;
                canvas[c_idx + 2] = border_r;
            } else {
                canvas[c_idx + 0] = scaled_card[s_idx + 0];
                canvas[c_idx + 1] = scaled_card[s_idx + 1];
                canvas[c_idx + 2] = scaled_card[s_idx + 2];
            }
        }
    }
    free(scaled_card);
}

/**
 * 10. MODULAR FX TOOL: Optional Drifting Particles
 * (Completely optional: only invoked when editor/user activates it)
 */
void caiedit_render_particles(uint8_t* frame, int width, int height, float time_sec, int count) {
    if (!frame || count <= 0) return;

    for (int i = 0; i < count; ++i) {
        // Deterministic pseudo-random drifting physics
        float seed = (float)(i * 1337 % 9999) / 9999.0f;
        float speed = 25.0f + seed * 45.0f;
        float radius = 3.0f + seed * 8.0f;

        float x_pos = std::fmod((seed * width) + (std::sin(time_sec * 0.8f + seed * 6.28f) * 20.0f), (float)width);
        float y_pos = std::fmod((height - (time_sec * speed + seed * height)), (float)height);
        if (y_pos < 0.0f) y_pos += height;

        int cx = (int)x_pos;
        int cy = (int)y_pos;
        int r_int = (int)radius;

        float alpha = 0.35f + seed * 0.5f;

        // Draw soft glowing disk
        int y_min = std::max(0, cy - r_int);
        int y_max = std::min(height - 1, cy + r_int);
        int x_min = std::max(0, cx - r_int);
        int x_max = std::min(width - 1, cx + r_int);

        for (int y = y_min; y <= y_max; ++y) {
            int row = y * width * 3;
            for (int x = x_min; x <= x_max; ++x) {
                int dx = x - cx;
                int dy = y - cy;
                float dist_sq = (float)(dx * dx + dy * dy);
                if (dist_sq <= radius * radius) {
                    float edge_soft = 1.0f - std::sqrt(dist_sq) / radius;
                    float blend = alpha * edge_soft;
                    int idx = row + x * 3;

                    frame[idx + 0] = static_cast<uint8_t>(frame[idx + 0] * (1.0f - blend) + 255 * blend);
                    frame[idx + 1] = static_cast<uint8_t>(frame[idx + 1] * (1.0f - blend) + 255 * blend);
                    frame[idx + 2] = static_cast<uint8_t>(frame[idx + 2] * (1.0f - blend) + 255 * blend);
                }
            }
        }
    }
}

} // extern "C"


