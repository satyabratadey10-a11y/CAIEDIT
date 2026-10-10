"""
CAIEDIT CLI Interface
Execute agentic video edits directly from your terminal.
"""

import os
import sys
import argparse
import subprocess
import numpy as np
from caiedit.harness import CAIEditHarness

def generate_synthetic_demo_assets(work_dir: str):
    """Generates small synthetic audio & video clips to verify the pipeline with zero downloads."""
    os.makedirs(work_dir, exist_ok=True)
    audio_file = os.path.join(work_dir, "demo_phonk_track.wav")
    clip1_file = os.path.join(work_dir, "demo_car_clip_1.mp4")
    clip2_file = os.path.join(work_dir, "demo_car_clip_2.mp4")

    # 1. Synthesize 6-second Phonk-style audio with a drop at 3.0s
    if not os.path.exists(audio_file):
        print("  -> Synthesizing demo audio track with drop...")
        sr = 44100
        duration = 6.0
        t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
        # 160 BPM beat grid: beat interval = 60 / 160 = 0.375s
        audio = np.sin(2 * np.pi * 55 * t) * 0.3  # 808 sub bass
        for beat_t in np.arange(0.375, duration, 0.375):
            idx = int(beat_t * sr)
            if idx + 1000 < len(audio):
                audio[idx:idx+1000] += np.hanning(1000) * 0.9  # kick punch
        # Huge drop boost at 3.0s
        audio[int(3.0 * sr):int(3.75 * sr)] *= 2.2
        # Save as 16-bit PCM WAV
        audio_int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
        import wave
        with wave.open(audio_file, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(audio_int16.tobytes())

    # 2. Synthesize test video clips via FFmpeg test patterns
    if not os.path.exists(clip1_file):
        print("  -> Generating demo video clip 1...")
        subprocess.run([
            "ffmpeg", "-y", "-v", "error",
            "-f", "lavfi", "-i", "testsrc=duration=4:size=720x1280:rate=30",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", clip1_file
        ], check=True)

    if not os.path.exists(clip2_file):
        print("  -> Generating demo video clip 2...")
        subprocess.run([
            "ffmpeg", "-y", "-v", "error",
            "-f", "lavfi", "-i", "smptebars=duration=4:size=720x1280:rate=30",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", clip2_file
        ], check=True)

    return audio_file, [clip1_file, clip2_file]

def main():
    parser = argparse.ArgumentParser(description="CAIEDIT: Autonomous AI Agentic Video & Audio Studio")
    parser.add_argument("--prompt", type=str, default="Make a viral phonk car edit synced on the bass drop", help="Creative instruction for the Director Agent")
    parser.add_argument("--audio", type=str, help="Path to reference audio (.mp3, .wav)")
    parser.add_argument("--clips", nargs="+", help="Paths to raw video clips (.mp4, .mov)")
    parser.add_argument("--ref-video", type=str, default="", help="Optional viral reference video to clone cuts/velocity from")
    parser.add_argument("--output", type=str, default="", help="Path for final rendered video")
    parser.add_argument("--demo", action="store_true", help="Run a self-contained end-to-end demo session")

    args = parser.parse_args()

    harness = CAIEditHarness()

    if args.demo:
        print("\n🧪 [CAIEDIT] Starting Self-Contained End-to-End Demo Benchmark...")
        demo_dir = os.path.abspath("workspace/demo")
        audio_path, raw_clips = generate_synthetic_demo_assets(demo_dir)
        session = harness.run(
            prompt="Autonomous Car Phonk Edit with Impact Flash & Camera Shake",
            audio_path=audio_path,
            raw_clips=raw_clips,
            output_path="workspace/output/caiedit_demo_render.mp4"
        )
        print("\n🎉 Demo test completed successfully!")
        print(f"Output Video : {session.rendered_video_path}")
        return

    if not args.audio or not args.clips:
        print("❌ Error: Both --audio and --clips are required (or use --demo).")
        parser.print_help()
        sys.exit(1)

    harness.run(
        prompt=args.prompt,
        audio_path=args.audio,
        raw_clips=args.clips,
        reference_video=args.ref_video,
        output_path=args.output
    )

if __name__ == "__main__":
    main()
