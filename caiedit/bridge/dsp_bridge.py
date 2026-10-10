"""
Zero-copy ctypes bridge to libcaiedit_dsp.so
Sub-millisecond audio feature extraction: RMS, low-pass bass, transients, drop points.
"""

import os
import ctypes
import numpy as np
from typing import List, Tuple

_LIB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "native", "libcaiedit_dsp.so")
_LIB_PATH = os.path.abspath(_LIB_PATH)

if not os.path.exists(_LIB_PATH):
    raise FileNotFoundError(f"Native DSP library not found at: {_LIB_PATH}. Run native/build.sh first.")

_lib = ctypes.CDLL(_LIB_PATH)

# Signatures
_lib.caiedit_calculate_rms.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
_lib.caiedit_calculate_rms.restype = ctypes.c_int

_lib.caiedit_lowpass_filter.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_float, ctypes.c_float]
_lib.caiedit_lowpass_filter.restype = None

_lib.caiedit_detect_transients.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_float, ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
_lib.caiedit_detect_transients.restype = ctypes.c_int

_lib.caiedit_locate_drop.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
_lib.caiedit_locate_drop.restype = ctypes.c_int

def calculate_rms_curve(samples: np.ndarray, hop_size: int = 512) -> np.ndarray:
    """Computes RMS energy curve across audio float32 samples."""
    samples = np.ascontiguousarray(samples, dtype=np.float32)
    num_samples = len(samples)
    max_frames = num_samples // hop_size
    out_energy = np.empty(max_frames, dtype=np.float32)
    
    s_ptr = samples.ctypes.data_as(ctypes.c_void_p)
    e_ptr = out_energy.ctypes.data_as(ctypes.c_void_p)
    actual_frames = _lib.caiedit_calculate_rms(s_ptr, num_samples, hop_size, e_ptr)
    return out_energy[:actual_frames]

def lowpass_filter(samples: np.ndarray, cutoff_hz: float = 140.0, sample_rate: float = 44100.0) -> np.ndarray:
    """Isolates sub-bass / kick drum audio frequencies (< 140Hz)."""
    samples = np.ascontiguousarray(samples, dtype=np.float32)
    out = np.empty_like(samples)
    s_ptr = samples.ctypes.data_as(ctypes.c_void_p)
    o_ptr = out.ctypes.data_as(ctypes.c_void_p)
    _lib.caiedit_lowpass_filter(s_ptr, o_ptr, len(samples), float(cutoff_hz), float(sample_rate))
    return out

def detect_transients(energy: np.ndarray, threshold_factor: float = 1.35, window_size: int = 15, max_peaks: int = 1000) -> np.ndarray:
    """Detects transient frame indices (e.g. kicks, downbeats) in energy array."""
    energy = np.ascontiguousarray(energy, dtype=np.float32)
    out_peaks = np.empty(max_peaks, dtype=np.int32)
    
    e_ptr = energy.ctypes.data_as(ctypes.c_void_p)
    p_ptr = out_peaks.ctypes.data_as(ctypes.c_void_p)
    count = _lib.caiedit_detect_transients(e_ptr, len(energy), float(threshold_factor), int(window_size), p_ptr, max_peaks)
    return out_peaks[:count]

def locate_drop_frame(energy: np.ndarray, hop_size: int = 512) -> int:
    """Finds the primary climax / bass drop frame index."""
    energy = np.ascontiguousarray(energy, dtype=np.float32)
    e_ptr = energy.ctypes.data_as(ctypes.c_void_p)
    return _lib.caiedit_locate_drop(e_ptr, len(energy), hop_size)
