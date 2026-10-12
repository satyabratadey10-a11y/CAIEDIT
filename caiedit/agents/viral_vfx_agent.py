"""
Viral VFX Agent: Native Execution Engine
Executes compiled CAI-Lang timelines using the high-speed CAILangVM and C++ SIMD FX.
"""

import os
import subprocess
from caiedit.agents.base import BaseAgent, StudioSession
from caiedit.cailang.vm import CAILangVM

class ViralVFXAgent(BaseAgent):
    def __init__(self):
        super().__init__("ViralVFXAgent")

    def _detect_resolution(self, session: StudioSession) -> tuple:
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
        return 1080, 1080

    def execute(self, session: StudioSession) -> None:
        timeline = session.choreography_timeline
        if not timeline:
            raise RuntimeError("No compiled choreography timeline found in session.")

        width, height = self._detect_resolution(session)
        target_output = session.output_target or f"workspace/output/caiedit_{session.session_id}.mp4"
        os.makedirs(os.path.dirname(os.path.abspath(target_output)), exist_ok=True)

        session.log(self.name, f"⚡ Initializing CAI-Lang Virtual Machine ({width}x{height} @ 60 FPS)...")
        vm = CAILangVM(width=width, height=height, fps=60)

        session.log(self.name, f"🚀 Executing compiled timeline -> {target_output}")
        rendered_path = vm.execute(
            timeline=timeline,
            audio_path=session.reference_audio,
            output_path=target_output
        )

        session.rendered_video_path = rendered_path
        session.log(self.name, f"🎉 Render Complete: {rendered_path}")
