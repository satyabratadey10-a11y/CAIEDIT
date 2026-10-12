"""
Sonic Agent: Perceptual Music Intelligence ("The Ear")
Dissects the song's musical soul: multi-band instruments, melody contours, and narrative phases.
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
            session.log(self.name, "⚠️ No valid reference audio found.")
            return

        session.log(self.name, f"🎧 Hearing & dissecting musical arc: {os.path.basename(session.reference_audio)}")
        analysis = self.engine.analyze(session.reference_audio)
        session.audio_analysis = analysis

        session.log(self.name, f"🎵 Tempo: {analysis.bpm} BPM | Duration: {analysis.duration_sec:.2f}s")
        session.log(self.name, f"💥 Detected Musical Drop Climax at: {analysis.drop_timestamp:.2f}s")
        session.log(self.name, f"🎹 Melodic Synthesizer/Lead Onsets: {len(analysis.melodic_onsets)} triggers")
        session.log(self.name, f"🥁 Sub-Bass / 808 Kick Transients: {len(analysis.percussive_onsets)} triggers")
        
        # Log detected narrative phases
        phase_names = [f"{p.name} ({p.start_sec:.1f}s-{p.end_sec:.1f}s)" for p in analysis.phases]
        session.log(self.name, f"🎼 Musical Narrative Arc: {' ➔ '.join(phase_names)}")
