import json
import shutil
import subprocess
from pathlib import Path

import pytest

from web_video_creator.audio import AudioProcessor
from web_video_creator.cli import parse_args
from web_video_creator.converter import HTMLToVideo
from web_video_creator.pipeline import PostProductionPipeline, load_project_config
from web_video_creator.scene import (
    CCTVScene,
    CompositeScene,
    CyberHUDScene,
    SubtitleScene,
    TimedSubtitleScene,
)


def test_cli_subcommands_and_legacy_parsing():
    # Subcommand: overlay
    args_ov = parse_args(
        ["overlay", "--video", "raw.mp4", "-o", "custom.mp4", "--type", "cyber", "--theme", "crimson"]
    )
    assert args_ov.command == "overlay"
    assert args_ov.video == "raw.mp4"
    assert args_ov.output == "custom.mp4"
    assert args_ov.type == "cyber"
    assert args_ov.theme == "crimson"
    assert args_ov.duration is None

    # Subcommand: pad
    args_pad = parse_args(["pad", "--video", "raw.mp4", "-o", "padded.mp4", "--start", "0.4", "--stop", "0.6"])
    assert args_pad.command == "pad"
    assert args_pad.output == "padded.mp4"
    assert args_pad.start == 0.4
    assert args_pad.stop == 0.6

    # Subcommand: audio
    args_aud = parse_args(["audio", "--input", "voice.mp3", "-o", "out.aac", "--preset", "cctv_speaker"])
    assert args_aud.command == "audio"
    assert args_aud.preset == "cctv_speaker"
    assert args_aud.output == "out.aac"

    # Legacy flat invocation: --text
    args_legacy = parse_args(["--text", "Hello World", "-o", "hello.mp4", "-d", "3.5"])
    assert args_legacy.command == "render"
    assert args_legacy.text == "Hello World"
    assert args_legacy.output == "hello.mp4"
    assert args_legacy.duration == 3.5

    # Legacy positional HTML file
    args_html = parse_args(["examples/sample.html", "-o", "sample.mp4"])
    assert args_html.command == "render"
    assert args_html.input == "examples/sample.html"
    assert args_html.output == "sample.mp4"


def test_pipeline_build_overlay_composite(tmp_path: Path):
    cfg = {
        "video": "clip.mp4",
        "hud": {"type": "cyber", "title": "UNIT-09"},
        "subtitles": {
            "style": "neon",
            "cues": [{"start": 0.0, "end": 1.5, "text": "Line 1"}],
        },
    }
    scene = PostProductionPipeline.build_overlay_scene(cfg, duration=4.0)
    assert isinstance(scene, CompositeScene)
    assert len(scene.layers) == 2
    assert isinstance(scene.layers[0], CyberHUDScene)
    assert isinstance(scene.layers[1], TimedSubtitleScene)

    cfg_file = tmp_path / "proj.json"
    cfg_file.write_text(json.dumps(cfg), encoding="utf-8")
    loaded = load_project_config(str(cfg_file))
    assert loaded["hud"]["title"] == "UNIT-09"

    # Static single-card SubtitleScene (no cues) should also build cleanly
    static_cfg = {"video": "clip.mp4", "subtitles": {"text": "Single Card", "style": "cinema"}}
    static_scene = PostProductionPipeline.build_overlay_scene(static_cfg, duration=3.0)
    assert isinstance(static_scene, SubtitleScene)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_ffmpeg_audio_and_smart_padding_integration(tmp_path: Path):
    raw_mp4 = tmp_path / "raw.mp4"
    padded_mp4 = tmp_path / "padded.mp4"
    tone_aac = tmp_path / "room_tone.aac"
    click_aac = tmp_path / "click.aac"
    voice_wav = tmp_path / "voice.wav"
    mixed_aac = tmp_path / "mixed.aac"

    # 1. Generate 1s synthetic 720p video
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x111827:s=1280x720:d=1:r=30",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(raw_mp4),
        ],
        check=True,
        capture_output=True,
    )

    # 2. Apply smart padding (0.35s start + 0.50s stop)
    HTMLToVideo.apply_smart_padding(str(raw_mp4), str(padded_mp4), start_duration=0.35, stop_duration=0.50)
    meta = HTMLToVideo.probe_video(str(padded_mp4))
    assert meta["width"] == 1280
    assert meta["height"] == 720
    assert meta["duration"] >= 1.75

    # 3. Synthesize room tone, transition click, and dry mono voice, then mix with spatial reverb
    AudioProcessor.generate_room_tone(str(tone_aac), duration=2.0, tone="hall")
    AudioProcessor.generate_transition_click(str(click_aac), style="cctv_static")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1",
            str(voice_wav),
        ],
        check=True,
        capture_output=True,
    )
    AudioProcessor.mix_dialogue_and_ambience(
        str(voice_wav),
        str(tone_aac),
        str(mixed_aac),
        dialogue_delay=0.35,
        dialogue_preset="hall",
        target_duration=2.5,
    )
    assert tone_aac.exists() and tone_aac.stat().st_size > 0
    assert click_aac.exists() and click_aac.stat().st_size > 0
    assert mixed_aac.exists() and mixed_aac.stat().st_size > 0

    final_mp4 = tmp_path / "final.mp4"
    HTMLToVideo.add_audio(str(padded_mp4), str(mixed_aac), str(final_mp4))
    final_meta = HTMLToVideo.probe_video(str(final_mp4))
    assert final_meta["has_audio"] is True
    assert final_meta["duration"] >= 1.8

    delayed_only = tmp_path / "delayed_only.aac"
    AudioProcessor.apply_preset(
        str(voice_wav),
        str(delayed_only),
        preset="radio",
        delay=0.35,
        target_duration=2.0,
    )
    assert delayed_only.exists() and delayed_only.stat().st_size > 0
