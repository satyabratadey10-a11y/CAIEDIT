"""
Optic Agent: Visual Perception & Cut Reverse-Engineering ("The Eye")
Examines visual assets, classifies shot roles, and maps cuts from reference videos.
"""

import os
from caiedit.agents.base import BaseAgent, StudioSession
from caiedit.vision.semantic_eye import SemanticEye
from caiedit.vision.analyzer import VisionAnalyzer, VideoBlueprint

class OpticAgent(BaseAgent):
    def __init__(self):
        super().__init__("OpticAgent")
        self.eye = SemanticEye()
        self.analyzer = VisionAnalyzer()

    def execute(self, session: StudioSession) -> None:
        # 1. "SEEING" THE ASSETS
        if session.raw_footage_paths:
            session.log(self.name, f"👁️ Activating Semantic Eye on {len(session.raw_footage_paths)} visual assets...")
            assets = self.eye.inspect_assets(session.raw_footage_paths)
            session.visual_assets = assets
            
            # Log classification breakdown
            roles = {}
            for a in assets:
                roles[a.role] = roles.get(a.role, 0) + 1
            session.log(self.name, f"🎨 Asset Perception: {roles}")
            money_shots = [os.path.basename(a.path) for a in assets if a.role == "MONEY_SHOT"]
            session.log(self.name, f"🏆 Designated Drop Money Shot: {money_shots[0] if money_shots else 'Auto'}")

        # 2. REVERSE-ENGINEERING REFERENCE VIDEO
        if session.reference_video and os.path.exists(session.reference_video):
            session.log(self.name, f"👁️ Reverse-engineering viral reference video: {os.path.basename(session.reference_video)}")
            blueprint = self.analyzer.analyze_reference(session.reference_video)
            session.video_blueprint = blueprint
            session.log(self.name, f"📊 Reference Cuts Mapped: {len(blueprint.cut_timestamps)} cuts (Avg shot: {blueprint.average_shot_duration}s)")
            session.log(self.name, f"🔥 Reference Style: [{blueprint.detected_style}]")
        else:
            session.video_blueprint = None
