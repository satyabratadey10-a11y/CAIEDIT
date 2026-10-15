"""
CAI-Lang Virtual Machine (Execution Runtime)
Executes a ChoreographyTimeline frame-by-frame with native C++ SIMD acceleration.
Integrates Multi-Window Layouts (TRIPLE_CARD, HERO_CARD, FULLSCREEN), Typography Headers,
and Modular Tool Tray (Particles, Shakes, Flashes).
"""

import os
import random
import subprocess
import numpy as np
from typing import Dict, List
from caiedit.cailang.compiler import ChoreographyTimeline, ShotPlan
from caiedit.vfx.layout_engine import LayoutEngine, LayoutSpec, HeaderOverlay
from caiedit.bridge import fx_bridge

class CAILangVM:
    """High-speed execution runtime for compiled CAI-Lang timelines."""

    def __init__(self, width: int = 1080, height: int = 1080, fps: int = 60):
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_bytes = width * height * 3
        self._image_cache: Dict[str, np.ndarray] = {}
        self.layout_engine = LayoutEngine(width=width, height=height)

    def _get_image(self, path: str) -> np.ndarray:
        """Loads and pre-scales an image into memory, caching it for instant re-use."""
        if path in self._image_cache:
            return self._image_cache[path]

        cmd = [
            "ffmpeg", "-v", "error", "-i", path,
            "-vf", f"scale={self.width}:{self.height}:force_original_aspect_ratio=increase,crop={self.width}:{self.height}",
            "-f", "rawvideo", "-pix_fmt", "bgr24", "-"
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        raw, _ = proc.communicate()
        if len(raw) < self.frame_bytes:
            raise RuntimeError(f"Failed to decode image buffer: {path}")

        arr = np.frombuffer(raw[:self.frame_bytes], dtype=np.uint8).reshape((self.height, self.width, 3))
        self._image_cache[path] = arr
        return arr

    def execute(
        self,
        timeline: ChoreographyTimeline,
        audio_path: str,
        output_path: str
    ) -> str:
        """Renders the compiled timeline into final video."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        total_frames = int(timeline.total_duration * self.fps)
        print(f"⚡ [CAILangVM] Executing timeline: {len(timeline.shots)} choreographed shots ({total_frames} frames @ {self.fps} FPS)")

        # Prepare FFmpeg encoder
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "rawvideo", "-pix_fmt", "bgr24",
            "-s", f"{self.width}x{self.height}",
            "-r", str(self.fps),
            "-i", "-",  # Video pipe from stdin
            "-i", audio_path,  # Audio track
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(timeline.total_duration),
            output_path
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        shot_idx = 0
        current_shot = timeline.shots[0] if timeline.shots else None

        active_shake_frames = 0
        active_shake_mag = 0
        active_flash_frames = 0
        active_flash_intensity = 0.0
        active_rgb_frames = 0
        active_rgb_shift = 0

        try:
            for frame_idx in range(total_frames):
                current_time = frame_idx / float(self.fps)

                # Check if current shot ended
                if current_shot and current_time >= current_shot.end_sec and shot_idx < len(timeline.shots) - 1:
                    shot_idx += 1
                    current_shot = timeline.shots[shot_idx]

                    # Trigger shot entry FX
                    if current_shot.shake_intensity > 0:
                        active_shake_mag = current_shot.shake_intensity
                        active_shake_frames = current_shot.shake_decay_frames
                    if current_shot.flash_intensity > 0:
                        active_flash_intensity = current_shot.flash_intensity
                        active_flash_frames = 12
                    if current_shot.rgb_split_shift > 0:
                        active_rgb_shift = current_shot.rgb_split_shift
                        active_rgb_frames = 16

                if not current_shot:
                    break

                # Prepare card images for this shot
                card_paths = current_shot.card_assets or [current_shot.asset_path]
                card_images = [self._get_image(p) for p in card_paths]

                # Dynamic Ken Burns Zoom on primary card
                shot_progress = min(1.0, max(0.0, (current_time - current_shot.start_sec) / max(0.05, current_shot.duration_sec)))
                zoom = current_shot.zoom_start + (current_shot.zoom_end - current_shot.zoom_start) * shot_progress
                if zoom > 1.001:
                    base_primary = card_images[0]
                    crop_w = int(self.width / zoom)
                    crop_h = int(self.height / zoom)
                    x1 = (self.width - crop_w) // 2
                    y1 = (self.height - crop_h) // 2
                    cropped = base_primary[y1:y1+crop_h, x1:x1+crop_w]
                    card_images[0] = fx_bridge.resize_bilinear(np.ascontiguousarray(cropped), self.width, self.height)

                # Build Layout Specification
                header_overlay = None
                if current_shot.header_text:
                    header_overlay = HeaderOverlay(text=current_shot.header_text)

                layout_spec = LayoutSpec(
                    mode=current_shot.layout_mode,
                    bg_mode=current_shot.bg_mode,
                    header=header_overlay,
                    enable_particles=current_shot.enable_particles,  # Optional tool!
                    particle_count=60
                )

                # 1. Compose Multi-Window Frame Canvas
                frame = self.layout_engine.compose_frame(layout_spec, card_images, time_sec=current_time)

                # 2. Apply Camera Shake (on Canvas)
                if active_shake_frames > 0:
                    decay = active_shake_frames / float(max(1, current_shot.shake_decay_frames))
                    dx = int(random.uniform(-active_shake_mag, active_shake_mag) * decay)
                    dy = int(random.uniform(-active_shake_mag, active_shake_mag) * decay)
                    frame = fx_bridge.camera_shake(frame, dx=dx, dy=dy)
                    active_shake_frames -= 1

                # 3. Apply White Flash Impact
                if active_flash_frames > 0:
                    decay = active_flash_frames / 12.0
                    intensity = active_flash_intensity * decay
                    fx_bridge.white_flash(frame, intensity=intensity)
                    active_flash_frames -= 1

                # 4. Apply RGB Chromatic Glitch
                if active_rgb_frames > 0:
                    decay = active_rgb_frames / 16.0
                    shift = int(active_rgb_shift * decay)
                    fx_bridge.rgb_split(frame, shift_x=shift)
                    active_rgb_frames -= 1

                # 5. Apply Phonk Contrast & Saturation Color Grade
                fx_bridge.color_grade(
                    frame,
                    contrast=current_shot.contrast,
                    saturation=current_shot.saturation,
                    crush_black=current_shot.crush_black
                )

                proc.stdin.write(frame.tobytes())

        finally:
            proc.stdin.close()
            proc.wait()

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError(f"Rendering failed: {output_path}")

        print(f"✅ [CAILangVM] Render Complete: {output_path} ({os.path.getsize(output_path) / (1024*1024):.2f} MB)")
        return output_path
