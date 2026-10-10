"""
High-Performance Viral Video Compositor & VFX Renderer
Applies velocity speed ramping, bass-reactive shakes, impact flashes, and RGB split.
Encodes directly via FFmpeg pipe (Zero temp disk frames).
Supports both video clips (.mp4, .mov) and image sequences (.jpg, .png) with dynamic camera motion.
"""

import os
import random
import subprocess
import numpy as np
from typing import List, Dict, Any, Optional
from caiedit.bridge import fx_bridge

class ViralRenderer:
    """Zero-disk-overhead video rendering engine powered by native C++ VFX."""

    def __init__(self, width: int = 1080, height: int = 1080, fps: int = 60):
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_bytes = width * height * 3

    def _is_image(self, path: str) -> bool:
        ext = os.path.splitext(path)[1].lower()
        return ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]

    def _load_images_to_memory(self, image_paths: List[str]) -> List[np.ndarray]:
        """Loads and pre-scales images into BGR numpy arrays."""
        loaded = []
        print(f"🖼️ Pre-loading {len(image_paths)} images into high-speed memory buffers...")
        for p in image_paths:
            # Scale and crop to target resolution via FFmpeg
            cmd = [
                "ffmpeg", "-v", "error", "-i", p,
                "-vf", f"scale={self.width}:{self.height}:force_original_aspect_ratio=increase,crop={self.width}:{self.height}",
                "-f", "rawvideo", "-pix_fmt", "bgr24", "-"
            ]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw, _ = proc.communicate()
            if len(raw) >= self.frame_bytes:
                arr = np.frombuffer(raw[:self.frame_bytes], dtype=np.uint8).reshape((self.height, self.width, 3))
                loaded.append(arr)
        if not loaded:
            raise RuntimeError("Failed to decode any input images.")
        return loaded

    def render(
        self,
        raw_clips: List[str],
        audio_path: str,
        output_path: str,
        cut_timestamps: List[float],
        drop_timestamp: float = 0.0,
        transient_timestamps: Optional[List[float]] = None,
        enable_shake: bool = True,
        enable_flash: bool = True,
        enable_rgb_split: bool = True,
        enable_color_grade: bool = True,
        max_duration: Optional[float] = None
    ) -> str:
        """Assembles clips/images, synchronizes VFX on beats and drops, and renders final MP4."""
        if not raw_clips:
            raise ValueError("At least one raw footage clip or image is required.")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        if max_duration:
            total_duration = max_duration
        elif cut_timestamps and len(cut_timestamps) > 1:
            total_duration = cut_timestamps[-1]
        else:
            total_duration = 10.0

        total_frames = int(total_duration * self.fps)
        print(f"🎬 [ViralRenderer] Rendering {total_frames} frames ({total_duration:.2f}s) @ {self.fps} FPS ({self.width}x{self.height})")

        # Convert transients to frame indices for beat-reactive shakes
        transient_frames = set()
        if transient_timestamps:
            for t in transient_timestamps:
                if 0 <= t <= total_duration:
                    transient_frames.add(int(t * self.fps))

        # Check if input is image-based
        all_images = all(self._is_image(p) for p in raw_clips)
        cached_images = self._load_images_to_memory(raw_clips) if all_images else None

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

        clip_processes = []
        if not all_images:
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

        # Track shake frames
        shake_remaining = 0
        shake_magnitude = 0

        try:
            for frame_idx in range(total_frames):
                current_time = frame_idx / float(self.fps)

                # Check if cut transition hit
                if cut_idx < len(cut_timestamps) - 1:
                    if current_time >= cut_timestamps[cut_idx + 1]:
                        cut_idx += 1
                        if all_images:
                            current_clip_idx = (current_clip_idx + 1) % len(cached_images)
                        else:
                            current_clip_idx = (current_clip_idx + 1) % len(clip_processes)

                # Acquire base frame
                if all_images:
                    base_img = cached_images[current_clip_idx]
                    
                    # Calculate dynamic Ken Burns zoom within this shot
                    shot_start = cut_timestamps[cut_idx]
                    shot_end = cut_timestamps[cut_idx + 1] if cut_idx < len(cut_timestamps) - 1 else total_duration
                    shot_len = max(0.1, shot_end - shot_start)
                    progress = min(1.0, max(0.0, (current_time - shot_start) / shot_len))
                    
                    # Zoom factor: 1.00 to 1.05
                    zoom = 1.0 + 0.05 * progress
                    crop_w = int(self.width / zoom)
                    crop_h = int(self.height / zoom)
                    x1 = (self.width - crop_w) // 2
                    y1 = (self.height - crop_h) // 2
                    
                    cropped = base_img[y1:y1+crop_h, x1:x1+crop_w]
                    frame = fx_bridge.resize_bilinear(np.ascontiguousarray(cropped), self.width, self.height)
                else:
                    active_p = clip_processes[current_clip_idx]
                    raw_data = active_p.stdout.read(self.frame_bytes)
                    if not raw_data or len(raw_data) < self.frame_bytes:
                        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                    else:
                        frame = np.frombuffer(raw_data, dtype=np.uint8).reshape((self.height, self.width, 3)).copy()

                # --- TRIGGER AUDIO-REACTIVE SHAKES ---
                if enable_shake:
                    # Major Drop Impact Shake (Violent 24 frames)
                    if drop_frame_idx >= 0 and frame_idx == drop_frame_idx:
                        shake_remaining = 24
                        shake_magnitude = 22
                    # Transient Kick Shakes (Subtle 6 frames)
                    elif frame_idx in transient_frames:
                        shake_remaining = max(shake_remaining, 6)
                        shake_magnitude = max(shake_magnitude, 8)

                    if shake_remaining > 0:
                        decay = shake_remaining / 24.0
                        dx = int(random.uniform(-shake_magnitude, shake_magnitude) * decay)
                        dy = int(random.uniform(-shake_magnitude, shake_magnitude) * decay)
                        frame = fx_bridge.camera_shake(frame, dx=dx, dy=dy)
                        shake_remaining -= 1

                # --- WHITE IMPACT FLASH ON DROP ---
                if enable_flash and drop_frame_idx >= 0:
                    delta = frame_idx - drop_frame_idx
                    if 0 <= delta <= 12:  # 12 frames flash decay
                        flash_intensity = 0.95 * (1.0 - (delta / 12.0))
                        fx_bridge.white_flash(frame, intensity=flash_intensity)

                # --- RGB SPLIT / CHROMATIC ABERRATION ---
                if enable_rgb_split and drop_frame_idx >= 0:
                    delta = frame_idx - drop_frame_idx
                    if 0 <= delta <= 18:
                        shift_x = int(14 * (1.0 - (delta / 18.0)))
                        fx_bridge.rgb_split(frame, shift_x=shift_x)

                # --- PHONK CONTRAST & SATURATION COLOR GRADE ---
                if enable_color_grade:
                    fx_bridge.color_grade(frame, contrast=1.28, saturation=1.35, crush_black=12)

                # Stream processed frame to FFmpeg encoder
                proc.stdin.write(frame.tobytes())

        finally:
            proc.stdin.close()
            proc.wait()
            for p in clip_processes:
                try:
                    p.kill()
                except Exception:
                    pass

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError(f"Rendering failed. Output file is empty or missing: {output_path}")

        print(f"✅ [ViralRenderer] Successfully rendered: {output_path} ({os.path.getsize(output_path) / (1024*1024):.2f} MB)")
        return output_path
