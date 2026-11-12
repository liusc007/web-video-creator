import argparse
import asyncio
import sys
from pathlib import Path
from typing import List, Optional

from .audio import AudioProcessor
from .converter import HTMLToVideo
from .pipeline import PostProductionPipeline, load_project_config
from .scene import (
    CCTVScene,
    CompositeScene,
    CyberHUDScene,
    HUDScene,
    ImageScene,
    Scene,
    SubtitleScene,
    TextScene,
    TimedSubtitleScene,
)

SUBCOMMANDS = {"render", "overlay", "pad", "audio", "build", "presets"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="web-video-creator",
        description="HTML to Video Rendering & AI Video Post-Production Engine",
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # 1. render
    render_parser = subparsers.add_parser("render", help="Render HTML/text/image scenes to video")
    render_parser.add_argument("input", nargs="?", help="HTML file to convert")
    render_parser.add_argument("-o", "--output", default="output.mp4", help="Output video path")
    render_parser.add_argument("-d", "--duration", type=float, default=5.0, help="Duration (seconds)")
    render_parser.add_argument("--text", help="Create a text scene with this text")
    render_parser.add_argument("--image", help="Create an image scene with this URL")
    render_parser.add_argument("--width", type=int, default=1920, help="Video width")
    render_parser.add_argument("--height", type=int, default=1080, help="Video height")
    render_parser.add_argument("--fps", type=int, default=30, help="Frames per second")

    # 2. overlay
    overlay_parser = subparsers.add_parser("overlay", help="Overlay HUD/subtitles onto an AI video")
    overlay_parser.add_argument("--video", required=True, help="Base AI video path")
    overlay_parser.add_argument("-o", "--output", default="overlaid.mp4", help="Output video path")
    overlay_parser.add_argument(
        "--type",
        choices=["cctv", "cyber", "hud", "subtitle"],
        default="cctv",
        help="Overlay type",
    )
    overlay_parser.add_argument("--title", default="CAM-01 [NORTH_GATE]", help="Camera title or header")
    overlay_parser.add_argument("--location", default="PERIMETER // 35° MOUNT", help="HUD location label")
    overlay_parser.add_argument(
        "--theme",
        choices=["emerald", "amber", "cyan", "crimson", "monochrome"],
        default="emerald",
        help="HUD color theme",
    )
    overlay_parser.add_argument("--text", help="Subtitle or main message text")
    overlay_parser.add_argument("--translation", help="Subtitle secondary translation")
    overlay_parser.add_argument("--srt", help="Optional .srt subtitle file to composite")
    overlay_parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=None,
        help="Duration in seconds (auto-probed from --video when omitted)",
    )
    overlay_parser.add_argument("--fps", type=int, default=30, help="Frames per second")

    # 3. pad
    pad_parser = subparsers.add_parser("pad", help="Apply smart tpad breathing frame padding to video")
    pad_parser.add_argument("--video", required=True, help="Input video path")
    pad_parser.add_argument("-o", "--output", default="padded.mp4", help="Output video path")
    pad_parser.add_argument("--start", type=float, default=0.35, help="Start padding in seconds (clone)")
    pad_parser.add_argument("--stop", type=float, default=0.5, help="Stop padding in seconds (clone)")

    # 4. audio
    audio_parser = subparsers.add_parser("audio", help="Apply spatial acoustics / filters to audio")
    audio_parser.add_argument("--input", required=True, help="Input audio path")
    audio_parser.add_argument("-o", "--output", default="spatial_audio.aac", help="Output audio path")
    audio_parser.add_argument(
        "--preset",
        choices=list(AudioProcessor.REVERB_PRESETS.keys()),
        default="hall",
        help="Acoustic reverb preset",
    )
    audio_parser.add_argument("--volume", type=float, default=1.0, help="Audio volume scale")
    audio_parser.add_argument("--fade-in", type=float, default=0.0, help="Fade-in seconds")
    audio_parser.add_argument("--fade-out", type=float, default=0.0, help="Fade-out seconds")

    # 5. build
    build_parser = subparsers.add_parser(
        "build", help="Run full 3-tier post-production pipeline from a JSON/YAML project config"
    )
    build_parser.add_argument("config", help="Path to project.json or project.yaml")
    build_parser.add_argument("-o", "--output", help="Override output video path")
    build_parser.add_argument("--fps", type=int, default=30, help="Frames per second")

    # 6. presets
    subparsers.add_parser("presets", help="List available HUD overlays and acoustic presets")

    return parser


