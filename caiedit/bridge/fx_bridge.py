"""
Zero-copy ctypes bridge to libcaiedit_fx.so
Direct memory-pointer access to ARM NEON accelerated video effects.
"""

import os
import ctypes
import numpy as np

_LIB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "native", "libcaiedit_fx.so")
_LIB_PATH = os.path.abspath(_LIB_PATH)

if not os.path.exists(_LIB_PATH):
    raise FileNotFoundError(f"Native FX library not found at: {_LIB_PATH}. Run native/build.sh first.")

_lib = ctypes.CDLL(_LIB_PATH)

# Signatures
_lib.caiedit_rgb_split.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
_lib.caiedit_rgb_split.restype = None

_lib.caiedit_white_flash.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_float]
_lib.caiedit_white_flash.restype = None

_lib.caiedit_camera_shake.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
_lib.caiedit_camera_shake.restype = None

_lib.caiedit_color_grade.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.c_float, ctypes.c_int]
_lib.caiedit_color_grade.restype = None

_lib.caiedit_motion_blur_blend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_float]
_lib.caiedit_motion_blur_blend.restype = None

_lib.caiedit_resize_bilinear.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
_lib.caiedit_resize_bilinear.restype = None

def resize_bilinear(src: np.ndarray, dst_w: int, dst_h: int) -> np.ndarray:
    """Scales src frame to dst_w x dst_h using native C++ bilinear filtering."""
    src_h, src_w, _ = src.shape
    dst = np.empty((dst_h, dst_w, 3), dtype=np.uint8)
    p_src = src.ctypes.data_as(ctypes.c_void_p)
    p_dst = dst.ctypes.data_as(ctypes.c_void_p)
    _lib.caiedit_resize_bilinear(p_src, src_w, src_h, p_dst, dst_w, dst_h)
    return dst


def rgb_split(frame: np.ndarray, shift_x: int) -> np.ndarray:
    """Applies chromatic aberration (RGB split) in-place."""
    if shift_x <= 0:
        return frame
    h, w, _ = frame.shape
    ptr = frame.ctypes.data_as(ctypes.c_void_p)
    _lib.caiedit_rgb_split(ptr, w, h, shift_x)
    return frame

def white_flash(frame: np.ndarray, intensity: float) -> np.ndarray:
    """Applies white impact flash in-place."""
    if intensity <= 0.0:
        return frame
    h, w, _ = frame.shape
    ptr = frame.ctypes.data_as(ctypes.c_void_p)
    _lib.caiedit_white_flash(ptr, w, h, float(intensity))
    return frame

def camera_shake(src_frame: np.ndarray, dx: int, dy: int) -> np.ndarray:
    """Translates frame with edge reflection into a new output buffer."""
    if dx == 0 and dy == 0:
        return src_frame
    h, w, _ = src_frame.shape
    dst_frame = np.empty_like(src_frame)
    src_ptr = src_frame.ctypes.data_as(ctypes.c_void_p)
    dst_ptr = dst_frame.ctypes.data_as(ctypes.c_void_p)
    _lib.caiedit_camera_shake(src_ptr, dst_ptr, w, h, dx, dy)
    return dst_frame

def color_grade(frame: np.ndarray, contrast: float = 1.2, saturation: float = 1.3, crush_black: int = 10) -> np.ndarray:
    """Applies high-contrast anime/car phonk color grade in-place."""
    h, w, _ = frame.shape
    ptr = frame.ctypes.data_as(ctypes.c_void_p)
    _lib.caiedit_color_grade(ptr, w, h, float(contrast), float(saturation), int(crush_black))
    return frame

def motion_blur_blend(f1: np.ndarray, f2: np.ndarray, alpha: float) -> np.ndarray:
    """Blends two consecutive frames for velocity motion blur."""
    h, w, _ = f1.shape
    dst = np.empty_like(f1)
    p1 = f1.ctypes.data_as(ctypes.c_void_p)
    p2 = f2.ctypes.data_as(ctypes.c_void_p)
    pd = dst.ctypes.data_as(ctypes.c_void_p)
    _lib.caiedit_motion_blur_blend(p1, p2, pd, w, h, float(alpha))
    return dst

# --- Multi-Window Layout & Canvas Blitters ---

_lib.caiedit_fill_canvas.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8]
_lib.caiedit_fill_canvas.restype = None

_lib.caiedit_blur_backdrop.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_float]
_lib.caiedit_blur_backdrop.restype = None

_lib.caiedit_blit_card_window.argtypes = [
    ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
    ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8,
    ctypes.c_int, ctypes.c_float
]
_lib.caiedit_blit_card_window.restype = None

_lib.caiedit_render_particles.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.c_int]
_lib.caiedit_render_particles.restype = None

def fill_canvas(canvas: np.ndarray, r: int, g: int, b: int) -> np.ndarray:
    """Fills canvas with solid RGB color in-place."""
    h, w, _ = canvas.shape
    ptr = canvas.ctypes.data_as(ctypes.c_void_p)
    _lib.caiedit_fill_canvas(ptr, w, h, int(r), int(g), int(b))
    return canvas

def blur_backdrop(src: np.ndarray, canvas: np.ndarray, dim_factor: float = 0.35) -> np.ndarray:
    """Renders a scaled, blurred, and dimmed background copy of src into canvas in-place."""
    src_h, src_w, _ = src.shape
    dst_h, dst_w, _ = canvas.shape
    p_src = src.ctypes.data_as(ctypes.c_void_p)
    p_dst = canvas.ctypes.data_as(ctypes.c_void_p)
    _lib.caiedit_blur_backdrop(p_src, src_w, src_h, p_dst, dst_w, dst_h, float(dim_factor))
    return canvas

def blit_card_window(
    card_img: np.ndarray,
    canvas: np.ndarray,
    dst_x: int, dst_y: int,
    dst_w: int, dst_h: int,
    border_w: int = 3,
    border_rgb: tuple = (255, 255, 255),
    shadow_radius: int = 15,
    shadow_alpha: float = 0.6
) -> np.ndarray:
    """Blits an aspect-scaled card window into canvas with drop shadow and border."""
    c_h, c_w, _ = card_img.shape
    can_h, can_w, _ = canvas.shape
    p_card = card_img.ctypes.data_as(ctypes.c_void_p)
    p_can = canvas.ctypes.data_as(ctypes.c_void_p)
    br, bg, bb = border_rgb
    _lib.caiedit_blit_card_window(
        p_card, c_w, c_h,
        p_can, can_w, can_h,
        int(dst_x), int(dst_y), int(dst_w), int(dst_h),
        int(border_w), int(br), int(bg), int(bb),
        int(shadow_radius), float(shadow_alpha)
    )
    return canvas

def render_particles(frame: np.ndarray, time_sec: float, count: int = 60) -> np.ndarray:
    """MODULAR FX TOOL: Drifts soft glowing particles across frame (completely optional)."""
    h, w, _ = frame.shape
    ptr = frame.ctypes.data_as(ctypes.c_void_p)
    _lib.caiedit_render_particles(ptr, w, h, float(time_sec), int(count))
    return frame

