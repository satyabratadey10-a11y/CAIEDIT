"""
Director Agent: The Executive Planner & Orchestrator
Parses user intent, assigns style presets, and creates the execution DAG.
"""

from caiedit.agents.base import BaseAgent, StudioSession

class DirectorAgent(BaseAgent):
    def __init__(self):
        super().__init__("DirectorAgent")

    def execute(self, session: StudioSession) -> None:
        session.log(self.name, f"🎬 Analyzing project request: '{session.user_prompt}'")
        
        prompt_lower = session.user_prompt.lower()
        if "anime" in prompt_lower:
            session.style_preset = "anime_amv_velocity"
        elif "car" in prompt_lower or "drift" in prompt_lower or "phonk" in prompt_lower:
            session.style_preset = "car_phonk_velocity"
        else:
            session.style_preset = "high_impact_sync"

        session.log(self.name, f"⚡ Selected Visual Architecture: [{session.style_preset}]")
        session.log(self.name, "📋 Execution DAG created: [SonicAgent -> OpticAgent -> ViralVFXAgent -> QAPolishAgent]")
