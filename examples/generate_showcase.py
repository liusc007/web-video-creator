"""
Generate visual showcase assets for web-video-creator documentation:
  - docs/assets/comparison-demo.gif   (AI direct prompt vs web-video-creator)
  - docs/assets/presets-showcase.png  (CCTV / CyberHUD / HUD+Subtitle gallery)

Usage:
    python examples/generate_showcase.py
"""

import asyncio
import base64
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List

from web_video_creator import (
    CCTVScene,
    CompositeScene,
    CyberHUDScene,
    HTMLToVideo,
    HUDScene,
    Scene,
    TimedSubtitleScene,
)


def build_base_sanctuary_scene(duration: float = 2.0) -> Scene:
    """Renders an atmospheric, text-free cinematic sanctuary scene via HTML5 Canvas."""
    html = '<canvas id="stage" width="1280" height="720"></canvas>'
    css = "body { background: #070b12; } canvas { width: 100vw; height: 100vh; display: block; }"
    js = r"""
    (function () {
      const canvas = document.getElementById('stage');
      const ctx = canvas.getContext('2d');
      const W = 1280, H = 720;

      // Deterministic dust particles
      const motes = [];
      for (let i = 0; i < 42; i++) {
        motes.push({
          x: ((i * 193) % W),
          y: ((i * 97) % H),
          r: 1.2 + (i % 4) * 0.7,
          speedY: 14 + (i % 7) * 5,
          drift: (i % 2 === 0 ? 1 : -1) * (4 + (i % 5) * 2),
          alpha: 0.22 + (i % 5) * 0.1
        });
      }

      function drawFrame(tSec) {
        ctx.clearRect(0, 0, W, H);

        // Background moody gradient
        const bg = ctx.createLinearGradient(0, 0, 0, H);
        bg.addColorStop(0, '#070c14');
        bg.addColorStop(0.55, '#101d2e');
        bg.addColorStop(1, '#090e15');
        ctx.fillStyle = bg;
        ctx.fillRect(0, 0, W, H);

        // Perspective architectural pillars
        const pillars = [120, 270, 930, 1080];
        pillars.forEach((px, idx) => {
          const pw = idx === 0 || idx === 3 ? 84 : 62;
          const pg = ctx.createLinearGradient(px, 0, px + pw, 0);
          pg.addColorStop(0, '#09101a');
          pg.addColorStop(0.5, '#19293e');
          pg.addColorStop(1, '#070b12');
          ctx.fillStyle = pg;
          ctx.fillRect(px, 40, pw, H - 140);
          ctx.fillStyle = 'rgba(148, 163, 184, 0.08)';
          ctx.fillRect(px + pw - 4, 40, 4, H - 140);
        });

        // Floor reflection plane
        const floorGrad = ctx.createLinearGradient(0, 520, 0, H);
        floorGrad.addColorStop(0, '#0a121d');
        floorGrad.addColorStop(1, '#04070b');
        ctx.fillStyle = floorGrad;
        ctx.fillRect(0, 520, W, H - 520);

        // Perspective floor lines
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.09)';
        ctx.lineWidth = 1.5;
        for (let i = -5; i <= 5; i++) {
          ctx.beginPath();
          ctx.moveTo(W / 2 + i * 75, 520);
          ctx.lineTo(W / 2 + i * 240, H);
          ctx.stroke();
        }

        // Volumetric sanctuary spotlight beam
        const sway = Math.sin(tSec * 1.4) * 14;
        const beam = ctx.createRadialGradient(W / 2 + sway, 20, 20, W / 2, 340, 480);
        beam.addColorStop(0, 'rgba(251, 191, 36, 0.24)');
        beam.addColorStop(0.45, 'rgba(56, 189, 248, 0.10)');
        beam.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = beam;
        ctx.beginPath();
        ctx.moveTo(W / 2 - 90, 0);
        ctx.lineTo(W / 2 + 90, 0);
        ctx.lineTo(W / 2 + 340 + sway, H);
        ctx.lineTo(W / 2 - 340 + sway, H);
        ctx.closePath();
        ctx.fill();

        // Central figure silhouette (subtle breathing sway)
        const breath = Math.sin(tSec * 2.6) * 2.5;
        const cx = W / 2;
        const cy = 365 + breath;

        // Rim light halo
        const halo = ctx.createRadialGradient(cx, cy - 30, 10, cx, cy, 175);
        halo.addColorStop(0, 'rgba(253, 224, 71, 0.22)');
        halo.addColorStop(0.55, 'rgba(16, 185, 129, 0.08)');
        halo.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = halo;
        ctx.beginPath();
        ctx.arc(cx, cy, 175, 0, Math.PI * 2);
        ctx.fill();

        // Silhouette torso + cloak
        ctx.fillStyle = '#070b11';
        ctx.strokeStyle = 'rgba(251, 191, 36, 0.42)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(cx - 72, 548);
        ctx.quadraticCurveTo(cx - 66, cy - 30, cx - 28, cy - 42);
        ctx.lineTo(cx + 28, cy - 42);
        ctx.quadraticCurveTo(cx + 66, cy - 30, cx + 72, 548);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Head
        ctx.beginPath();
        ctx.arc(cx, cy - 76, 30, 0, Math.PI * 2);
        ctx.fillStyle = '#070b11';
        ctx.fill();
        ctx.strokeStyle = 'rgba(253, 224, 71, 0.55)';
        ctx.stroke();

        // Ambient dust motes
        motes.forEach((m, i) => {
          const y = (m.y - tSec * m.speedY + H * 3) % H;
          const x = (m.x + Math.sin(tSec * 1.8 + i) * m.drift + W) % W;
          ctx.fillStyle = `rgba(253, 230, 138, ${m.alpha})`;
          ctx.beginPath();
          ctx.arc(x, y, m.r, 0, Math.PI * 2);
          ctx.fill();
        });
      }

      window.__wvcOnFrame = function (_progress, elapsedMs) {
        drawFrame((elapsedMs || 0) / 1000.0);
      };
      drawFrame(0);
    })();
    """
    return Scene(html=html, css=css, js=js, duration=duration, transparent=False)


