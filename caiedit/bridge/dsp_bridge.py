"""
Zero-copy ctypes bridge to libcaiedit_dsp.so
Sub-millisecond audio feature extraction:
- 4-Band Musical Spectrum Separation (Sub-Bass, Mid/Snare, Synth/Melody, Air)
- Melodic Brightness / Spectral Centroid
- Tension & Buildup Acceleration
- Drops, Kicks & Transients
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

_lib.caiedit_bandpass_filter.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_float, ctypes.c_float, ctypes.c_float]
_lib.caiedit_bandpass_filter.restype = None

_lib.caiedit_spectral_centroid.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.c_void_p]
_lib.caiedit_spectral_centroid.restype = ctypes.c_int

_lib.caiedit_calculate_tension.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
_lib.caiedit_calculate_tension.restype = ctypes.c_int

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

def bandpass_filter(samples: np.ndarray, low_hz: float, high_hz: float, sample_rate: float = 44100.0) -> np.ndarray:
    """Isolates specific frequency band (e.g. synths, cowbells, lead saws)."""
    samples = np.ascontiguousarray(samples, dtype=np.float32)
    out = np.empty_like(samples)
    s_ptr = samples.ctypes.data_as(ctypes.c_void_p)
    o_ptr = out.ctypes.data_as(ctypes.c_void_p)
    _lib.caiedit_bandpass_filter(s_ptr, o_ptr, len(samples), float(low_hz), float(high_hz), float(sample_rate))
    return out

def calculate_spectral_centroid(samples: np.ndarray, hop_size: int = 512, sample_rate: float = 44100.0) -> np.ndarray:
    """Tracks melodic brightness / lead synth activity."""
    samples = np.ascontiguousarray(samples, dtype=np.float32)
    max_frames = len(samples) // hop_size
    out = np.empty(max_frames, dtype=np.float32)
    s_ptr = samples.ctypes.data_as(ctypes.c_void_p)
    o_ptr = out.ctypes.data_as(ctypes.c_void_p)
    actual = _lib.caiedit_spectral_centroid(s_ptr, len(samples), hop_size, float(sample_rate), o_ptr)
    return out[:actual]

def calculate_tension_curve(sub_energy: np.ndarray, mid_energy: np.ndarray, high_energy: np.ndarray) -> np.ndarray:
    """Calculates musical tension curve across frames."""
    sub_energy = np.ascontiguousarray(sub_energy, dtype=np.float32)
    mid_energy = np.ascontiguousarray(mid_energy, dtype=np.float32)
    high_energy = np.ascontiguousarray(high_energy, dtype=np.float32)
    num_frames = min(len(sub_energy), len(mid_energy), len(high_energy))
    out = np.empty(num_frames, dtype=np.float32)
    
    _lib.caiedit_calculate_tension(
        sub_energy.ctypes.data_as(ctypes.c_void_p),
        mid_energy.ctypes.data_as(ctypes.c_void_p),
        high_energy.ctypes.data_as(ctypes.c_void_p),
        num_frames,
        out.ctypes.data_as(ctypes.c_void_p)
    )
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
