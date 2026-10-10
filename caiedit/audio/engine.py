"""
Audio Analysis & Intelligence Engine
Extracts beats, kicks, drop points, and audio dynamics using C++ DSP engine.
"""

import os
import subprocess
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from caiedit.bridge import dsp_bridge

@dataclass
class AudioAnalysis:
    duration_sec: float
    sample_rate: int
    bpm: float
    transients: List[float]       # Kick/snare timestamps in seconds
    drop_timestamp: float         # Climax / Bass drop timestamp in seconds
    energy_curve: List[float]     # Normalized RMS energy over time
    hop_sec: float

class AudioEngine:
    """Processes audio files using FFmpeg PCM decoding and C++ DSP analysis."""

    def __init__(self, sample_rate: int = 44100, hop_size: int = 512):
        self.sample_rate = sample_rate
        self.hop_size = hop_size
        self.hop_sec = hop_size / float(sample_rate)

    def load_audio(self, audio_path: str) -> np.ndarray:
        """Decodes any audio format (MP3, WAV, FLAC, AAC, etc.) to float32 mono array."""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        cmd = [
            "ffmpeg", "-v", "error", "-i", audio_path,
            "-f", "f32le", "-ac", "1", "-ar", str(self.sample_rate), "-"
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        raw_bytes, stderr = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg audio decode failed: {stderr.decode('utf-8', errors='ignore')}")

        samples = np.frombuffer(raw_bytes, dtype=np.float32)
        return samples

    def analyze(self, audio_path: str) -> AudioAnalysis:
        """Performs full audio intelligence analysis."""
        samples = self.load_audio(audio_path)
        duration_sec = len(samples) / float(self.sample_rate)

        # 1. Lowpass filter for bass/kicks
        bass_samples = dsp_bridge.lowpass_filter(samples, cutoff_hz=140.0, sample_rate=self.sample_rate)

        # 2. RMS energy curves
        bass_energy = dsp_bridge.calculate_rms_curve(bass_samples, hop_size=self.hop_size)
        full_energy = dsp_bridge.calculate_rms_curve(samples, hop_size=self.hop_size)

        # 3. Detect transient kicks
        transient_frames = dsp_bridge.detect_transients(bass_energy, threshold_factor=1.3, window_size=15)
        transient_times = [float(f * self.hop_sec) for f in transient_frames]

        # 4. Estimate BPM from transient inter-arrival times
        bpm = self._estimate_bpm(transient_times, duration_sec)

        # 5. Locate Drop Point
        drop_frame = dsp_bridge.locate_drop_frame(full_energy, hop_size=self.hop_size)
        drop_sec = float(drop_frame * self.hop_sec)

        # Normalize energy curve for downsampled telemetry
        subsampled_energy = full_energy[::max(1, len(full_energy) // 100)]
        norm_factor = np.max(subsampled_energy) if len(subsampled_energy) > 0 and np.max(subsampled_energy) > 0 else 1.0
        normalized_curve = (subsampled_energy / norm_factor).tolist()

        return AudioAnalysis(
            duration_sec=duration_sec,
            sample_rate=self.sample_rate,
            bpm=bpm,
            transients=transient_times,
            drop_timestamp=drop_sec,
            energy_curve=normalized_curve,
            hop_sec=self.hop_sec
        )

    def _estimate_bpm(self, transient_times: List[float], duration_sec: float) -> float:
        """Calculates BPM from peak intervals."""
        if len(transient_times) < 4:
            return 140.0  # Default fallback
        intervals = np.diff(transient_times)
        valid_intervals = intervals[(intervals > 0.25) & (intervals < 1.0)]
        if len(valid_intervals) == 0:
            return 140.0
        median_interval = np.median(valid_intervals)
        raw_bpm = 60.0 / median_interval
        # Quantize to common range (70 - 180)
        while raw_bpm < 90:
            raw_bpm *= 2
        while raw_bpm > 180:
            raw_bpm /= 2
        return round(float(raw_bpm), 1)
