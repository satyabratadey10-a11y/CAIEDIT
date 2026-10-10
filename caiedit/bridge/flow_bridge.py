"""
Zero-copy ctypes bridge to libcaiedit_flow.so
Scene cut detection and motion magnitude estimation.
"""

import os
import ctypes
import numpy as np

_LIB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "native", "libcaiedit_flow.so")
_LIB_PATH = os.path.abspath(_LIB_PATH)

if not os.path.exists(_LIB_PATH):
    raise FileNotFoundError(f"Native flow library not found at: {_LIB_PATH}. Run native/build.sh first.")

_lib = ctypes.CDLL(_LIB_PATH)

# Signatures
_lib.caiedit_frame_difference.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
_lib.caiedit_frame_difference.restype = ctypes.c_float

_lib.caiedit_estimate_motion_magnitude.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
_lib.caiedit_estimate_motion_magnitude.restype = ctypes.c_float

_lib.caiedit_interpolate_frame.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_float]
_lib.caiedit_interpolate_frame.restype = None

def frame_difference(f1: np.ndarray, f2: np.ndarray) -> float:
    """Calculates difference score between two frames [0.0 - 255.0]."""
    h, w, _ = f1.shape
    p1 = f1.ctypes.data_as(ctypes.c_void_p)
    p2 = f2.ctypes.data_as(ctypes.c_void_p)
    return float(_lib.caiedit_frame_difference(p1, p2, w, h))

def estimate_motion(f1: np.ndarray, f2: np.ndarray) -> float:
    """Estimates motion magnitude between frames."""
    h, w, _ = f1.shape
    p1 = f1.ctypes.data_as(ctypes.c_void_p)
    p2 = f2.ctypes.data_as(ctypes.c_void_p)
    return float(_lib.caiedit_estimate_motion_magnitude(p1, p2, w, h))

def interpolate_frame(f1: np.ndarray, f2: np.ndarray, t: float) -> np.ndarray:
    """Generates an intermediate frame at fraction t in [0.0, 1.0]."""
    h, w, _ = f1.shape
    dst = np.empty_like(f1)
    p1 = f1.ctypes.data_as(ctypes.c_void_p)
    p2 = f2.ctypes.data_as(ctypes.c_void_p)
    pd = dst.ctypes.data_as(ctypes.c_void_p)
    _lib.caiedit_interpolate_frame(p1, p2, pd, w, h, float(t))
    return dst
