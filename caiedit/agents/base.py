"""
Agent Base Classes and Pipeline Session Context
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class StudioSession:
    session_id: str
    user_prompt: str
    reference_audio: str = ""
    reference_video: str = ""
    raw_footage_paths: List[str] = field(default_factory=list)
    output_target: str = ""

    # Pipeline State
    style_preset: str = "car_phonk_edit"
    audio_analysis: Optional[Any] = None
    video_blueprint: Optional[Any] = None
    vfx_render_plan: Dict[str, Any] = field(default_factory=dict)
    rendered_video_path: str = ""
    qa_report: Dict[str, Any] = field(default_factory=dict)
    execution_logs: List[str] = field(default_factory=list)

    def log(self, agent_name: str, message: str):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{agent_name}] {message}"
        self.execution_logs.append(entry)
        print(entry)

class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def execute(self, session: StudioSession) -> None:
        raise NotImplementedError
