"""
Multi-Window Layout & Framing Compositor
Supports:
- Multi-Card Layouts: TRIPLE_CARD (3-card showcase), HERO_CARD (single floating frame), FULLSCREEN, DUAL_SPLIT
- Canvas Backgrounds: SOLID, BLURRED_BACKDROP
- Typography Overlays: MY BEST PHOTOCARD / Title Headers
- Modular Tool Tray: Particles, Camera Shakes, Flashes, RGB Glitch (all optional toggles!)
"""

import os
import subprocess
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from caiedit.bridge import fx_bridge

@dataclass
class WindowSlot:
    x: int
    y: int
    w: int
    h: int
    border_w: int = 3
    border_rgb: Tuple[int, int, int] = (255, 255, 255)
    shadow_radius: int = 15
    shadow_alpha: float = 0.65

@dataclass
class HeaderOverlay:
    text: str = "MY BEST PHOTOCARD"
    font_path: str = "/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf"
    font_size: int = 80
    y_pos: int = 140
    color: Tuple[int, int, int] = (255, 255, 255)
    shadow_color: Tuple[int, int, int] = (0, 0, 0)

@dataclass
class LayoutSpec:
    mode: str = "HERO_CARD"                 # 'TRIPLE_CARD', 'HERO_CARD', 'FULLSCREEN', 'DUAL_SPLIT'
    bg_mode: str = "SOLID"                  # 'SOLID', 'BLURRED_BACKDROP'
    bg_color: Tuple[int, int, int] = (0, 0, 0)  # Pure deep black
    header: Optional[HeaderOverlay] = None
    
    # Modular FX Tool Tray (Optional Toggles)
    enable_particles: bool = False          # Off by default! Only enabled if specified
    particle_count: int = 60
    enable_shake: bool = True
    enable_flash: bool = True
    enable_rgb_split: bool = True
    enable_color_grade: bool = True

class LayoutEngine:
    """Composites multi-window frames and overlays directly onto the render canvas."""

    def __init__(self, width: int = 1080, height: int = 1080):
        self.width = width
        self.height = height
        self._header_cache: Dict[str, np.ndarray] = {}

    def get_layout_slots(self, mode: str, hero_size: int = 780) -> List[WindowSlot]:
        """Calculates precise window slot geometries on canvas."""
        if mode == "TRIPLE_CARD":
            # 3 landscape cards side-by-side matching viral photocard edit templates
            card_w = 310
            card_h = 230
            gap = 35
            total_w = card_w * 3 + gap * 2
            start_x = (self.width - total_w) // 2
            center_y = (self.height - card_h) // 2 + 15

            return [
                WindowSlot(x=start_x + 0 * (card_w + gap), y=center_y, w=card_w, h=card_h, border_w=3),
                WindowSlot(x=start_x + 1 * (card_w + gap), y=center_y, w=card_w, h=card_h, border_w=3),
                WindowSlot(x=start_x + 2 * (card_w + gap), y=center_y, w=card_w, h=card_h, border_w=3)
            ]

        elif mode == "HERO_CARD":
            # Single centered floating photocard
            card_w = min(hero_size, self.width - 60)
            card_h = min(hero_size, self.height - 60)
            start_x = (self.width - card_w) // 2
            start_y = (self.height - card_h) // 2
            return [
                WindowSlot(x=start_x, y=start_y, w=card_w, h=card_h, border_w=3, shadow_radius=22, shadow_alpha=0.75)
            ]

        elif mode == "DUAL_SPLIT":
            card_w = (self.width - 80) // 2
            card_h = (self.height - 140)
            start_y = 70
            return [
                WindowSlot(x=30, y=start_y, w=card_w, h=card_h, border_w=2),
                WindowSlot(x=50 + card_w, y=start_y, w=card_w, h=card_h, border_w=2)
            ]

        else: # FULLSCREEN
            return [
                WindowSlot(x=0, y=0, w=self.width, h=self.height, border_w=0, shadow_radius=0, shadow_alpha=0.0)
            ]

    def render_header_mask(self, header: HeaderOverlay) -> np.ndarray:
        """Renders anti-aliased header typography with drop shadow into an RGBA mask."""
        key = f"{header.text}_{header.font_size}_{self.width}x{self.height}"
        if key in self._header_cache:
            return self._header_cache[key]

        font_arg = f":fontfile='{header.font_path}'" if os.path.exists(header.font_path) else ""
        escaped_text = header.text.replace("'", "\\'")

        # Render typography using FFmpeg drawtext into an RGBA raw stream
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "lavfi", "-i", f"color=c=black@0.0:s={self.width}x{self.height},format=rgba",
            "-vf", f"drawtext=text='{escaped_text}'{font_arg}:fontcolor=white:fontsize={header.font_size}:x=(w-text_w)/2:y={header.y_pos}:shadowcolor=black@0.7:shadowx=3:shadowy=3",
            "-vframes", "1", "-f", "rawvideo", "-pix_fmt", "rgba", "-"
        ]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw, _ = proc.communicate()
            if len(raw) >= self.width * self.height * 4:
                mask = np.frombuffer(raw[:self.width * self.height * 4], dtype=np.uint8).reshape((self.height, self.width, 4))
                self._header_cache[key] = mask
                return mask
        except Exception:
            pass

        # Blank fallback mask if drawtext fails
        blank = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        self._header_cache[key] = blank
        return blank

    def compose_frame(
        self,
        layout: LayoutSpec,
        card_images: List[np.ndarray],
        time_sec: float
    ) -> np.ndarray:
        """Composites canvas background, windows/photocards, and typography."""
        canvas = np.empty((self.height, self.width, 3), dtype=np.uint8)

        # 1. Canvas Background
        if layout.bg_mode == "BLURRED_BACKDROP" and card_images:
            fx_bridge.blur_backdrop(card_images[0], canvas, dim_factor=0.35)
        else: # SOLID
            r, g, b = layout.bg_color
            fx_bridge.fill_canvas(canvas, r, g, b)

        # 2. Window Slots (Cards)
        slots = self.get_layout_slots(layout.mode)
        for i, slot in enumerate(slots):
            img = card_images[i % len(card_images)]
            fx_bridge.blit_card_window(
                card_img=img,
                canvas=canvas,
                dst_x=slot.x,
                dst_y=slot.y,
                dst_w=slot.w,
                dst_h=slot.h,
                border_w=slot.border_w,
                border_rgb=slot.border_rgb,
                shadow_radius=slot.shadow_radius,
                shadow_alpha=slot.shadow_alpha
            )

        # 3. Typography Overlay (Header)
        if layout.header:
            mask = self.render_header_mask(layout.header)
            # Alpha blend text over canvas
            alpha = mask[:, :, 3:4].astype(np.float32) / 255.0
            text_rgb = mask[:, :, :3]
            canvas[:] = (canvas * (1.0 - alpha) + text_rgb * alpha).astype(np.uint8)

        # 4. MODULAR TOOL: Particles (ONLY if enabled by user/editor!)
        if layout.enable_particles:
            fx_bridge.render_particles(canvas, time_sec=time_sec, count=layout.particle_count)

        return canvas
