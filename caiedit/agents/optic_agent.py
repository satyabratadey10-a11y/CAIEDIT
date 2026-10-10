"""
Optic Agent: Video Reverse-Engineering & Cut Mapping
Ingests viral reference videos or synthesizes dynamic cut pacing based on audio transients.
"""

import os
from caiedit.agents.base import BaseAgent, StudioSession
from caiedit.vision.analyzer import VisionAnalyzer, VideoBlueprint

class OpticAgent(BaseAgent):
    def __init__(self):
        super().__init__("OpticAgent")
        self.analyzer = VisionAnalyzer()

    def execute(self, session: StudioSession) -> None:
        if session.reference_video and os.path.exists(session.reference_video):
            session.log(self.name, f"👁️ Reverse-engineering viral reference video: {os.path.basename(session.reference_video)}")
            blueprint = self.analyzer.analyze_reference(session.reference_video)
            session.video_blueprint = blueprint
            session.log(self.name, f"📊 Extracted {len(blueprint.cut_timestamps)} scene cuts (Avg shot: {blueprint.average_shot_duration}s)")
            session.log(self.name, f"🔥 Detected Viral Pacing Style: [{blueprint.detected_style}]")
        else:
            session.log(self.name, "👁️ No reference video provided. Synthesizing cut map aligned with audio rhythm.")
            # Synthesize cut map from audio analysis
            if session.audio_analysis and session.audio_analysis.transients:
                transients = session.audio_analysis.transients
                # Select cuts every 2nd or 3rd kick for dynamic pacing
                step = 2 if session.style_preset == "car_phonk_velocity" else 3
                cuts = [0.0] + transients[::step]
                cuts = [round(c, 2) for c in cuts if c > 0.0]
                if 0.0 not in cuts:
                    cuts.insert(0, 0.0)
            else:
                cuts = [0.0, 1.2, 2.4, 3.6, 4.8, 6.0, 7.2, 8.4, 9.6]

            session.video_blueprint = VideoBlueprint(
                duration_sec=session.audio_analysis.duration_sec if session.audio_analysis else 10.0,
                cut_timestamps=cuts,
                cut_intervals=[round(cuts[i+1] - cuts[i], 2) for i in range(len(cuts)-1)],
                average_shot_duration=round(sum([cuts[i+1] - cuts[i] for i in range(len(cuts)-1)]) / max(1, len(cuts)-1), 2),
                motion_energy=[],
                detected_style=session.style_preset
            )
            session.log(self.name, f"📐 Generated {len(cuts)} beat-synced cut anchors.")
