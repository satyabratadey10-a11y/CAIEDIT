"""
Director Agent: The Master Choreographer & CAI-Lang Synthesizer
Composes executable CAI-Lang programs fusing the Ear's musical perception and the Eye's visual assets.
"""

import os
from caiedit.agents.base import BaseAgent, StudioSession
from caiedit.cailang.synthesizer import CAILangSynthesizer
from caiedit.cailang.lexer import Lexer
from caiedit.cailang.parser import Parser
from caiedit.cailang.compiler import Compiler

class DirectorAgent(BaseAgent):
    def __init__(self):
        super().__init__("DirectorAgent")
        self.synthesizer = CAILangSynthesizer()
        self.compiler = Compiler()

    def execute(self, session: StudioSession) -> None:
        session.log(self.name, f"🎬 Directing project: '{session.user_prompt}'")
        session.log(self.name, "🧠 Fusing Musical Perception (Ear) + Visual Perception (Eye)...")

        # Determine reference drop if reference video was provided
        ref_drop = 5.88 if session.reference_video and session.video_blueprint else 0.0

        # 1. Synthesize CAI-Lang Script
        cai_script = self.synthesizer.compose_script(
            audio=session.audio_analysis,
            assets=session.visual_assets,
            ref_drop=ref_drop,
            header_text=session.header_text,
            enable_particles=session.enable_particles
        )
        session.cailang_script = cai_script

        # Save script to disk for transparency & user inspection
        cai_file = os.path.join("workspace", "choreography.cai")
        os.makedirs("workspace", exist_ok=True)
        with open(cai_file, "w", encoding="utf-8") as f:
            f.write(cai_script)
        session.log(self.name, f"📝 Composed CAI-Lang Program: {cai_file}")

        # 2. Tokenize & Parse CAI-Lang Script into AST
        lexer = Lexer(cai_script)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        # 3. Compile AST into Choreography Timeline
        ref_cuts = session.video_blueprint.cut_timestamps if session.video_blueprint else None
        timeline = self.compiler.compile(
            ast=ast,
            audio=session.audio_analysis,
            assets=session.visual_assets,
            ref_cut_timestamps=ref_cuts
        )
        session.choreography_timeline = timeline
        session.log(self.name, f"📐 Compiled Choreography Timeline: {len(timeline.shots)} synchronized shots across {len(ast.phases)} phases")
