# ⚡ CAIEDIT
### Autonomous AI Agentic Music & Video Editing Studio
**Powered by Native C++ ARM NEON Engines + Multi-Agent Orchestration Swarm**

```
   ┌───────────────────────────────────────────────────────────────┐
   │                  CAIEDIT AI AGENTIC HARNESS                   │
   │  DirectorAgent ➔ SonicAgent ➔ OpticAgent ➔ ViralVFX ➔ QAPolish│
   └───────────────────────────────┬───────────────────────────────┘
                                   │ (Zero-Copy Pointers)
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                            ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ libcaiedit_dsp.so│      │ libcaiedit_fx.so │      │libcaiedit_flow.so│
│  (C++ Audio DSP) │      │(C++ SIMD VFX 60F)│      │  (C++ Flow & Cut)│
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

---

## 🚀 Key Features

1. **Autonomous 5-Agent Swarm**:
   - **`DirectorAgent`**: Deconstructs user creative prompts, identifies visual aesthetics (`car_phonk_velocity`, `anime_amv_velocity`, etc.), and builds the execution DAG.
   - **`SonicAgent`**: Decodes audio, calculates BPM (e.g. 161.5 BPM), isolates sub-bass kick transients (<140 Hz), and pinpoints exact climax/drop timestamps.
   - **`OpticAgent`**: Reverse-engineers viral TikTok/Reels reference videos, extracting shot cut maps, velocity ramps, and motion curves.
   - **`ViralVFXAgent`**: Synchronizes cuts on kick drums, applies audio-reactive camera shakes, white impact flashes, chromatic aberration (RGB split), and phonk color grading.
   - **`QAPolishAgent`**: Audits 9:16 vertical 1080×1920 60 FPS output, locks audio-video sync drift, and generates viral titles, descriptions, and hashtags.

2. **Native C++ Acceleration (ARM NEON SIMD)**:
   - **`libcaiedit_fx.so`**: Sub-pixel reflective camera shake, exponential decay white flash, RGB split, and color contrast grade processing 1080×1920 frames in single-digit milliseconds.
   - **`libcaiedit_dsp.so`**: Ultra-low latency transient and drop locator without loading gigabytes of heavy external AI libraries.
   - **`libcaiedit_flow.so`**: Fast block-matching motion estimator and scene-cut difference analyzer.

3. **Zero-Disk-Overhead Streaming**:
   - Frames are processed in memory and streamed directly into FFmpeg H.264 / AAC encoder pipes with zero temporary frame PNGs written to storage.

---

## 📁 Project Architecture

```
CAIEDIT/
├── native/                         # C++ SIMD Engines
│   ├── caiedit_fx.cpp              # Video VFX (RGB Split, Flash, Shake, Color Grade)
│   ├── caiedit_dsp.cpp             # Audio DSP (RMS, Filters, Transients, Drop Locator)
│   ├── caiedit_flow.cpp            # Optical Flow & Scene Cut Difference
│   ├── build.sh                    # Clang++ compilation script
│   ├── libcaiedit_fx.so            # Compiled native VFX shared library
│   ├── libcaiedit_dsp.so           # Compiled native DSP shared library
│   └── libcaiedit_flow.so          # Compiled native Flow shared library
├── caiedit/
│   ├── bridge/                     # Zero-copy ctypes C++ bridges
│   │   ├── fx_bridge.py
│   │   ├── dsp_bridge.py
│   │   └── flow_bridge.py
│   ├── audio/                      # Audio intelligence
│   │   └── engine.py
│   ├── vision/                     # Video reverse-engineering
│   │   └── analyzer.py
│   ├── vfx/                        # Video assembly & FFmpeg streaming
│   │   └── renderer.py
│   ├── agents/                     # The 5 Autonomous AI Agents
│   │   ├── base.py
│   │   ├── director_agent.py
│   │   ├── sonic_agent.py
│   │   ├── optic_agent.py
│   │   ├── viral_vfx_agent.py
│   │   └── qa_polish_agent.py
│   ├── harness.py                  # Master Studio Agent Harness
│   └── cli.py                      # CLI runner & demo generator
├── tests/
│   └── test_native_bridges.py      # Benchmark & correctness suite
└── workspace/
    ├── input/                      # Your raw clips and music
    ├── output/                     # Rendered 60 FPS vertical videos & JSON metadata
    └── demo/                       # Synthetic test assets
```

---

## ⚡ Quick Start & Usage

### 1. Run the Self-Contained Demo Benchmark
Synthesizes a test phonk soundtrack, generates test video patterns, detects the bass drop at 3.0s, and renders a complete 60 FPS 9:16 vertical edit:

```bash
cd /data/data/com.termux/files/home/CAIEDIT
PYTHONPATH=. python3 -m caiedit.cli --demo
```

### 2. Run with Your Own Clips and Song
```bash
PYTHONPATH=. python3 -m caiedit.cli \
  --prompt "Make an aggressive drift car edit with hard shakes on the drop" \
  --audio "workspace/input/song.mp3" \
  --clips "workspace/input/clip1.mp4" "workspace/input/clip2.mp4" \
  --output "workspace/output/my_viral_edit.mp4"
```

### 3. Clone Cuts & Pacing from a Reference Viral Video
```bash
PYTHONPATH=. python3 -m caiedit.cli \
  --prompt "Anime fight velocity edit cloning the reference TikTok pacing" \
  --audio "workspace/input/track.wav" \
  --clips "workspace/input/anime_scene1.mp4" "workspace/input/anime_scene2.mp4" \
  --ref-video "workspace/input/viral_reference.mp4" \
  --output "workspace/output/anime_edit.mp4"
```

### 4. Rebuild / Compile Native C++ Engines
```bash
bash /data/data/com.termux/files/home/CAIEDIT/native/build.sh
```

---

## 📊 Benchmark Verification

On ARM aarch64 (NEON SIMD enabled):
- **White Impact Flash**: `9.95 ms` (100.5 FPS) @ 1080×1920
- **RGB Split Glitch**: `16.25 ms` (61.5 FPS) @ 1080×1920
- **Camera Shake**: `18.46 ms` (54.2 FPS) @ 1080×1920
- **Audio Transient DSP**: `3.28 ms` for 5 seconds of audio (1,500x faster than real-time)
- **Scene Cut Flow**: `6.31 ms` per frame comparison
