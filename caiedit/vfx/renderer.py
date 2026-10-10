"""
High-Performance Viral Video Compositor & VFX Renderer
Applies velocity speed ramping, bass-reactive shakes, impact flashes, and RGB split.
Encodes directly via FFmpeg pipe (Zero temp disk frames).
"""

import os
import random
import subprocess
import numpy as np
from typing import List, Dict, Any, Optional
from caiedit.bridge import fx_bridge

class ViralRenderer:
    """Zero-disk-overhead video rendering engine powered by native C++ VFX."""

    def __init__(self, width: int = 1080, height: int = 1920, fps: int = 60):
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_bytes = width * height * 3

    def render(
        self,
        raw_clips: List[str],
        audio_path: str,
        output_path: str,
        cut_timestamps: List[float],
        drop_timestamp: float = 0.0,
        enable_shake: bool = True,
        enable_flash: bool = True,
        enable_rgb_split: bool = True,
        enable_color_grade: bool = True,
        max_duration: Optional[float] = None
    ) -> str:
        """Assembles clips, synchronizes VFX on beats and drops, and renders final MP4."""
        if not raw_clips:
            raise ValueError("At least one raw footage clip is required.")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Determine total render duration from cuts or max_duration
        if max_duration:
            total_duration = max_duration
        elif cut_timestamps and len(cut_timestamps) > 1:
            total_duration = cut_timestamps[-1]
        else:
            total_duration = 10.0

        total_frames = int(total_duration * self.fps)
        print(f"🎬 [ViralRenderer] Rendering {total_frames} frames ({total_duration:.2f}s) @ {self.fps} FPS ({self.width}x{self.height} 9:16)")

        # Prepare FFmpeg output encoder pipe
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "rawvideo", "-pix_fmt", "bgr24",
            "-s", f"{self.width}x{self.height}",
            "-r", str(self.fps),
            "-i", "-",  # Video pipe from stdin
            "-i", audio_path,  # Audio input
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(total_duration),
            output_path
        ]

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        # Prepare clip readers
        clip_processes = []
        for clip in raw_clips:
            p = subprocess.Popen([
                "ffmpeg", "-v", "error", "-stream_loop", "-1", "-i", clip,
                "-vf", f"scale={self.width}:{self.height}:force_original_aspect_ratio=increase,crop={self.width}:{self.height},fps={self.fps}",
                "-f", "rawvideo", "-pix_fmt", "bgr24", "-"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            clip_processes.append(p)

        current_clip_idx = 0
        cut_idx = 0
        drop_frame_idx = int(drop_timestamp * self.fps) if drop_timestamp > 0 else -1

        try:
            for frame_idx in range(total_frames):
                current_time = frame_idx / float(self.fps)

                # Check if we should switch clips (cut point hit)
                if cut_idx < len(cut_timestamps) - 1:
                    if current_time >= cut_timestamps[cut_idx + 1]:
                        cut_idx += 1
                        current_clip_idx = (current_clip_idx + 1) % len(clip_processes)

                # Read frame from active clip
                active_p = clip_processes[current_clip_idx]
                raw_data = active_p.stdout.read(self.frame_bytes)
                if not raw_data or len(raw_data) < self.frame_bytes:
                    frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                else:
                    frame = np.frombuffer(raw_data, dtype=np.uint8).reshape((self.height, self.width, 3)).copy()

                # --- APPLY NATIVE C++ VIRAL VFX ---

                # 1. Color Grade (Anime / Phonk punch)
                if enable_color_grade:
                    fx_bridge.color_grade(frame, contrast=1.25, saturation=1.35, crush_black=12)

                # 2. Climax / Drop Impact Flash
                if enable_flash and drop_frame_idx >= 0:
                    delta = frame_idx - drop_frame_idx
                    if 0 <= delta <= 12:  # 12 frames flash decay (~0.2s)
                        flash_intensity = 0.9 * (1.0 - (delta / 12.0))
                        fx_bridge.white_flash(frame, intensity=flash_intensity)

                # 3. Drop Bass Shake
                if enable_shake and drop_frame_idx >= 0:
                    delta = frame_idx - drop_frame_idx
                    if 0 <= delta <= 20:  # 20 frames camera shake
                        decay = 1.0 - (delta / 20.0)
                        dx = int((random.uniform(-18, 18)) * decay)
                        dy = int((random.uniform(-18, 18)) * decay)
                        frame = fx_bridge.camera_shake(frame, dx=dx, dy=dy)

                # 4. RGB Split (Chromatic Aberration on drop impact)
                if enable_rgb_split and drop_frame_idx >= 0:
                    delta = frame_idx - drop_frame_idx
                    if 0 <= delta <= 15:
                        shift_x = int(12 * (1.0 - (delta / 15.0)))
                        fx_bridge.rgb_split(frame, shift_x=shift_x)

                # Stream processed frame to FFmpeg encoder
                proc.stdin.write(frame.tobytes())

        finally:
            proc.stdin.close()
            proc.wait()
            # Clean up clip readers
            for p in clip_processes:
                try:
                    p.kill()
                except Exception:
                    pass

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError(f"Rendering failed. Output file is empty or missing: {output_path}")

        print(f"✅ [ViralRenderer] Successfully rendered: {output_path} ({os.path.getsize(output_path) / (1024*1024):.2f} MB)")
        return output_path
