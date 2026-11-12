import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .scene import Scene


class HTMLToVideo:
    """
    Video rendering engine using Playwright for headless browser frame capture
    and FFmpeg for encoding and multi-layer composition.
    """

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
        browser_channel: Optional[str] = None,
        executable_path: Optional[str] = None,
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.browser_channel = browser_channel
        self.executable_path = executable_path

    @staticmethod
    def _find_local_chromium_executable() -> Optional[str]:
        """
        Searches common Playwright browser cache directories when the pinned
        revision differs slightly from an already-installed local Chromium build.
        """
        candidates: List[Path] = []
        env_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
        if env_path and env_path != "0":
            candidates.append(Path(env_path))

        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            candidates.append(Path(local_appdata) / "ms-playwright")

        home: Optional[Path] = None
        try:
            home = Path.home()
        except Exception:
            profile = os.environ.get("USERPROFILE")
            if profile:
                home = Path(profile)
            elif os.environ.get("USERNAME"):
                home = Path("C:/Users") / os.environ["USERNAME"]

        if home is not None:
            candidates.extend(
                [
                    home / "AppData" / "Local" / "ms-playwright",
                    home / ".cache" / "ms-playwright",
                    home / "Library" / "Caches" / "ms-playwright",
                ]
            )

        users_dir = Path("C:/Users")
        if users_dir.exists():
            candidates.extend(users_dir.glob("*/AppData/Local/ms-playwright"))

        patterns = [
            "chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell.exe",
            "chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell",
            "chromium-*/chrome-win64/chrome.exe",
            "chromium-*/chrome-linux/chrome",
            "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
        ]
        for base in candidates:
            if not base.exists():
                continue
            for pat in patterns:
                matches = sorted(base.glob(pat), reverse=True)
                for match in matches:
                    if match.is_file():
                        return str(match)
        return None

    async def _launch_browser(self, playwright: Any) -> Any:
        if self.executable_path:
            return await playwright.chromium.launch(executable_path=self.executable_path)
        if self.browser_channel:
            return await playwright.chromium.launch(channel=self.browser_channel)

        try:
            return await playwright.chromium.launch()
        except Exception as primary_err:
            fallback_exe = self._find_local_chromium_executable()
            if fallback_exe:
                return await playwright.chromium.launch(executable_path=fallback_exe)
            for ch in ("msedge", "chrome"):
                try:
                    return await playwright.chromium.launch(channel=ch)
                except Exception:
                    continue
            raise primary_err

    @staticmethod
    def probe_video(video_path: str) -> Dict[str, Any]:
        """
        Inspects a video file using ffprobe and returns width, height, fps,
        duration, and has_audio metadata.
        """
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]
        res = subprocess.run(cmd, check=True, capture_output=True, text=True)
        info = json.loads(res.stdout or "{}")
        streams = info.get("streams", [])
        fmt = info.get("format", {})

        video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
        has_audio = any(s.get("codec_type") == "audio" for s in streams)

        fps_val = 30.0
        rate_str = video_stream.get("r_frame_rate") or video_stream.get("avg_frame_rate")
        if rate_str and "/" in str(rate_str):
            num, den = str(rate_str).split("/", 1)
            if float(den) > 0:
                fps_val = float(num) / float(den)

        duration = float(
            fmt.get("duration") or video_stream.get("duration") or 0.0
        )
        return {
            "width": int(video_stream.get("width", 1920)),
            "height": int(video_stream.get("height", 1080)),
            "fps": round(fps_val, 3),
            "duration": duration,
            "has_audio": has_audio,
        }

    async def render_scenes(self, scenes: List[Scene], output_path: str) -> str:
        """Renders a sequence of HTML scenes into a standalone video."""
        from playwright.async_api import async_playwright

        frames_dir = Path(tempfile.mkdtemp(prefix="wvc_frames_"))
        try:
            total_frames = 0
            async with async_playwright() as p:
                browser = await self._launch_browser(p)
                try:
                    for i, scene in enumerate(scenes):
                        html = scene.to_html()
                        html_path = frames_dir / f"scene_{i}.html"
                        html_path.write_text(html, encoding="utf-8")

                        scene_frames = max(int(round(scene.duration * self.fps)), 1)
                        await self._capture_scene_with_browser(
                            browser,
                            str(html_path),
                            frames_dir,
                            total_frames,
                            scene_frames,
                            duration_sec=scene.duration,
                            transparent=bool(scene.transparent),
                            width=self.width,
                            height=self.height,
                        )
                        total_frames += scene_frames
                finally:
                    await browser.close()

            self._encode_video(str(frames_dir), output_path, self.width, self.height)
            return output_path
        finally:
            shutil.rmtree(str(frames_dir), ignore_errors=True)

    async def overlay_scenes_on_video(
        self,
        base_video: str,
        scenes: List[Scene],
        output_path: str,
        auto_match_video: bool = True,
    ) -> str:
        """
        Renders transparent HTML scenes (HUD, subtitles, telemetry, watermarks)
        and overlays them directly onto a base video using FFmpeg.
        """
        from playwright.async_api import async_playwright

        target_w, target_h = self.width, self.height
        if auto_match_video:
            try:
                meta = self.probe_video(base_video)
                target_w = meta["width"]
                target_h = meta["height"]
            except Exception:
                pass

        frames_dir = Path(tempfile.mkdtemp(prefix="wvc_overlay_"))
        try:
            total_frames = 0
            async with async_playwright() as p:
                browser = await self._launch_browser(p)
                try:
                    for i, scene in enumerate(scenes):
                        html = scene.to_html()
                        html_path = frames_dir / f"scene_{i}.html"
                        html_path.write_text(html, encoding="utf-8")

                        scene_frames = max(int(round(scene.duration * self.fps)), 1)
                        await self._capture_scene_with_browser(
                            browser,
                            str(html_path),
                            frames_dir,
                            total_frames,
                            scene_frames,
                            duration_sec=scene.duration,
                            transparent=True,
                            width=target_w,
                            height=target_h,
                        )
                        total_frames += scene_frames
                finally:
                    await browser.close()

            pattern = str(frames_dir / "frame_%06d.png")
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(base_video),
                "-framerate",
                str(self.fps),
                "-i",
                pattern,
                "-filter_complex",
                "[0:v][1:v]overlay=0:0:eof_action=pass[outv]",
                "-map",
                "[outv]",
                "-map",
                "0:a?",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-c:a",
                "copy",
                str(output_path),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        finally:
            shutil.rmtree(str(frames_dir), ignore_errors=True)

    async def _capture_scene_with_browser(
        self,
        browser: Any,
        html_path: str,
        frames_dir: Path,
        start_frame_offset: int,
        scene_frames: int,
        duration_sec: float,
        transparent: bool = False,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        vw = width or self.width
        vh = height or self.height
        page = await browser.new_page(viewport={"width": vw, "height": vh})
        try:
            file_url = Path(html_path).resolve().as_uri()
            await page.goto(file_url, wait_until="load")
            duration_ms = duration_sec * 1000.0

            for frame_idx in range(scene_frames):
                global_frame_num = start_frame_offset + frame_idx
                progress = frame_idx / max(scene_frames - 1, 1)
                elapsed_ms = (frame_idx / max(self.fps, 1)) * 1000.0

                await page.evaluate(
                    """
                    ({ progress, elapsedMs, durationMs }) => {
                      const stepDoc = (doc, win) => {
                        if (!doc) return;
                        if (doc.documentElement) {
                          doc.documentElement.style.setProperty('--hf-progress', String(progress));
                        }
                        if (doc.body) {
                          doc.body.style.setProperty('--hf-progress', String(progress));
                        }
                        if (win) {
                          win.__hfProgress = progress;
                          win.__wvcTimeMs = elapsedMs;
                          win.__wvcDurationMs = durationMs;
                          if (typeof win.__wvcOnFrame === 'function') {
                            win.__wvcOnFrame(progress, elapsedMs, durationMs);
                          }
                        }
                        if (typeof doc.getAnimations === 'function') {
                          doc.getAnimations().forEach((anim) => {
                            anim.pause();
                            anim.currentTime = elapsedMs;
                          });
                        }
                      };
                      stepDoc(document, window);
                    }
                    """,
                    {
                        "progress": progress,
                        "elapsedMs": elapsed_ms,
                        "durationMs": duration_ms,
                    },
                )
                target_frame_path = frames_dir / f"frame_{global_frame_num:06d}.png"
                await page.screenshot(
                    path=str(target_frame_path),
                    full_page=False,
                    omit_background=transparent,
                )
        finally:
            await page.close()

    def _encode_video(
        self, frames_dir: str, output_path: str, width: int, height: int
    ) -> None:
        pattern = os.path.join(frames_dir, "frame_%06d.png")
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate",
            str(self.fps),
            "-i",
            pattern,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-vf",
            f"scale={width}:{height}",
            output_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    @staticmethod
    def apply_smart_padding(
        video_path: str,
        output_path: str,
        start_duration: float = 0.35,
        stop_duration: float = 0.5,
    ) -> str:
        """
        Clones initial and ending frames using FFmpeg's tpad filter.
        Essential for AI-generated video clips to prevent abrupt scene cuts
        and give actors natural breathing pacing before/after dialogue.
        If the input video carries an audio stream, delays & pads audio to stay in sync.
        """
        has_audio = False
        try:
            has_audio = HTMLToVideo.probe_video(video_path)["has_audio"]
        except Exception:
            has_audio = False

        vf = (
            f"tpad=start_duration={start_duration}:start_mode=clone:"
            f"stop_duration={stop_duration}:stop_mode=clone"
        )
        if has_audio:
            delay_ms = int(round(start_duration * 1000))
            af = f"adelay={delay_ms}:all=1,apad"
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-vf",
                vf,
                "-af",
                af,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-shortest",
                str(output_path),
            ]
        else:
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-vf",
                vf,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(output_path),
            ]
        subprocess.run(cmd, check=True, capture_output=True)
        return str(output_path)

    @staticmethod
    def add_audio(video_path: str, audio_path: str, output_path: str) -> str:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-shortest",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return str(output_path)

    @staticmethod
    def concat_clips(clip_paths: List[str], output_path: str) -> str:
        """Concatenates multiple MP4 clips cleanly into a single video."""
        if not clip_paths:
            raise ValueError("clip_paths must contain at least one clip")

        tmp_dir = Path(tempfile.mkdtemp(prefix="wvc_concat_"))
        try:
            list_file = tmp_dir / "clips.txt"
            lines = [
                f"file '{Path(p).resolve().as_posix()}'" for p in clip_paths
            ]
            list_file.write_text("\n".join(lines), encoding="utf-8")
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                str(output_path),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return str(output_path)
        finally:
            shutil.rmtree(str(tmp_dir), ignore_errors=True)
