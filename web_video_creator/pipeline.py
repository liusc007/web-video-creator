import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .audio import AudioProcessor
from .converter import HTMLToVideo
from .scene import (
    CCTVScene,
    CompositeScene,
    CyberHUDScene,
    HUDScene,
    Scene,
    SubtitleScene,
    TimedSubtitleScene,
)


def load_project_config(config_path: str) -> Dict[str, Any]:
    """
    Loads a declarative post-production project file (.json natively, or .yaml/.yml if PyYAML is installed).
    """
    path = Path(config_path)
    raw = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "YAML config requires PyYAML (`pip install pyyaml`), or use a .json project file."
            ) from exc
        data = yaml.safe_load(raw)
        return dict(data or {})
    return json.loads(raw)


class PostProductionPipeline:
    """
    Three-Tier AI Video Post-Production Pipeline:
      1. Raw Video Layer: smart breathing frame padding (tpad).
      2. Web Overlay Layer: transparent HUD + Whisper-timed subtitles composited via Playwright.
      3. Spatial Audio Layer: acoustic reverb + optional room tone + muxing.
    """

    def __init__(self, converter: Optional[HTMLToVideo] = None):
        self.converter = converter or HTMLToVideo()

    @staticmethod
    def build_overlay_scene(config: Dict[str, Any], duration: float) -> Scene:
        layers: List[Scene] = []
        hud_cfg = config.get("hud")
        if hud_cfg:
            hud_type = str(hud_cfg.get("type", "cctv")).lower()
            hud_cls = {
                "cctv": CCTVScene,
                "cyber": CyberHUDScene,
                "hud": HUDScene,
            }.get(hud_type, CCTVScene)
            hud_kwargs = {
                k: v
                for k, v in hud_cfg.items()
                if k not in {"type"}
            }
            hud_kwargs.setdefault("duration", duration)
            layers.append(hud_cls(**hud_kwargs))

        sub_cfg = config.get("subtitles")
        if sub_cfg:
            if isinstance(sub_cfg, dict) and sub_cfg.get("whisper_json"):
                whisper_data = json.loads(
                    Path(sub_cfg["whisper_json"]).read_text(encoding="utf-8")
                )
                sub_kwargs = {
                    k: v
                    for k, v in sub_cfg.items()
                    if k not in {"whisper_json", "srt_file"}
                }
                sub_kwargs.setdefault("duration", duration)
                layers.append(TimedSubtitleScene.from_whisper(whisper_data, **sub_kwargs))
            elif isinstance(sub_cfg, dict) and sub_cfg.get("srt_file"):
                srt_text = Path(sub_cfg["srt_file"]).read_text(encoding="utf-8")
                sub_kwargs = {
                    k: v
                    for k, v in sub_cfg.items()
                    if k not in {"whisper_json", "srt_file"}
                }
                sub_kwargs.setdefault("duration", duration)
                layers.append(TimedSubtitleScene.from_srt(srt_text, **sub_kwargs))
            elif isinstance(sub_cfg, dict) and "cues" in sub_cfg:
                sub_kwargs = dict(sub_cfg)
                sub_kwargs.setdefault("duration", duration)
                layers.append(TimedSubtitleScene(**sub_kwargs))
            elif isinstance(sub_cfg, dict):
                sub_kwargs = dict(sub_cfg)
                sub_kwargs.setdefault("duration", duration)
                layers.append(SubtitleScene(**sub_kwargs))

        if not layers:
            return CCTVScene(duration=duration)
        if len(layers) == 1:
            return layers[0]
        return CompositeScene(layers=layers, duration=duration, transparent=True)

    async def run(self, config: Dict[str, Any], output_path: Optional[str] = None) -> str:
        base_video = config["video"]
        final_output = output_path or config.get("output", "final_output.mp4")

        work_dir = Path(tempfile.mkdtemp(prefix="wvc_pipe_"))
        try:
            current_video = str(base_video)

            # Tier 1: Smart breathing frame padding
            pad_cfg = config.get("padding")
            pad_start = 0.0
            if pad_cfg and pad_cfg.get("enabled", True):
                pad_start = float(pad_cfg.get("start", 0.35))
                pad_stop = float(pad_cfg.get("stop", 0.5))
                padded_video = str(work_dir / "tier1_padded.mp4")
                HTMLToVideo.apply_smart_padding(
                    current_video,
                    padded_video,
                    start_duration=pad_start,
                    stop_duration=pad_stop,
                )
                current_video = padded_video

            # Probe duration for overlay sync
            try:
                meta = HTMLToVideo.probe_video(current_video)
                video_duration = float(meta.get("duration") or config.get("duration", 5.0))
            except Exception:
                video_duration = float(config.get("duration", 5.0))

            # Auto-align subtitle offset to pad_start if not explicitly provided (for TimedSubtitleScene)
            sub_cfg = config.get("subtitles")
            if (
                isinstance(sub_cfg, dict)
                and "offset" not in sub_cfg
                and pad_start > 0
                and any(k in sub_cfg for k in ("whisper_json", "srt_file", "cues"))
            ):
                config = dict(config)
                config["subtitles"] = {**sub_cfg, "offset": pad_start}

            # Tier 2: Web Overlay Layer
            if config.get("hud") or config.get("subtitles"):
                overlay_scene = self.build_overlay_scene(config, duration=video_duration)
                overlaid_video = str(work_dir / "tier2_overlaid.mp4")
                await self.converter.overlay_scenes_on_video(
                    current_video,
                    [overlay_scene],
                    overlaid_video,
                )
                current_video = overlaid_video

            # Tier 3: Spatial Audio Layer
            audio_cfg = config.get("audio")
            if audio_cfg and audio_cfg.get("input"):
                preset = str(audio_cfg.get("preset", "hall"))
                delay = float(audio_cfg.get("delay", pad_start))
                ambience_path = audio_cfg.get("ambience")
                processed_audio = str(work_dir / "tier3_audio.aac")

                if ambience_path or audio_cfg.get("auto_room_tone"):
                    if not ambience_path:
                        ambience_path = str(work_dir / "auto_room_tone.aac")
                        AudioProcessor.generate_room_tone(
                            ambience_path,
                            duration=max(video_duration, 3.0),
                            tone=str(audio_cfg.get("room_tone_style", "indoor")),
                        )
                    AudioProcessor.mix_dialogue_and_ambience(
                        audio_cfg["input"],
                        ambience_path,
                        processed_audio,
                        dialogue_delay=delay,
                        ambience_volume=float(audio_cfg.get("ambience_volume", 0.18)),
                        dialogue_preset=preset,
                        target_duration=video_duration,
                    )
                else:
                    AudioProcessor.apply_preset(
                        audio_cfg["input"],
                        processed_audio,
                        preset=preset,
                        volume=float(audio_cfg.get("volume", 1.0)),
                        delay=delay,
                        target_duration=video_duration,
                    )

                HTMLToVideo.add_audio(current_video, processed_audio, final_output)
            else:
                shutil.copy2(current_video, final_output)

            return str(final_output)
        finally:
            shutil.rmtree(str(work_dir), ignore_errors=True)
