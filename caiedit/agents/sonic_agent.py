"""
Sonic Agent: Music Intelligence & Beat Alignment
Dissects reference audio, tracks kicks, BPM, and climax drop points.
"""

import os
from caiedit.agents.base import BaseAgent, StudioSession
from caiedit.audio.engine import AudioEngine

class SonicAgent(BaseAgent):
    def __init__(self):
        super().__init__("SonicAgent")
        self.engine = AudioEngine()

    def execute(self, session: StudioSession) -> None:
        if not session.reference_audio or not os.path.exists(session.reference_audio):
            session.log(self.name, "⚠️ No valid reference audio found. Generating fallback rhythm.")
            return

        session.log(self.name, f"🎧 Dissecting reference audio: {os.path.basename(session.reference_audio)}")
        analysis = self.engine.analyze(session.reference_audio)
        session.audio_analysis = analysis

        session.log(self.name, f"🎵 Detected BPM: {analysis.bpm} | Duration: {analysis.duration_sec:.2f}s")
        session.log(self.name, f"💥 Detected Primary Bass Drop at: {analysis.drop_timestamp:.2f}s")
        session.log(self.name, f"🎯 Found {len(analysis.transients)} kick/bass transients for cut synchronization.")
