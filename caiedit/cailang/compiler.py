"""
CAI-Lang Compiler
Compiles CAI-Lang AST + Audio Perception + Visual Assets into an executable timeline graph.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from caiedit.cailang.ast_nodes import ProgramNode, PhaseNode, DirectiveNode
from caiedit.audio.engine import AudioAnalysis
from caiedit.vision.semantic_eye import VisualAsset

@dataclass
class ShotPlan:
    start_sec: float
    end_sec: float
    duration_sec: float
    asset_path: str
    phase_name: str
    zoom_start: float = 1.0
    zoom_end: float = 1.05
    shake_intensity: int = 0
    shake_decay_frames: int = 0
    flash_intensity: float = 0.0
    rgb_split_shift: int = 0
    contrast: float = 1.25
    saturation: float = 1.35
    crush_black: int = 12

@dataclass
class ChoreographyTimeline:
    total_duration: float
    shots: List[ShotPlan] = field(default_factory=list)
    drop_time: float = 0.0

class Compiler:
    def __init__(self, fps: int = 60):
        self.fps = fps

    def compile(
        self,
        ast: ProgramNode,
        audio: AudioAnalysis,
        assets: List[VisualAsset],
        ref_cut_timestamps: Optional[List[float]] = None
    ) -> ChoreographyTimeline:
        """Binds the music's soul (Ear) to the visual assets (Eye) according to the CAI-Lang script."""
        shots = []
        total_duration = min(audio.duration_sec, 26.0)  # Standard viral short duration

        # Organize assets by role
        role_map = {
            "MONEY_SHOT": [a for a in assets if a.role == "MONEY_SHOT"],
            "DETAIL_TEASE": [a for a in assets if a.role == "DETAIL_TEASE"],
            "ATMOSPHERIC": [a for a in assets if a.role == "ATMOSPHERIC"],
            "ACTION_FLOW": [a for a in assets if a.role == "ACTION_FLOW"],
        }
        # Fallbacks if a role is empty
        for r, lst in role_map.items():
            if not lst:
                role_map[r] = assets

        asset_indices = {r: 0 for r in role_map}

        def pick_asset(role: str) -> str:
            pool = role_map.get(role, assets)
            idx = asset_indices[role] % len(pool)
            asset_indices[role] += 1
            return pool[idx].path

        # Iterate over phases defined in the CAI-Lang AST
        for phase in ast.phases:
            p_start = phase.start_sec
            p_end = min(phase.end_sec, total_duration)
            if p_start >= total_duration:
                break

            # Find phase directives
            target_role = "ACTION_FLOW"
            shake_amt = 0
            flash_amt = 0.0
            rgb_amt = 0
            zoom_speed = 0.04

            for d in phase.directives:
                if d.name == "visual_role":
                    target_role = d.action
                elif d.name == "motion" and "shake" in d.args:
                    shake_amt = int(d.args.get("shake", 0))
                elif d.name == "impact" and "intensity" in d.args:
                    flash_amt = float(d.args.get("intensity", 0.0))
                elif d.name == "fx" and "decay" in d.args:
                    rgb_amt = 12

            # Use reference cuts or rhythmic subdivisions within this phase
            phase_cuts = []
            if ref_cut_timestamps:
                phase_cuts = [t for t in ref_cut_timestamps if p_start <= t <= p_end]

            if not phase_cuts or len(phase_cuts) < 2:
                # Subdivide by rhythm
                if phase.name == "INTRO":
                    step = 1.6  # Slow cinematic breathing
                elif phase.name == "BUILDUP":
                    step = 0.35 # Fast accelerating cuts
                elif phase.name == "FAKEOUT":
                    step = max(0.08, p_end - p_start)
                elif phase.name == "DROP":
                    step = 0.38 # 160 BPM / 95 BPM groove cuts
                else:
                    step = 0.55
                
                curr = p_start
                while curr < p_end:
                    phase_cuts.append(round(curr, 2))
                    curr += step
                phase_cuts.append(round(p_end, 2))

            if phase_cuts[0] > p_start:
                phase_cuts.insert(0, p_start)

            # Generate individual shots
            for i in range(len(phase_cuts) - 1):
                s_start = phase_cuts[i]
                s_end = phase_cuts[i + 1]
                duration = s_end - s_start
                if duration <= 0.03:
                    continue

                shot_asset = pick_asset(target_role)

                # Special FX triggers
                shot_flash = flash_amt if i == 0 and phase.name == "DROP" else 0.0
                shot_shake = shake_amt if i == 0 and phase.name == "DROP" else (8 if phase.name == "DROP" else 0)
                shot_rgb = rgb_amt if i == 0 and phase.name == "DROP" else 0

                shots.append(ShotPlan(
                    start_sec=s_start,
                    end_sec=s_end,
                    duration_sec=duration,
                    asset_path=shot_asset,
                    phase_name=phase.name,
                    zoom_start=1.0,
                    zoom_end=1.0 + zoom_speed,
                    shake_intensity=shot_shake,
                    shake_decay_frames=20 if shot_shake > 15 else 8,
                    flash_intensity=shot_flash,
                    rgb_split_shift=shot_rgb,
                    contrast=1.35 if phase.name == "DROP" else 1.2,
                    saturation=1.4 if phase.name == "DROP" else 1.25,
                    crush_black=16 if phase.name == "DROP" else 10
                ))

        drop_time = audio.drop_timestamp
        if ref_cut_timestamps and any(t for t in ref_cut_timestamps if 5.5 <= t <= 6.5):
            drop_time = 5.88

        return ChoreographyTimeline(
            total_duration=total_duration,
            shots=shots,
            drop_time=drop_time
        )
