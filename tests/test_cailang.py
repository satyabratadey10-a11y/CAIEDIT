"""
Unit Test for CAI-Lang Lexer, Parser, and Compiler
"""

from caiedit.cailang.tokens import TokenType
from caiedit.cailang.lexer import Lexer
from caiedit.cailang.parser import Parser
from caiedit.cailang.compiler import Compiler
from caiedit.audio.engine import AudioAnalysis, SongPhase
from caiedit.vision.semantic_eye import VisualAsset

def test_cailang_pipeline():
    sample_script = """
    track "Test Drift Phonk" {
        tempo: 160.0;
        mood: "aggressive";
    }

    choreography {
        phase INTRO [0.00s -> 2.50s] {
            visual_role: ATMOSPHERIC;
            motion: ken_burns(zoom: push_in, speed: 0.03);
            color: moody_vignette(depth: 0.25);
            pace: atmospheric_bars(bars: 2);
        }

        phase DROP [2.50s -> 6.00s] {
            visual_role: MONEY_SHOT;
            impact: white_flash(intensity: 0.95);
            motion: bass_shockwave(shake: 24, decay: 0.35);
            fx: chromatic_glitch(decay: 0.18);
            color: crushed_phonk(contrast: 1.35, saturation: 1.4);
            pace: sync_downbeats();
        }
    }
    """

    print("--- 1. Testing CAI-Lang Lexer ---")
    lexer = Lexer(sample_script)
    tokens = lexer.tokenize()
    print(f"✅ Tokenized {len(tokens)} tokens successfully.")
    assert any(t.type == TokenType.TRACK for t in tokens)
    assert any(t.type == TokenType.CHOREOGRAPHY for t in tokens)

    print("--- 2. Testing CAI-Lang Parser ---")
    parser = Parser(tokens)
    ast = parser.parse()
    print(f"✅ Parsed AST: Track '{ast.track_title}' with {len(ast.phases)} phases.")
    assert len(ast.phases) == 2
    assert ast.phases[0].name == "INTRO"
    assert ast.phases[1].name == "DROP"

    print("--- 3. Testing CAI-Lang Compiler ---")
    dummy_audio = AudioAnalysis(
        duration_sec=6.0,
        sample_rate=44100,
        bpm=160.0,
        phases=[SongPhase("INTRO", 0.0, 2.5, 0.3, 0.2, "ambient"), SongPhase("DROP", 2.5, 6.0, 1.0, 0.8, "808")],
        melodic_onsets=[1.0, 2.0, 3.0],
        percussive_onsets=[0.5, 1.5, 2.5, 3.5, 4.5, 5.5],
        snare_onsets=[1.0, 2.0, 3.0],
        drop_timestamp=2.5,
        tension_curve=[0.2, 0.5, 0.9, 0.7],
        sub_energy_curve=[0.1, 0.2, 1.0, 0.8],
        synth_energy_curve=[0.3, 0.8, 0.5, 0.4],
        hop_sec=512/44100
    )
    dummy_assets = [
        VisualAsset("img_money.jpg", "MONEY_SHOT", 9.5, 1.5, 20.0, 0.6),
        VisualAsset("img_atmos.jpg", "ATMOSPHERIC", 4.2, 1.0, 8.0, 0.2)
    ]

    compiler = Compiler()
    timeline = compiler.compile(ast, dummy_audio, dummy_assets)
    print(f"✅ Compiled Timeline: {len(timeline.shots)} synchronized shots.")
    assert len(timeline.shots) > 0
    # The drop shot must be assigned to MONEY_SHOT
    drop_shots = [s for s in timeline.shots if s.phase_name == "DROP"]
    assert drop_shots[0].asset_path == "img_money.jpg", "Drop must use the MONEY_SHOT asset!"
    print(f"✅ Drop shot correctly mapped to '{drop_shots[0].asset_path}' with flash: {drop_shots[0].flash_intensity}")

if __name__ == "__main__":
    test_cailang_pipeline()
    print("\n🎯 ALL CAI-LANG COMPILER TESTS PASSED!")
