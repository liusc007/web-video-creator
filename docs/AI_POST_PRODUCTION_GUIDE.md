# AI Video Post-Production Field Guide

Modern generative video models (Kling, Runway, Sora, Wan, etc.) excel at expressive motion, lighting, and acting — **not** deterministic typography, UI overlays, pacing margins, or acoustic space.

`web-video-creator` is built around a core engineering rule:

> **Let generative models generate clean visual performance; let code handle everything that requires pixel, frame, or millisecond precision.**

---

## 1. Never Prompt Text or UI Into the Video Model

- **Avoid** asking video models to draw subtitles, security-camera timestamps, HUD boxes, or health bars. Diffusion models warp letters, jitter bounding boxes frame-to-frame, and burn irreversible artifacts into your base footage.
- **Instead**, generate clean, text-free base clips and composite transparent HTML5/CSS3 overlays with `HUDScene`, `CCTVScene`, `CyberHUDScene`, and `TimedSubtitleScene`.

## 2. Camera Framing & Character Consistency

- **Prefer locked or slow-drift camera angles** (e.g., `35° fixed ceiling CCTV mount`, `static medium shot`) when filming dialogue scenes or multi-shot sequences. Excessive multi-axis camera motion increases identity drift.
- **Anchor appearance traits verbatim** across shot prompts using a concise fixed descriptor block (~25–35 words covering face, hair, clothing silhouette, and lighting).

## 3. Solve Abrupt AI Openings & Cut-Off Endings (`tpad`)

- Generative clips often start talking at `0.05s` and clip mid-syllable at the tail.
- Prompt for a **1.5s silent reaction tail** whenever possible, and always pass raw clips through **Smart Breathing Padding**:

```bash
wvc pad --video raw_clip.mp4 -o padded.mp4 --start 0.35 --stop 0.50
```

This clones the opening and closing frames cleanly (`FFmpeg tpad`) while automatically shifting audio (`adelay`), giving editors and viewers natural visual breathing room before dialogue starts.

## 4. Separate Voice & Subtitles from Generation

- Generate dialogue separately using dedicated TTS or voice actors, leaving ellipsis (`……`) or punctuation pauses at sentence tails so final syllables aren't clipped.
- Extract word/segment timestamps with Whisper JSON or `.srt` and pass them directly into `TimedSubtitleScene.from_whisper(..., offset=0.35)` so subtitles align deterministically with your `tpad` head buffer.

## 5. Ground Dry Voiceovers in Acoustic Space

- Dry studio/TTS audio pasted directly onto a palace hall or surveillance clip sounds unnatural ("floating narrator").
- Run dry dialogue through `AudioProcessor` spatial presets and blend subtle room tone:

```bash
wvc audio --input dry_voice.mp3 --preset hall -o hall_voice.aac
```

Or run the entire 3-tier pipeline in one command:

```bash
wvc build examples/project_example.json -o final_cut.mp4
```