def build_garbled_ai_overlay(duration: float = 2.4) -> Scene:
    """Simulates common generative video artifacts when prompting text/UI directly."""
    html = '<canvas id="garble" width="1280" height="720"></canvas>'
    css = "body { background: transparent !important; } canvas { width: 100vw; height: 100vh; display: block; }"
    js = r"""
    (function () {
      const canvas = document.getElementById('garble');
      const ctx = canvas.getContext('2d');
      const W = 1280, H = 720;
      const garbledTitles = [
        'C4M-07 [S@NCTU4RY]',
        'CΔM-O7 [5ANCTU_RY]',
        'CAM-Q? [SANC7UARV]',
        'C4M-Ø7 [SΛNCTU4RY]'
      ];
      const garbledClocks = [
        'RΞC 89:7?:1X',
        'RE© 22:9B:??',
        'R3C 8Z:45:9$',
        'R£C 2#:71:8X'
      ];
      const garbledSubs = [
        'A1l U1 & subtit1es m3lt3d in pixels...',
        'All Ul & subtitels m3lted in pixe1s...',
        'A1l UI & suptitles melτed 1n pix3ls...',
        'AII U1 & subtit1es m3lt3d in p1xels...'
      ];

      function drawArtifact(elapsedMs) {
        ctx.clearRect(0, 0, W, H);
        const step = Math.floor((elapsedMs || 0) / 120);
        const jx = Math.sin(step * 2.7) * 9;
        const jy = Math.cos(step * 3.1) * 6;
        const skew = Math.sin(step * 1.9) * 0.045;

        // Warped jittering HUD header text
        ctx.save();
        ctx.transform(1, skew, -skew * 0.8, 1, jx, jy);
        ctx.font = 'bold 30px Consolas, monospace';
        ctx.fillStyle = 'rgba(239, 68, 68, 0.88)';
        ctx.fillText(garbledClocks[step % garbledClocks.length], 48, 72);
        ctx.fillStyle = 'rgba(74, 222, 128, 0.78)';
        ctx.fillText(garbledTitles[step % garbledTitles.length], 340 + (step % 3) * 4, 74);
        ctx.restore();

        // Jittering warped bounding box
        ctx.save();
        ctx.translate(430 + jx * 1.4, 180 + jy * 1.2);
        ctx.rotate(Math.sin(step * 1.7) * 0.035);
        ctx.strokeStyle = step % 2 === 0 ? 'rgba(34, 197, 94, 0.85)' : 'rgba(248, 113, 113, 0.85)';
        ctx.lineWidth = 3;
        ctx.strokeRect(0, 0, 390 + (step % 5) * 6, 330 - (step % 4) * 5);

        ctx.fillStyle = 'rgba(15, 23, 42, 0.65)';
        ctx.fillRect(0, -42, 270, 36);
        ctx.font = 'bold 20px Consolas, monospace';
        ctx.fillStyle = '#fca5a5';
        ctx.fillText('SUBJ£CT-0? [42%?]', 10, -17);
        ctx.restore();

        // Melted / double-vision burned-in subtitles
        ctx.save();
        const sx = W / 2 + Math.cos(step * 2.3) * 6;
        const sy = 626 + Math.sin(step * 2.9) * 4;
        ctx.font = 'bold 36px Arial, sans-serif';
        ctx.textAlign = 'center';
        const line = garbledSubs[step % garbledSubs.length];
        ctx.fillStyle = 'rgba(239, 68, 68, 0.65)';
        ctx.fillText(line, sx - 3, sy - 2);
        ctx.fillStyle = 'rgba(56, 189, 248, 0.65)';
        ctx.fillText(line, sx + 3, sy + 2);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.92)';
        ctx.fillText(line, sx, sy);
        ctx.restore();
      }

      window.__wvcOnFrame = function (_progress, elapsedMs) {
        drawArtifact(elapsedMs || 0);
      };
      drawArtifact(0);
    })();
    """
    return Scene(html=html, css=css, js=js, duration=duration, transparent=True)


