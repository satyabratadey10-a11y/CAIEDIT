"""
Vision Intelligence & Reference Video Reverse-Engineering Engine
Extracts scene cuts, pacing blueprints, and motion velocity curves from reference videos.
"""

import os
import subprocess
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any
from caiedit.bridge import flow_bridge

@dataclass
class VideoBlueprint:
    duration_sec: float
    cut_timestamps: List[float]       # Detected scene transition timestamps
    cut_intervals: List[float]        # Duration of each shot
    average_shot_duration: float      # Overall pacing speed
    motion_energy: List[float]        # Optical flow velocity curve
    detected_style: str               # e.g., 'hyper_velocity_phonk', 'cinematic_pacing'

class VisionAnalyzer:
    """Analyzes reference videos using FFmpeg raw frame streaming and C++ flow engine."""

    def __init__(self, sample_fps: int = 15, width: int = 480, height: int = 854):
        self.sample_fps = sample_fps
        self.width = width
        self.height = height
        self.frame_bytes = width * height * 3

    def analyze_reference(self, video_path: str, cut_threshold: float = 28.0) -> VideoBlueprint:
        """Reads reference video and extracts cut map and velocity curves."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Reference video not found: {video_path}")

        # Stream scaled frames via FFmpeg
        cmd = [
            "ffmpeg", "-v", "error", "-i", video_path,
            "-vf", f"scale={self.width}:{self.height},fps={self.sample_fps}",
            "-f", "rawvideo", "-pix_fmt", "bgr24", "-"
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        cut_timestamps = [0.0]
        motion_curve = []
        prev_frame = None
        frame_idx = 0

        while True:
            raw_bytes = proc.stdout.read(self.frame_bytes)
            if not raw_bytes or len(raw_bytes) < self.frame_bytes:
                break

            curr_frame = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((self.height, self.width, 3))

            if prev_frame is not None:
                # 1. Scene cut difference using C++ engine
                diff = flow_bridge.frame_difference(prev_frame, curr_frame)
                motion = flow_bridge.estimate_motion(prev_frame, curr_frame)
                motion_curve.append(float(motion))

                if diff > cut_threshold:
                    t = frame_idx / float(self.sample_fps)
                    # Minimum shot distance: 0.15 seconds
                    if len(cut_timestamps) == 0 or (t - cut_timestamps[-1]) > 0.15:
                        cut_timestamps.append(round(t, 2))

            prev_frame = curr_frame
            frame_idx += 1

        proc.stdout.close()
        proc.wait()

        total_duration = frame_idx / float(self.sample_fps)
        if len(cut_timestamps) == 0:
            cut_timestamps = [0.0]

        # Calculate shot intervals
        cut_intervals = []
        for i in range(len(cut_timestamps) - 1):
            cut_intervals.append(round(cut_timestamps[i+1] - cut_timestamps[i], 2))

        avg_shot = float(np.mean(cut_intervals)) if cut_intervals else total_duration

        # Classify style
        if avg_shot < 0.6:
            style = "hyper_velocity_phonk"
        elif avg_shot < 1.2:
            style = "dynamic_action_montage"
        else:
            style = "cinematic_narrative"

        return VideoBlueprint(
            duration_sec=total_duration,
            cut_timestamps=cut_timestamps,
            cut_intervals=cut_intervals,
            average_shot_duration=round(avg_shot, 2),
            motion_energy=motion_curve[::max(1, len(motion_curve) // 50)],
            detected_style=style
        )
