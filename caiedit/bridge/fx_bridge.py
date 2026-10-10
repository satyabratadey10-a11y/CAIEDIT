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
