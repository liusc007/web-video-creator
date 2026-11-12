"""
Example: End-to-End Three-Tier AI Video Post-Production with web-video-creator.

Demonstrates:
1. Layering a live CCTV HUD + Whisper-aligned timed subtitles using CompositeScene.
2. Exporting an offline HTML preview you can inspect directly in any browser.
3. Optional full pipeline execution with synthetic base clip + room tone + FFmpeg tpad.
"""

import asyncio
from pathlib import Path

from web_video_creator import (
    AudioProcessor,
    CCTVScene,
    CompositeScene,
    HTMLToVideo,
    TimedSubtitleScene,
)


def build_demo_composite() -> CompositeScene:
    cctv_layer = CCTVScene(
        title="CAM-07 [MAIN_SANCTUARY]",
        location="INNER HALL // 35° CEILING MOUNT",
        status_text="REC ●",
        timestamp_text="2026-11-12 09:46:12.400",
        color_theme="emerald",
        show_grid=True,
        show_brackets=True,
        show_scanlines=True,
        targets=[
            {
                "x": 36,
                "y": 24,
                "w": 28,
                "h": 50,
                "label": "SUBJECT-01 // TRAVELER",
                "confidence": "99.8%",
                "metrics": {
                    "HEART RATE": "142 BPM",
                    "POSTURE": "STEADY",
                    "AUDIO SYNC": "LOCKED",
                },
            }
        ],
        duration=4.5,
    )

    # Whisper-like timed cues (automatically shifted by +0.35s to match tpad start padding)
    whisper_mock = {
        "segments": [
            {
                "start": 0.1,
                "end": 1.8,
                "text": "请保持机位稳定，画面只负责表演。",
                "translation": "Keep the camera locked—let the generative model act.",
                "words": [
                    {"word": "请保持", "start": 0.1, "end": 0.6},
                    {"word": "机位稳定，", "start": 0.6, "end": 1.1},
                    {"word": "画面只负责表演。", "start": 1.1, "end": 1.8},
                ],
            },
            {
                "start": 1.9,
                "end": 3.6,
                "text": "所有 UI、时间码与双语字幕，全部交给代码后期合成。",
                "translation": "All HUDs, timecodes, and subtitles are rendered deterministically in code.",
            },
        ]
    }

    subtitle_layer = TimedSubtitleScene.from_whisper(
        whisper_mock,
        offset=0.35,
        position="bottom",
        style="cinema",
        duration=4.5,
    )

    return CompositeScene(layers=[cctv_layer, subtitle_layer], duration=4.5)


async def main():
    print("=== web-video-creator: Three-Tier AI Post-Production Demo ===")
    composite = build_demo_composite()

    out_html = Path("preview_composite_hud.html")
    out_html.write_text(composite.to_html(), encoding="utf-8")
    print(f"1. Saved interactive HTML preview: {out_html.resolve()}")

    # Example production snippet (when you have raw_clip.mp4 & dry_voice.mp3):
    # HTMLToVideo.apply_smart_padding("raw_clip.mp4", "padded.mp4", start_duration=0.35, stop_duration=0.5)
    # converter = HTMLToVideo(width=1920, height=1080, fps=30)
    # await converter.overlay_scenes_on_video("padded.mp4", [composite], "overlaid.mp4")
    # AudioProcessor.generate_room_tone("room_tone.aac", duration=5.0, tone="hall")
    # AudioProcessor.mix_dialogue_and_ambience(
    #     "dry_voice.mp3", "room_tone.aac", "spatial_audio.aac",
    #     dialogue_delay=0.35, dialogue_preset="hall"
    # )
    # HTMLToVideo.add_audio("overlaid.mp4", "spatial_audio.aac", "final_cut.mp4")


if __name__ == "__main__":
    asyncio.run(main())
