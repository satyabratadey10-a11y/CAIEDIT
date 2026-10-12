"""
CAI-Lang Script Synthesizer
Generates expressive CAI-Lang choreography scripts by fusing musical perception and visual assets.
"""

from caiedit.audio.engine import AudioAnalysis
from caiedit.vision.semantic_eye import VisualAsset
from typing import List

class CAILangSynthesizer:
    """The Creative Director that writes CAI-Lang choreography programs."""

    def compose_script(self, audio: AudioAnalysis, assets: List[VisualAsset], ref_drop: float = 5.88) -> str:
        """Writes an expressive CAI-Lang script tailored to this specific song and assets."""
        drop_time = ref_drop if ref_drop > 0 else audio.drop_timestamp

        buildup_start = max(1.2, drop_time - 3.2)
        fakeout_start = max(buildup_start, drop_time - 0.28)
        drop_end = min(audio.duration_sec, drop_time + 12.0)
        total_end = min(audio.duration_sec, 25.6)

        script = f"""# CAIEDIT Choreography Script (.cai)
# Generated autonomously via Perceptual Ear & Eye Synthesis

track "Montagem Phonk Masterpiece" {{
    tempo: {audio.bpm};
    drop: {drop_time:.2f}s;
    duration: {total_end:.2f}s;
    mood: "aggressive_phonk_velocity";
}}

choreography {{
    phase INTRO [0.00s -> {buildup_start:.2f}s] {{
        visual_role: ATMOSPHERIC;
        motion: ken_burns(zoom: push_in, speed: 0.03);
        color: moody_vignette(depth: 0.25);
        pace: atmospheric_bars(bars: 2);
    }}

    phase BUILDUP [{buildup_start:.2f}s -> {fakeout_start:.2f}s] {{
        visual_role: DETAIL_TEASE;
        motion: accelerating_pan(speed: 0.08);
        pace: snare_roll_density();
        tension: rising_exposure();
    }}

    phase FAKEOUT [{fakeout_start:.2f}s -> {drop_time:.2f}s] {{
        visual_role: DETAIL_TEASE;
        motion: freeze_breath();
        fx: pre_drop_silence();
    }}

    phase DROP [{drop_time:.2f}s -> {drop_end:.2f}s] {{
        visual_role: MONEY_SHOT;
        impact: white_flash(intensity: 0.95);
        motion: bass_shockwave(shake: 24, decay: 0.35);
        fx: chromatic_glitch(decay: 0.18);
        color: crushed_phonk_contrast(contrast: 1.35, saturation: 1.4);
        pace: sync_downbeats();
    }}

    phase GROOVE [{drop_end:.2f}s -> {total_end:.2f}s] {{
        visual_role: ACTION_FLOW;
        motion: rhythmic_pulse(speed: 0.04);
        color: neon_boost(contrast: 1.25, saturation: 1.3);
        pace: melodic_phrases();
    }}
}}
"""
        return script
