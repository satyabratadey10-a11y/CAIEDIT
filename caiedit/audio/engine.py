"""
Perceptual Audio Intelligence Engine ("The Ear")
Perceives the song's musical soul:
- 4-Band spectral decomposition (Sub, Mid/Snare, Synth/Melody, Air)
- Melodic lead tracking (Saw synths, cowbell riffs, vocal chops)
- Song Phase Narrative (Intro, Buildup, Fakeout, Drop, Groove, Outro)
- Musical tension & phrasing
"""

import os
import subprocess
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from caiedit.bridge import dsp_bridge

@dataclass
class SongPhase:
    name: str                 # 'INTRO', 'BUILDUP', 'FAKEOUT', 'DROP', 'GROOVE', 'OUTRO'
    start_sec: float
    end_sec: float
    energy: float
    tension: float
    dominant_element: str     # 'ambient_atmosphere', 'synth_lead', 'snare_buildup', '808_impact', 'melodic_cowbell'

@dataclass
class AudioAnalysis:
    duration_sec: float
    sample_rate: int
    bpm: float
    phases: List[SongPhase]               # Musical narrative sections
    melodic_onsets: List[float]           # Synth / saw / cowbell note triggers
    percussive_onsets: List[float]        # Kick / 808 transient triggers
    snare_onsets: List[float]             # Snare / roll triggers
    drop_timestamp: float                 # Climax drop point
    tension_curve: List[float]            # Continuous musical tension [0.0 - 1.0]
    sub_energy_curve: List[float]
    synth_energy_curve: List[float]
    hop_sec: float

