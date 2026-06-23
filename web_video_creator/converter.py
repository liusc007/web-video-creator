import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .scene import Scene


class HTMLToVideo:
    def __init__(self, width: int = 1920, height: int = 1080, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps

    async def render_scenes(
        self, scenes: list[Scene], output_path: str
    ) -> str:
        frames_dir = Path(tempfile.mkdtemp())
        try:
            total_frames = 0
            for i, scene in enumerate(scenes):
                html = scene.to_html()
                html_path = frames_dir / f"scene_{i}.html"
                html_path.write_text(html, encoding="utf-8")

                scene_frames = int(scene.duration * self.fps)
                await self._capture_scene(
                    str(html_path), frames_dir, i, scene_frames
                )
                total_frames += scene_frames

            self._encode_video(str(frames_dir), output_path, total_frames)
            return output_path
        finally:
            import shutil
            shutil.rmtree(str(frames_dir), ignore_errors=True)

    async def _capture_scene(
        self, html_path: str, frames_dir: Path,
        scene_index: int, total_frames: int
    ):
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(
                viewport={"width": self.width, "height": self.height}
            )
            await page.goto(f"file://{html_path}", wait_until="networkidle")

            for frame_num in range(total_frames):
                progress = frame_num / max(total_frames - 1, 1)
                await page.evaluate(f"""
                    document.body.style.setProperty('--hf-progress', '{progress}');
                    window.__hfProgress = {progress};
                """)
                await page.screenshot(
                    path=str(frames_dir / f"frame_{scene_index}_{frame_num:06d}.png"),
                    full_page=False
                )

            await browser.close()

    def _encode_video(
        self, frames_dir: str, output_path: str, total_frames: int
    ):
        pattern = f"{frames_dir}/frame_%d_%06d.png"
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(self.fps),
            "-pattern_type", "glob",
            "-i", f"{frames_dir}/frame_*.png",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-crf", "18",
            "-vf", f"scale={self.width}:{self.height}",
            output_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    def add_audio(
        self, video_path: str, audio_path: str, output_path: str
    ) -> str:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest", output_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