def build_legacy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="web-video-creator",
        description="HTML to Video Rendering & AI Video Post-Production Engine",
    )
    parser.add_argument("input", nargs="?", help="HTML file to convert")
    parser.add_argument("-o", "--output", default="output.mp4", help="Output video path")
    parser.add_argument("-d", "--duration", type=float, default=5.0, help="Duration (seconds)")
    parser.add_argument("--text", help="Create a text scene with this text")
    parser.add_argument("--image", help="Create an image scene with this URL")
    parser.add_argument("--width", type=int, default=1920, help="Video width")
    parser.add_argument("--height", type=int, default=1080, help="Video height")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    return parser


def _normalize_argv(argv: List[str]) -> List[str]:
    """
    Supports both subcommands (`wvc render ...`, `wvc overlay ...`)
    and legacy flat invocation (`wvc --text "hello" -o out.mp4`, `wvc sample.html -o out.mp4`).
    """
    if not argv:
        return argv
    first = argv[0]
    if first in SUBCOMMANDS or first in {"-h", "--help"}:
        return argv
    return ["render", *argv]


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    normalized = _normalize_argv(raw_argv)
    parser = build_parser()
    if not normalized:
        return parser.parse_args(normalized)
    return parser.parse_args(normalized)


def main(argv: Optional[List[str]] = None) -> None:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if not raw_argv:
        parser.print_help()
        return

    args = parse_args(raw_argv)

    if args.command == "presets":
        print("HUD / Overlay Presets: cctv, cyber, hud, subtitle, timed-subtitle, composite")
        print("HUD Color Themes:      emerald, amber, cyan, crimson, monochrome")
        print("Subtitle Styles:       cinema, netflix, neon, cctv")
        print(f"Audio Spatial Presets: {', '.join(AudioProcessor.REVERB_PRESETS.keys())}")
        return

    if args.command == "pad":
        HTMLToVideo.apply_smart_padding(
            args.video, args.output, start_duration=args.start, stop_duration=args.stop
        )
        print(f"Padded video saved to {args.output}")
        return

    if args.command == "audio":
        AudioProcessor.apply_preset(
            args.input,
            args.output,
            preset=args.preset,
            volume=args.volume,
            fade_in=args.fade_in,
            fade_out=args.fade_out,
        )
        print(f"Spatial audio saved to {args.output}")
        return

    if args.command == "build":
        cfg = load_project_config(args.config)
        converter = HTMLToVideo(fps=args.fps)
        pipeline = PostProductionPipeline(converter=converter)
        result = asyncio.run(pipeline.run(cfg, output_path=args.output))
        print(f"Pipeline output saved to {result}")
        return

    if args.command == "overlay":
        converter = HTMLToVideo(fps=args.fps)
        duration = args.duration
        if duration is None:
            try:
                duration = float(HTMLToVideo.probe_video(args.video).get("duration") or 5.0)
            except Exception:
                duration = 5.0

        layers: List[Scene] = []

        if args.type == "cctv":
            layers.append(
                CCTVScene(
                    title=args.title,
                    location=args.location,
                    color_theme=args.theme,
                    duration=duration,
                )
            )
        elif args.type == "cyber":
            layers.append(
                CyberHUDScene(
                    title=args.title,
                    location=args.location,
                    color_theme=args.theme if args.theme != "emerald" else "cyan",
                    duration=duration,
                )
            )
        elif args.type == "hud":
            layers.append(
                HUDScene(
                    title=args.title,
                    location=args.location,
                    color_theme=args.theme,
                    duration=duration,
                )
            )

        if args.srt:
            srt_content = Path(args.srt).read_text(encoding="utf-8")
            layers.append(TimedSubtitleScene.from_srt(srt_content, duration=duration))
        elif args.type == "subtitle" or args.text:
            layers.append(
                SubtitleScene(
                    text=args.text or "Default Subtitle",
                    translation=args.translation or "",
                    duration=duration,
                )
            )

        scene = layers[0] if len(layers) == 1 else CompositeScene(layers=layers, duration=duration)
        asyncio.run(converter.overlay_scenes_on_video(args.video, [scene], args.output))
        print(f"Overlaid video saved to {args.output}")
        return

    if args.command == "render":
        converter = HTMLToVideo(width=args.width, height=args.height, fps=args.fps)
        if getattr(args, "text", None):
            scenes = [TextScene(text=args.text, duration=args.duration)]
        elif getattr(args, "image", None):
            scenes = [ImageScene(image_url=args.image, duration=args.duration)]
        elif getattr(args, "input", None):
            html_content = Path(args.input).read_text(encoding="utf-8")
            scenes = [Scene(html=html_content, duration=args.duration)]
        else:
            parser.print_help()
            return

        asyncio.run(converter.render_scenes(scenes, args.output))
        print(f"Video saved to {args.output}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