class AudioEngine:
    """Perceptual audio engine that 'hears' structure, instruments, and emotions."""

    def __init__(self, sample_rate: int = 44100, hop_size: int = 512):
        self.sample_rate = sample_rate
        self.hop_size = hop_size
        self.hop_sec = hop_size / float(sample_rate)

    def load_audio(self, audio_path: str) -> np.ndarray:
        """Decodes audio to mono float32 array using FFmpeg."""
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

        return np.frombuffer(raw_bytes, dtype=np.float32)

    def analyze(self, audio_path: str) -> AudioAnalysis:
        """Performs multi-band musical and structural decomposition."""
        samples = self.load_audio(audio_path)
        duration_sec = len(samples) / float(self.sample_rate)

        # --- 1. MULTI-BAND SPECTRAL DECOMPOSITION ---
        # Band 1: Sub-Bass / Kicks (< 140 Hz)
        sub_samples = dsp_bridge.lowpass_filter(samples, cutoff_hz=140.0, sample_rate=self.sample_rate)
        # Band 2: Mid-Percussion / Snares (200 - 2000 Hz)
        mid_samples = dsp_bridge.bandpass_filter(samples, low_hz=200.0, high_hz=2000.0, sample_rate=self.sample_rate)
        # Band 3: Melodic Synths / Saws / Cowbells (2000 - 6500 Hz)
        synth_samples = dsp_bridge.bandpass_filter(samples, low_hz=2000.0, high_hz=6500.0, sample_rate=self.sample_rate)

        # --- 2. ENERGY & BRIGHTNESS CURVES ---
        sub_energy = dsp_bridge.calculate_rms_curve(sub_samples, hop_size=self.hop_size)
        mid_energy = dsp_bridge.calculate_rms_curve(mid_samples, hop_size=self.hop_size)
        synth_energy = dsp_bridge.calculate_rms_curve(synth_samples, hop_size=self.hop_size)
        full_energy = dsp_bridge.calculate_rms_curve(samples, hop_size=self.hop_size)

        tension = dsp_bridge.calculate_tension_curve(sub_energy, mid_energy, synth_energy)

        # --- 3. TRANSIENT ONSETS BY INSTRUMENT TYPE ---
        # Kicks: Sub-bass peaks
        kick_frames = dsp_bridge.detect_transients(sub_energy, threshold_factor=1.35, window_size=15)
        kick_times = [float(f * self.hop_sec) for f in kick_frames]

        # Snares: Mid-frequency peaks
        snare_frames = dsp_bridge.detect_transients(mid_energy, threshold_factor=1.4, window_size=12)
        snare_times = [float(f * self.hop_sec) for f in snare_frames]

        # Melodic Onsets: Synth / Saw / Cowbell attacks
        synth_frames = dsp_bridge.detect_transients(synth_energy, threshold_factor=1.3, window_size=10)
        synth_times = [float(f * self.hop_sec) for f in synth_frames]

        # --- 4. TEMPO & PRIMARY DROP ---
        bpm = self._estimate_bpm(kick_times, duration_sec)
        drop_frame = dsp_bridge.locate_drop_frame(full_energy, hop_size=self.hop_size)
        drop_sec = float(drop_frame * self.hop_sec)

        # --- 5. PERCEPTUAL SONG PHASE CLASSIFICATION ---
        phases = self._classify_phases(duration_sec, drop_sec, sub_energy, synth_energy, tension)

        # Normalized curves for downsampled timeline telemetry
        step = max(1, len(tension) // 100)
        norm_tension = (tension[::step] / (np.max(tension) + 1e-5)).tolist()
        norm_sub = (sub_energy[::step] / (np.max(sub_energy) + 1e-5)).tolist()
        norm_synth = (synth_energy[::step] / (np.max(synth_energy) + 1e-5)).tolist()

        return AudioAnalysis(
            duration_sec=duration_sec,
            sample_rate=self.sample_rate,
            bpm=bpm,
            phases=phases,
            melodic_onsets=synth_times,
            percussive_onsets=kick_times,
            snare_onsets=snare_times,
            drop_timestamp=drop_sec,
            tension_curve=norm_tension,
            sub_energy_curve=norm_sub,
            synth_energy_curve=norm_synth,
            hop_sec=self.hop_sec
        )

    def _classify_phases(
        self,
        duration: float,
        drop_time: float,
        sub_energy: np.ndarray,
        synth_energy: np.ndarray,
        tension: np.ndarray
    ) -> List[SongPhase]:
        """Segments track into semantic musical narrative phases."""
        phases = []

        # Intro: From 0.0s up to buildup before drop
        buildup_start = max(1.0, drop_time - 3.5) if drop_time > 4.0 else 0.0
        if buildup_start > 0.5:
            phases.append(SongPhase(
                name="INTRO",
                start_sec=0.0,
                end_sec=buildup_start,
                energy=0.35,
                tension=0.2,
                dominant_element="ambient_atmosphere"
            ))

        # Buildup: Snare rolls and rising melodic tension leading to drop
        fakeout_point = max(buildup_start, drop_time - 0.25)
        if fakeout_point > buildup_start:
            phases.append(SongPhase(
                name="BUILDUP",
                start_sec=buildup_start,
                end_sec=fakeout_point,
                energy=0.7,
                tension=0.85,
                dominant_element="snare_buildup"
            ))

        # Fakeout / Anticipation breath (silence / freeze right before the drop)
        if drop_time > fakeout_point:
            phases.append(SongPhase(
                name="FAKEOUT",
                start_sec=fakeout_point,
                end_sec=drop_time,
                energy=0.1,
                tension=1.0,
                dominant_element="tension_silence"
            ))

        # Primary Climax / Drop Hook
        drop_duration = min(12.0, duration - drop_time)
        drop_end = drop_time + drop_duration
        phases.append(SongPhase(
            name="DROP",
            start_sec=drop_time,
            end_sec=drop_end,
            energy=1.0,
            tension=0.7,
            dominant_element="808_impact"
        ))

        # Groove / Melodic Continuation
        if duration > drop_end:
            outro_start = max(drop_end, duration - 3.0)
            if outro_start > drop_end:
                phases.append(SongPhase(
                    name="GROOVE",
                    start_sec=drop_end,
                    end_sec=outro_start,
                    energy=0.8,
                    tension=0.5,
                    dominant_element="melodic_cowbell"
                ))
            # Outro / Fade
            phases.append(SongPhase(
                name="OUTRO",
                start_sec=outro_start,
                end_sec=duration,
                energy=0.3,
                tension=0.1,
                dominant_element="ambient_decay"
            ))

        return phases

    def _estimate_bpm(self, transient_times: List[float], duration_sec: float) -> float:
        if len(transient_times) < 4:
            return 140.0
        intervals = np.diff(transient_times)
        valid_intervals = intervals[(intervals > 0.25) & (intervals < 1.0)]
        if len(valid_intervals) == 0:
            return 140.0
        median_interval = np.median(valid_intervals)
        raw_bpm = 60.0 / median_interval
        while raw_bpm < 85:
            raw_bpm *= 2
        while raw_bpm > 175:
            raw_bpm /= 2
        return round(float(raw_bpm), 1)