def build_wvc_composite(duration: float = 2.4) -> CompositeScene:
    """Real CompositeScene using CCTVScene + TimedSubtitleScene with Whisper words."""
    cctv = CCTVScene(
        title="CAM-07 [SANCTUARY]",
        location="INNER HALL // 35° MOUNT",
        timestamp_text="2026-11-12 22:45:12.000",
        status_text="REC ●",
        color_theme="emerald",
        telemetry_left="ISO 800 // F1.8 // 1/60s // TPAD +0.35s",
        telemetry_right="WEB-VIDEO-CREATOR // DETERMINISTIC",
        targets=[
            {
                "x": 36,
                "y": 23,
                "w": 28,
                "h": 54,
                "label": "SUBJECT-01",
                "confidence": "99.8%",
                "metrics": {"PULSE": "142 BPM", "SYNC": "LOCKED"},
            }
        ],
        duration=duration,
    )
    whisper_data = {
        "segments": [
            {
                "start": 0.0,
                "end": 2.2,
                "text": "所有 UI、时间码与双语字幕，全部代码合成。",
                "translation": "Deterministic HTML5/CSS3 overlays + Whisper sync.",
                "words": [
                    {"word": "所有 ", "start": 0.0, "end": 0.35},
                    {"word": "UI、", "start": 0.35, "end": 0.70},
                    {"word": "时间码与", "start": 0.70, "end": 1.15},
                    {"word": "双语字幕，", "start": 1.15, "end": 1.60},
                    {"word": "全部代码合成。", "start": 1.60, "end": 2.20},
                ],
            }
        ]
    }
    subs = TimedSubtitleScene.from_whisper(
        whisper_data,
        offset=0.25,
        position="bottom",
        style="cinema",
        font_size="40px",
        duration=duration,
    )
    return CompositeScene(layers=[cctv, subs], duration=duration)


def build_banner_scene(duration: float = 2.4) -> Scene:
    """Generates a crisp transparent header/footer comparison frame around the 2 videos."""
    html = """
    <div class="frame">
      <div class="top-bar">
        <div class="pill bad">❌ Prompting AI Video Directly — Warped HUD &amp; Garbled Text</div>
        <div class="pill good">✅ web-video-creator — Deterministic HTML5/CSS3 + Whisper Sync</div>
      </div>
      <div class="bottom-bar">
        <span>Tier 1 · FFmpeg tpad Breathing Padding</span>
        <span>•</span>
        <span>Tier 2 · Playwright Transparent Web Compositor</span>
        <span>•</span>
        <span>Tier 3 · Spatial Hall Reverb</span>
      </div>
    </div>
    """
    css = """
    body {
      width: 100vw; height: 100vh;
      background: #0d1117;
      font-family: "Inter", "Segoe UI", "Microsoft YaHei", sans-serif;
      color: #e6edf3;
    }
    .frame {
      width: 100vw; height: 100vh;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 12px 18px;
    }
    .top-bar {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
    .pill {
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 700;
      text-align: center;
      letter-spacing: 0.3px;
    }
    .pill.bad {
      background: rgba(239, 68, 68, 0.14);
      border: 1px solid rgba(239, 68, 68, 0.45);
      color: #fca5a5;
    }
    .pill.good {
      background: rgba(16, 185, 129, 0.14);
      border: 1px solid rgba(16, 185, 129, 0.5);
      color: #6ee7b7;
    }
    .bottom-bar {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 14px;
      font-size: 13px;
      color: #94a3b8;
      letter-spacing: 0.4px;
    }
    """
    return Scene(html=html, css=css, duration=duration, transparent=False)


