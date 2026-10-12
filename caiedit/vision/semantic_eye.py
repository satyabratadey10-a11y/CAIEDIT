"""
Semantic Vision Engine ("The Eye")
Perceives, scores, and classifies visual assets:
- Edge gradient sharpness & detail frequency
- Dynamic range, black depth & lighting punch
- Assigns semantic roles: MONEY_SHOT, ATMOSPHERIC, DETAIL_TEASE, ACTION_FLOW
- Ensures the most aggressive shots hit on the musical drops!
"""

import os
import subprocess
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class VisualAsset:
    path: str
    role: str                # 'MONEY_SHOT', 'ATMOSPHERIC', 'DETAIL_TEASE', 'ACTION_FLOW'
    punch_score: float       # [0.0 - 10.0] visual aggression / impact factor
    contrast: float          # dynamic range ratio
    sharpness: float         # edge frequency
    dark_ratio: float        # phonk shadow ratio

class SemanticEye:
    """Analyzes visual resources so CAIEDIT can 'see' and curate shots intelligently."""

    def __init__(self, sample_size: int = 360):
        self.sample_size = sample_size

    def inspect_assets(self, asset_paths: List[str]) -> List[VisualAsset]:
        """Examines every image/clip and returns a prioritized, categorized list."""
        analyzed = []
        print(f"👁️ [SemanticEye] Inspecting {len(asset_paths)} visual assets...")

        for p in asset_paths:
            if not os.path.exists(p):
                continue

            # Load a small downsampled thumbnail for lightning fast inspection
            cmd = [
                "ffmpeg", "-v", "error", "-i", p,
                "-vf", f"scale={self.sample_size}:{self.sample_size}:force_original_aspect_ratio=increase,crop={self.sample_size}:{self.sample_size}",
                "-vframes", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"
            ]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw, _ = proc.communicate()

            if len(raw) < self.sample_size * self.sample_size:
                # Fallback neutral score
                analyzed.append(VisualAsset(p, "ACTION_FLOW", 5.0, 1.0, 1.0, 0.5))
                continue

            img = np.frombuffer(raw[:self.sample_size * self.sample_size], dtype=np.uint8).reshape((self.sample_size, self.sample_size)).astype(np.float32)

            # 1. Edge sharpness via discrete Laplacian gradient proxy
            diff_y = np.abs(np.diff(img, axis=0))
            diff_x = np.abs(np.diff(img, axis=1))
            sharpness = float((np.mean(diff_y) + np.mean(diff_x)) / 2.0)

            # 2. Dynamic range & contrast (standard deviation of luminosity)
            contrast = float(np.std(img))

            # 3. Shadow / dark moody ratio (< 40 luminosity)
            dark_ratio = float(np.sum(img < 40) / img.size)

            # 4. Overall Visual Punch Score (0.0 to 10.0)
            # High punch = sharp edges + punchy contrast + moody phonk darkness
            punch = (sharpness * 0.25) + (contrast * 0.08) + (dark_ratio * 4.0)
            punch = round(min(10.0, max(1.0, punch)), 2)

            # 5. Role Classification
            if punch >= 7.2:
                role = "MONEY_SHOT"      # Peak impact for the drops!
            elif sharpness > 18.0 and dark_ratio > 0.3:
                role = "DETAIL_TEASE"    # Aggressive details for buildups
            elif dark_ratio < 0.25 or contrast < 45.0:
                role = "ATMOSPHERIC"     # Wide / airy for intros & outros
            else:
                role = "ACTION_FLOW"     # Rhythmic flow for verses & grooves

            analyzed.append(VisualAsset(p, role, punch, round(contrast, 2), round(sharpness, 2), round(dark_ratio, 2)))

        # Sort by punch score descending
        analyzed.sort(key=lambda x: x.punch_score, reverse=True)

        # Ensure at least one MONEY_SHOT exists
        if not any(a.role == "MONEY_SHOT" for a in analyzed) and analyzed:
            analyzed[0].role = "MONEY_SHOT"

        # Summary telemetry
        roles_count = {}
        for a in analyzed:
            roles_count[a.role] = roles_count.get(a.role, 0) + 1
        print(f"👁️ [SemanticEye] Classified assets: {roles_count}")

        return analyzed
