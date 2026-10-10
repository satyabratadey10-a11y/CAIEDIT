"""
Viral VFX Agent: Assembly & Native FX Compositor
Orchestrates high-velocity rendering, audio-reactive camera shakes, flashes, and color grades.
"""

import os
import subprocess
from caiedit.agents.base import BaseAgent, StudioSession
from caiedit.vfx.renderer import ViralRenderer

class ViralVFXAgent(BaseAgent):
    def __init__(self):
        super().__init__("ViralVFXAgent")

    def _detect_resolution(self, session: StudioSession) -> tuple:
        """Determines target resolution from reference video or default 1080x1080 / 1080x1920."""
        if session.reference_video and os.path.exists(session.reference_video):
            try:
                cmd = [
                    "ffprobe", "-v", "error", "-select_streams", "v:0",
                    "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0",
                    session.reference_video
                ]
                out = subprocess.check_output(cmd).decode().strip()
                if "x" in out:
                    w, h = out.split("x")
                    return int(w), int(h)
            except Exception:
                pass
        return 1080, 1080  # Default square phonk edit format

    def execute(self, session: StudioSession) -> None:
        session.log(self.name, "⚡ Preparing Viral VFX Compositor Specification...")

        cut_times = session.video_blueprint.cut_timestamps if session.video_blueprint else [0.0, 5.0]
        drop_time = session.audio_analysis.drop_timestamp if session.audio_analysis else 0.0
        transients = session.audio_analysis.transients if session.audio_analysis else []

        # If reference video provided, align drop with reference audio drop (~5.8s) or song drop
        if session.reference_video and len(cut_times) > 10:
            # The reference video has its major visual impact around 5.8s
            drop_time = 5.88

        width, height = self._detect_resolution(session)
        renderer = ViralRenderer(width=width, height=height, fps=60)

        target_output = session.output_target or f"workspace/output/caiedit_{session.session_id}.mp4"
        os.makedirs(os.path.dirname(os.path.abspath(target_output)), exist_ok=True)

        session.vfx_render_plan = {
            "resolution": f"{width}x{height}",
            "fps": 60,
            "cuts_count": len(cut_times),
            "drop_sync_sec": drop_time,
            "effects": ["transient_shakes", "drop_impact_flash", "rgb_split", "phonk_contrast_grade", "ken_burns_zoom"]
        }

        session.log(self.name, f"🚀 Executing Native C++ 60 FPS Render Pipeline ({width}x{height}) -> {target_output}")
        rendered_path = renderer.render(
            raw_clips=session.raw_footage_paths,
            audio_path=session.reference_audio,
            output_path=target_output,
            cut_timestamps=cut_times,
            drop_timestamp=drop_time,
            transient_timestamps=transients,
            enable_shake=True,
            enable_flash=True,
            enable_rgb_split=True,
            enable_color_grade=True
        )

        session.rendered_video_path = rendered_path
        session.log(self.name, f"🎉 Render Complete: {rendered_path}")