def build_presets_gallery_html(panel_imgs: List[Dict[str, str]]) -> str:
    cards = ""
    for p in panel_imgs:
        cards += f"""
        <div class="card">
          <img src="{p['data_uri']}" />
          <div class="cap">
            <span class="badge">{p['tag']}</span>
            <span class="title">{p['label']}</span>
          </div>
        </div>
        """
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: 1200px; height: 312px;
  background: #0d1117;
  font-family: "Inter", "Segoe UI", "Microsoft YaHei", sans-serif;
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}}
.card {{
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}}
.card img {{
  width: 100%;
  height: 214px;
  object-fit: contain;
  background: #05080c;
  display: block;
}}
.cap {{
  flex: 1;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e6edf3;
  font-size: 13px;
  font-weight: 600;
}}
.badge {{
  background: rgba(6, 182, 212, 0.16);
  color: #67e8f9;
  border: 1px solid rgba(6, 182, 212, 0.4);
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-family: Consolas, monospace;
}}
</style>
</head>
<body>{cards}</body>
</html>"""


async def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    assets_dir = repo_root / "docs" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    work = Path(tempfile.mkdtemp(prefix="wvc_showcase_"))
    try:
        raw_clip = work / "base_raw.mp4"
        padded_clip = work / "base_padded.mp4"
        left_clip = work / "left_ai_garbled.mp4"
        right_clip = work / "right_wvc_real.mp4"
        banner_clip = work / "banner_bg.mp4"
        composed_mp4 = work / "comparison.mp4"
        palette_png = work / "palette.png"
        gif_out = assets_dir / "comparison-demo.gif"

        # 1. Render base clean clip (1.9s) and apply Tier 1 tpad -> 2.4s
        base_conv = HTMLToVideo(width=1280, height=720, fps=12)
        await base_conv.render_scenes([build_base_sanctuary_scene(duration=1.9)], str(raw_clip))
        HTMLToVideo.apply_smart_padding(
            str(raw_clip), str(padded_clip), start_duration=0.25, stop_duration=0.25
        )

        # 2. Overlay left (simulated AI hallucination) & right (real web-video-creator)
        await base_conv.overlay_scenes_on_video(
            str(padded_clip), [build_garbled_ai_overlay(duration=2.4)], str(left_clip)
        )
        await base_conv.overlay_scenes_on_video(
            str(padded_clip), [build_wvc_composite(duration=2.4)], str(right_clip)
        )

        # 3. Render sleek GitHub-dark background frame (1120x380) and place 2 panels (534x300 each)
        banner_conv = HTMLToVideo(width=1120, height=382, fps=12)
        await banner_conv.render_scenes([build_banner_scene(duration=2.4)], str(banner_clip))

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(banner_clip),
                "-i", str(left_clip),
                "-i", str(right_clip),
                "-filter_complex",
                "[1:v]scale=534:300[l];[2:v]scale=534:300[r];"
                "[0:v][l]overlay=18:48[bg1];[bg1][r]overlay=568:48[out]",
                "-map", "[out]",
                "-t", "2.4",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(composed_mp4),
            ],
            check=True,
            capture_output=True,
        )

        # 4. Two-pass crisp palette GIF for GitHub README
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(composed_mp4),
                "-vf", "fps=12,palettegen=stats_mode=diff",
                str(palette_png),
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(composed_mp4),
                "-i", str(palette_png),
                "-lavfi", "fps=12[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3",
                str(gif_out),
            ],
            check=True,
            capture_output=True,
        )

        # 5. Render 3-preset gallery PNG (CCTV emerald, CyberHUD cyan, HUD amber + Neon subtitle)
        preset_specs = [
            (
                "cctv",
                "CCTVScene",
                "Surveillance HUD · Emerald",
                CompositeScene(
                    layers=[
                        CCTVScene(
                            title="CAM-07 [SANCTUARY]",
                            location="35° CEILING MOUNT",
                            timestamp_text="2026-11-12 22:45:12.640",
                            color_theme="emerald",
                            targets=[
                                {
                                    "x": 36, "y": 23, "w": 28, "h": 54,
                                    "label": "SUBJECT-01",
                                    "confidence": "99.8%",
                                    "metrics": {"PULSE": "142 BPM", "SYNC": "LOCKED"},
                                }
                            ],
                            duration=1.5,
                        ),
                        TimedSubtitleScene(
                            cues=[
                                {
                                    "start": 0.0,
                                    "end": 1.5,
                                    "text": "监控 HUD 与动态时间码",
                                    "translation": "CCTVScene + terminal subtitles",
                                }
                            ],
                            style="cctv",
                            font_size="40px",
                            duration=1.5,
                        ),
                    ],
                    duration=1.5,
                ),
            ),
            (
                "cyber",
                "CyberHUDScene",
                "Radar + Scan Beam · Cyan",
                CompositeScene(
                    layers=[
                        CyberHUDScene(
                            title="TAC-OS // UNIT-07",
                            location="SECTOR 04 :: SCAN",
                            timestamp_text="2026-11-12 22:45:12.640",
                            color_theme="cyan",
                            targets=[
                                {
                                    "x": 36, "y": 23, "w": 28, "h": 54,
                                    "label": "ENTITY-07",
                                    "confidence": "99.4%",
                                    "metrics": {"LOCK": "ACTIVE", "RANGE": "4.2m"},
                                }
                            ],
                            duration=1.5,
                        ),
                        TimedSubtitleScene(
                            cues=[
                                {
                                    "start": 0.0,
                                    "end": 1.5,
                                    "text": "赛博战术扫描与旋转雷达",
                                    "translation": "CyberHUDScene + neon captions",
                                }
                            ],
                            style="neon",
                            font_size="40px",
                            duration=1.5,
                        ),
                    ],
                    duration=1.5,
                ),
            ),
            (
                "amber",
                "HUDScene",
                "Amber Telemetry + Karaoke",
                CompositeScene(
                    layers=[
                        HUDScene(
                            title="CAM-02 [EAST_WING]",
                            location="ARCHIVE CORRIDOR",
                            timestamp_text="2026-11-12 22:45:12.640",
                            status_text="LIVE",
                            color_theme="amber",
                            targets=[
                                {
                                    "x": 36, "y": 23, "w": 28, "h": 54,
                                    "label": "SPEAKER-A",
                                    "confidence": "98.9%",
                                    "metrics": {"AUDIO": "HALL REVERB", "TPAD": "+0.35s"},
                                }
                            ],
                            duration=1.5,
                        ),
                        TimedSubtitleScene(
                            cues=[
                                {
                                    "start": 0.0,
                                    "end": 1.5,
                                    "text": "逐词卡点高亮字幕",
                                    "translation": "Word-level Whisper highlight",
                                    "words": [
                                        {"word": "逐词", "start": 0.0, "end": 0.4},
                                        {"word": "卡点高亮", "start": 0.4, "end": 1.0},
                                        {"word": "字幕", "start": 1.0, "end": 1.5},
                                    ],
                                }
                            ],
                            style="cinema",
                            font_size="42px",
                            duration=1.5,
                        ),
                    ],
                    duration=1.5,
                ),
            ),
        ]

        panel_imgs: List[Dict[str, str]] = []
        still_conv = HTMLToVideo(width=1280, height=720, fps=5)
        for key, tag, label, comp in preset_specs:
            vid = work / f"preset_{key}.mp4"
            png = work / f"preset_{key}.png"
            await still_conv.overlay_scenes_on_video(str(padded_clip), [comp], str(vid))
            subprocess.run(
                ["ffmpeg", "-y", "-ss", "0.7", "-i", str(vid), "-frames:v", "1", str(png)],
                check=True,
                capture_output=True,
            )
            b64 = base64.b64encode(png.read_bytes()).decode("ascii")
            panel_imgs.append(
                {
                    "tag": tag,
                    "label": label,
                    "data_uri": f"data:image/png;base64,{b64}",
                }
            )

        gallery_html = build_presets_gallery_html(panel_imgs)
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await still_conv._launch_browser(p)
            try:
                page = await browser.new_page(viewport={"width": 1200, "height": 312})
                await page.set_content(gallery_html, wait_until="load")
                await page.screenshot(path=str(assets_dir / "presets-showcase.png"))
                await page.close()
            finally:
                await browser.close()

        print(f"Generated: {gif_out} ({gif_out.stat().st_size // 1024} KB)")
        gallery_path = assets_dir / "presets-showcase.png"
        print(f"Generated: {gallery_path} ({gallery_path.stat().st_size // 1024} KB)")
    finally:
        shutil.rmtree(str(work), ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
