import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_DEFAULT_FONT_SANS = (
    '"PingFang SC", "Microsoft YaHei", "Noto Sans SC", "Inter", '
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
)
_DEFAULT_FONT_MONO = (
    '"JetBrains Mono", "Cascadia Mono", "SF Mono", "Share Tech Mono", '
    'Consolas, "Courier New", monospace'
)


def _font_import_css(font_url: Optional[str]) -> str:
    if font_url:
        return f"@import url('{font_url}');\n"
    return ""


@dataclass
class Scene:
    html: str = ""
    duration: float = 5.0
    css: str = ""
    js: str = ""
    transparent: bool = False

    def to_html(self) -> str:
        stripped = self.html.lstrip()
        lower_head = stripped[:200].lower()
        if lower_head.startswith("<!doctype") or lower_head.startswith("<html"):
            if self.transparent and "</head>" in self.html:
                inject = "<style>html,body{background:transparent !important;}</style></head>"
                return self.html.replace("</head>", inject, 1)
            return self.html

        bg_style = "background: transparent !important;" if self.transparent else ""
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{
  width: 100%;
  height: 100%;
  overflow: hidden;
  {bg_style}
}}
{self.css}
</style>
</head>
<body>
{self.html}
<script>
{self.js}
</script>
</body>
</html>"""


@dataclass
class TextScene(Scene):
    text: str = ""
    font_size: str = "48px"
    color: str = "#ffffff"
    bg_color: str = "#1a1a2e"
    animation: str = "fadeIn"

    def __post_init__(self):
        css = f"""
body {{
  width: 100vw; height: 100vh;
  display: flex; align-items: center; justify-content: center;
  background: {self.bg_color};
  font-family: {_DEFAULT_FONT_SANS};
  overflow: hidden;
}}
.text {{
  font-size: {self.font_size}; color: {self.color};
  text-align: center; padding: 60px;
  line-height: 1.6; max-width: 82%;
  animation: {self.animation} 1s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}
@keyframes fadeIn {{
  from {{ opacity: 0; transform: translateY(30px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes slideIn {{
  from {{ opacity: 0; transform: translateX(-60px); }}
  to {{ opacity: 1; transform: translateX(0); }}
}}
@keyframes scaleIn {{
  from {{ opacity: 0; transform: scale(0.85); }}
  to {{ opacity: 1; transform: scale(1); }}
}}
@keyframes typewriter {{
  from {{ clip-path: inset(0 100% 0 0); }}
  to {{ clip-path: inset(0 0 0 0); }}
}}
"""
        html = f'<div class="text">{self.text}</div>'
        object.__setattr__(self, "css", css)
        object.__setattr__(self, "html", html)


@dataclass
class ImageScene(Scene):
    image_url: str = ""
    caption: str = ""

    def __post_init__(self):
        html = (
            f'<img src="{self.image_url}" '
            f'style="max-width:90%;max-height:78%;object-fit:contain;">'
        )
        if self.caption:
            html += (
                '<p style="color:#fff;font-size:28px;margin-top:24px;'
                f'letter-spacing:1px;">{self.caption}</p>'
            )
        css = f"""
body {{
  width: 100vw; height: 100vh;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  background: #0f0f23; font-family: {_DEFAULT_FONT_SANS};
}}
"""
        object.__setattr__(self, "css", css)
        object.__setattr__(self, "html", html)


@dataclass
class HUDScene(Scene):
    """
    Cinematic HUD / Overlay Scene designed specifically for AI video post-production.
    Renders with a transparent background by default to be overlaid directly on raw AI clips.
    """

    title: str = "CAM-01 [ZONE-A]"
    location: str = "NORTH PERIMETER"
    timestamp_text: str = "2026-11-10 22:45:12.804"
    status_text: str = "REC"
    targets: List[Dict[str, Any]] = field(default_factory=list)
    show_rec_dot: bool = True
    show_grid: bool = True
    show_brackets: bool = True
    show_scanlines: bool = True
    color_theme: str = "emerald"  # emerald, amber, cyan, crimson, monochrome
    telemetry_left: str = "ISO 800 // F1.8 // 1/60s // 30FPS HD"
    telemetry_right: str = "AI TRACKING LOCKED // WVC-HUD"
    font_url: Optional[str] = None
    transparent: bool = True

    def __post_init__(self):
        themes = {
            "emerald": {
                "primary": "#10b981",
                "glow": "rgba(16, 185, 129, 0.45)",
                "bg_subtle": "rgba(16, 185, 129, 0.08)",
            },
            "amber": {
                "primary": "#f59e0b",
                "glow": "rgba(245, 158, 11, 0.45)",
                "bg_subtle": "rgba(245, 158, 11, 0.08)",
            },
            "cyan": {
                "primary": "#06b6d4",
                "glow": "rgba(6, 182, 212, 0.45)",
                "bg_subtle": "rgba(6, 182, 212, 0.08)",
            },
            "crimson": {
                "primary": "#ef4444",
                "glow": "rgba(239, 68, 68, 0.45)",
                "bg_subtle": "rgba(239, 68, 68, 0.08)",
            },
            "monochrome": {
                "primary": "#e2e8f0",
                "glow": "rgba(226, 232, 240, 0.35)",
                "bg_subtle": "rgba(255, 255, 255, 0.06)",
            },
        }
        theme = themes.get(self.color_theme, themes["emerald"])
        p_color = theme["primary"]
        glow = theme["glow"]
        bg_subtle = theme["bg_subtle"]

        rec_dot_html = '<span class="rec-dot"></span>' if self.show_rec_dot else ""
        grid_html = '<div class="hud-grid"></div>' if self.show_grid else ""
        scanlines_html = '<div class="hud-scanlines"></div>' if self.show_scanlines else ""
        brackets_html = (
            """
        <div class="corner-bracket top-left"></div>
        <div class="corner-bracket top-right"></div>
        <div class="corner-bracket bottom-left"></div>
        <div class="corner-bracket bottom-right"></div>
        """
            if self.show_brackets
            else ""
        )

        targets_html = ""
        for idx, t in enumerate(self.targets):
            x = t.get("x", 50)
            y = t.get("y", 50)
            w = t.get("w", 20)
            h = t.get("h", 25)
            label = t.get("label", f"TARGET-{idx+1:02d}")
            confidence = t.get("confidence", "99.1%")
            metrics = t.get("metrics", {})
            metrics_str = "".join(
                f'<div class="metric-row"><span>{k}:</span> <span>{v}</span></div>'
                for k, v in metrics.items()
            )

            targets_html += f"""
            <div class="target-box" style="left:{x}%; top:{y}%; width:{w}%; height:{h}%;">
              <div class="target-reticle"></div>
              <div class="target-info">
                <div class="target-title">{label} <span class="target-conf">[{confidence}]</span></div>
                {metrics_str}
              </div>
            </div>
            """

        extra_body_html = self._extra_body_html()
        extra_css = self._extra_css(p_color, glow, bg_subtle)

        html = f"""
        <div class="hud-container">
          {grid_html}
          {scanlines_html}
          {brackets_html}
          {extra_body_html}

          <div class="hud-header">
            <div class="header-left">
              <div class="hud-tag">{rec_dot_html} {self.status_text}</div>
              <div class="hud-cam">{self.title}</div>
            </div>
            <div class="header-right">
              <div class="hud-loc">{self.location}</div>
              <div class="hud-time" id="hud-timer">{self.timestamp_text}</div>
            </div>
          </div>

          <div class="hud-body">
            {targets_html}
          </div>

          <div class="hud-footer">
            <div class="footer-left">{self.telemetry_left}</div>
            <div class="footer-right">{self.telemetry_right}</div>
          </div>
        </div>
        """

        css = f"""
        {_font_import_css(self.font_url)}
        body {{
          width: 100vw; height: 100vh;
          background: {"transparent" if self.transparent else "#05080c"};
          color: {p_color};
          font-family: {_DEFAULT_FONT_MONO};
          user-select: none;
        }}
        .hud-container {{
          position: relative;
          width: 100vw;
          height: 100vh;
          padding: 4.8vh 4.2vw;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          text-shadow: 0 1px 4px rgba(0, 0, 0, 0.85), 0 0 8px {glow};
        }}
        .hud-grid {{
          position: absolute;
          inset: 0;
          background-image:
            linear-gradient(to right, {bg_subtle} 1px, transparent 1px),
            linear-gradient(to bottom, {bg_subtle} 1px, transparent 1px);
          background-size: 120px 120px;
          opacity: 0.35;
          pointer-events: none;
        }}
        .hud-scanlines {{
          position: absolute;
          inset: 0;
          background: repeating-linear-gradient(
            to bottom,
            rgba(0, 0, 0, 0) 0px,
            rgba(0, 0, 0, 0) 3px,
            rgba(0, 0, 0, 0.14) 4px
          );
          pointer-events: none;
          opacity: 0.55;
        }}
        .corner-bracket {{
          position: absolute;
          width: 34px;
          height: 34px;
          border: 3px solid {p_color};
          opacity: 0.88;
        }}
        .top-left {{ top: 2.2vh; left: 2.0vw; border-right: none; border-bottom: none; }}
        .top-right {{ top: 2.2vh; right: 2.0vw; border-left: none; border-bottom: none; }}
        .bottom-left {{ bottom: 2.2vh; left: 2.0vw; border-right: none; border-top: none; }}
        .bottom-right {{ bottom: 2.2vh; right: 2.0vw; border-left: none; border-top: none; }}

        .hud-header, .hud-footer {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          z-index: 10;
        }}
        .header-left, .header-right {{
          display: flex;
          align-items: center;
          gap: 18px;
        }}
        .hud-tag {{
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: {bg_subtle};
          border: 1px solid {p_color};
          padding: 4px 14px;
          border-radius: 4px;
          font-weight: 700;
          font-size: 20px;
          letter-spacing: 2px;
        }}
        .rec-dot {{
          width: 12px;
          height: 12px;
          background: #ef4444;
          border-radius: 50%;
          box-shadow: 0 0 10px #ef4444;
          animation: blink 1s infinite alternate;
        }}
        @keyframes blink {{
          0% {{ opacity: 0.2; }}
          100% {{ opacity: 1; }}
        }}
        .hud-cam {{
          font-size: 24px;
          letter-spacing: 2.5px;
          font-weight: 700;
        }}
        .hud-loc {{
          font-size: 18px;
          opacity: 0.85;
          letter-spacing: 2px;
        }}
        .hud-time {{
          font-size: 24px;
          font-weight: 700;
          letter-spacing: 2px;
          font-variant-numeric: tabular-nums;
        }}
        .hud-body {{
          position: relative;
          flex: 1;
          margin: 20px 0;
        }}
        .target-box {{
          position: absolute;
          border: 2px dashed {p_color};
          background: {bg_subtle};
          box-shadow: 0 0 14px {glow};
          border-radius: 2px;
          animation: pulseBox 3s infinite ease-in-out;
        }}
        @keyframes pulseBox {{
          0%, 100% {{ border-color: {p_color}; }}
          50% {{ border-color: rgba(255, 255, 255, 0.9); }}
        }}
        .target-reticle {{
          position: absolute;
          inset: 0;
        }}
        .target-reticle::before, .target-reticle::after {{
          content: '';
          position: absolute;
          background: {p_color};
        }}
        .target-reticle::before {{ top: 50%; left: -8px; width: 16px; height: 2px; }}
        .target-reticle::after {{ left: 50%; top: -8px; width: 2px; height: 16px; }}

        .target-info {{
          position: absolute;
          bottom: calc(100% + 8px);
          left: 0;
          background: rgba(5, 8, 12, 0.85);
          backdrop-filter: blur(8px);
          border: 1px solid {p_color};
          padding: 8px 12px;
          border-radius: 4px;
          white-space: nowrap;
          font-size: 15px;
          line-height: 1.4;
          box-shadow: 0 0 10px {glow};
        }}
        .target-title {{
          font-weight: 700;
          font-size: 17px;
          color: #fff;
          margin-bottom: 2px;
        }}
        .target-conf {{
          color: {p_color};
        }}
        .metric-row {{
          display: flex;
          gap: 8px;
          font-size: 14px;
          opacity: 0.92;
        }}
        .hud-footer {{
          font-size: 17px;
          letter-spacing: 2px;
          opacity: 0.85;
          border-top: 1px solid {bg_subtle};
          padding-top: 14px;
        }}
        {extra_css}
        """

        duration_ms = int(round(self.duration * 1000))
        js = f"""
        (function() {{
          const timerEl = document.getElementById('hud-timer');
          const durationMs = {duration_ms};
          if (!timerEl) return;
          const originalText = timerEl.textContent.trim();
          const m = originalText.match(/^(.*?)(\\d{{2}}):(\\d{{2}}):(\\d{{2}})\\.(\\d{{3}})(.*)$/);
          if (!m) return;
          const prefix = m[1];
          const baseTotalMs =
            (parseInt(m[2], 10) * 3600 + parseInt(m[3], 10) * 60 + parseInt(m[4], 10)) * 1000 +
            parseInt(m[5], 10);
          const suffix = m[6];

          function formatClock(totalMs) {{
            const dayMs = 86400000;
            const wrapped = ((Math.floor(totalMs) % dayMs) + dayMs) % dayMs;
            const hh = Math.floor(wrapped / 3600000);
            const mm = Math.floor((wrapped % 3600000) / 60000);
            const ss = Math.floor((wrapped % 60000) / 1000);
            const ms = wrapped % 1000;
            return (
              prefix +
              String(hh).padStart(2, '0') + ':' +
              String(mm).padStart(2, '0') + ':' +
              String(ss).padStart(2, '0') + '.' +
              String(ms).padStart(3, '0') +
              suffix
            );
          }}

          window.__wvcOnFrame = function(progress, elapsedMs) {{
            const offset = typeof elapsedMs === 'number' ? elapsedMs : (progress || 0) * durationMs;
            timerEl.textContent = formatClock(baseTotalMs + offset);
          }};
        }})();
        """

        object.__setattr__(self, "css", css)
        object.__setattr__(self, "html", html)
        object.__setattr__(self, "js", js)

    def _extra_body_html(self) -> str:
        return ""

    def _extra_css(self, primary: str, glow: str, bg_subtle: str) -> str:
        return ""


@dataclass
class CCTVScene(HUDScene):
    """Convenience preset specifically styled for surveillance camera footage."""

    title: str = "CAM-03 [TEMPLE_HALL]"
    location: str = "INNER PALACE 35° DOWN"
    status_text: str = "REC ●"
    color_theme: str = "emerald"
    show_scanlines: bool = True


@dataclass
class CyberHUDScene(HUDScene):
    """Futuristic tactical scanner overlay with animated scan beam and SVG reticle."""

    title: str = "TAC-OS // UNIT-07"
    location: str = "SECTOR 04 :: ACTIVE SCAN"
    status_text: str = "LOCKED"
    color_theme: str = "cyan"
    show_scanlines: bool = True
    telemetry_left: str = "FOV 85° // LIDAR SYNC // 30FPS"
    telemetry_right: str = "NEURAL OVERLAY // ENGINE v0.2"

    def _extra_body_html(self) -> str:
        return """
        <div class="cyber-scanbeam"></div>
        <div class="cyber-radar" aria-hidden="true">
          <svg viewBox="0 0 120 120" width="96" height="96">
            <circle cx="60" cy="60" r="52" class="radar-ring" />
            <circle cx="60" cy="60" r="32" class="radar-ring inner" />
            <line x1="60" y1="60" x2="60" y2="8" class="radar-sweep" />
          </svg>
        </div>
        """

    def _extra_css(self, primary: str, glow: str, bg_subtle: str) -> str:
        return f"""
        .cyber-scanbeam {{
          position: absolute;
          left: 0;
          right: 0;
          height: 3px;
          background: linear-gradient(90deg, transparent, {primary}, transparent);
          box-shadow: 0 0 18px {glow};
          opacity: 0.55;
          pointer-events: none;
          animation: scanBeam 4s linear infinite;
        }}
        @keyframes scanBeam {{
          0% {{ top: 8%; }}
          100% {{ top: 92%; }}
        }}
        .cyber-radar {{
          position: absolute;
          right: 48px;
          bottom: 92px;
          opacity: 0.78;
          pointer-events: none;
          z-index: 9;
        }}
        .radar-ring {{
          fill: {bg_subtle};
          stroke: {primary};
          stroke-width: 1.5;
          stroke-dasharray: 6 4;
        }}
        .radar-ring.inner {{
          fill: none;
          opacity: 0.6;
        }}
        .radar-sweep {{
          stroke: {primary};
          stroke-width: 2;
          transform-origin: 60px 60px;
          animation: radarSpin 3s linear infinite;
        }}
        @keyframes radarSpin {{
          from {{ transform: rotate(0deg); }}
          to {{ transform: rotate(360deg); }}
        }}
        """


@dataclass
class SubtitleScene(Scene):
    """
    Broadcast & Cinema grade single-card Subtitle Overlay.
    Supports primary text, secondary translation, and backdrop blur.
    """

    text: str = ""
    translation: str = ""
    position: str = "bottom"  # bottom, top, center
    style: str = "cinema"  # cinema, netflix, neon, cctv
    font_size: str = "36px"
    font_url: Optional[str] = None
    transparent: bool = True

    def __post_init__(self):
        translation_html = (
            f'<div class="sub-trans">{self.translation}</div>' if self.translation else ""
        )
        html = f"""
        <div class="subtitle-wrap {self.position} {self.style}">
          <div class="subtitle-box">
            <div class="sub-primary">{self.text}</div>
            {translation_html}
          </div>
        </div>
        """

        css = f"""
        {_font_import_css(self.font_url)}
        body {{
          width: 100vw; height: 100vh;
          background: {"transparent" if self.transparent else "#000"};
          font-family: {_DEFAULT_FONT_SANS};
          overflow: hidden;
        }}
        .subtitle-wrap {{
          position: absolute;
          left: 0; right: 0;
          display: flex;
          justify-content: center;
          align-items: center;
          padding: 0 7vw;
          pointer-events: none;
        }}
        .subtitle-wrap.bottom {{ bottom: 6.5vh; }}
        .subtitle-wrap.top {{ top: 6.5vh; }}
        .subtitle-wrap.center {{ top: 50%; transform: translateY(-50%); }}

        .subtitle-box {{
          background: rgba(10, 10, 15, 0.68);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border: 1px solid rgba(255, 255, 255, 0.14);
          border-radius: 12px;
          padding: 16px 36px;
          text-align: center;
          max-width: 85%;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
          animation: subFadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }}
        @keyframes subFadeIn {{
          from {{ opacity: 0; transform: translateY(12px); }}
          to {{ opacity: 1; transform: translateY(0); }}
        }}
        .sub-primary {{
          font-size: {self.font_size};
          font-weight: 700;
          color: #ffffff;
          line-height: 1.4;
          letter-spacing: 1.5px;
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
        }}
        .sub-trans {{
          font-size: calc({self.font_size} * 0.58);
          font-weight: 500;
          color: #d1d5db;
          margin-top: 6px;
          letter-spacing: 0.5px;
          text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
        }}
        .netflix .subtitle-box {{
          background: transparent;
          backdrop-filter: none;
          border: none;
          box-shadow: none;
        }}
        .netflix .sub-primary {{
          text-shadow: 0 3px 10px rgba(0, 0, 0, 0.95), 0 0 3px rgba(0, 0, 0, 0.95);
        }}
        .neon .subtitle-box {{
          border-color: #06b6d4;
          box-shadow: 0 0 20px rgba(6, 182, 212, 0.35);
        }}
        .neon .sub-primary {{
          color: #a5f3fc;
          text-shadow: 0 0 12px rgba(6, 182, 212, 0.7);
        }}
        .cctv .subtitle-box {{
          background: rgba(5, 10, 8, 0.82);
          border: 1px solid #10b981;
          border-radius: 4px;
          font-family: {_DEFAULT_FONT_MONO};
        }}
        .cctv .sub-primary {{
          color: #d1fae5;
        }}
        """

        object.__setattr__(self, "css", css)
        object.__setattr__(self, "html", html)


@dataclass
class TimedSubtitleScene(Scene):
    """
    Timestamped & Whisper-ready bilingual subtitle track overlay.
    Supports cue start/end windows, optional word-level active highlighting,
    and smart time offset (e.g. +0.35s to match FFmpeg tpad breathing frames).
    """

    cues: List[Dict[str, Any]] = field(default_factory=list)
    offset: float = 0.0
    position: str = "bottom"  # bottom, top, center
    style: str = "cinema"  # cinema, netflix, neon, cctv
    font_size: str = "36px"
    highlight_color: str = "#fbbf24"
    font_url: Optional[str] = None
    transparent: bool = True

    def __post_init__(self):
        cues_json = json.dumps(self.cues, ensure_ascii=False)
        offset_ms = round(self.offset * 1000.0, 2)
        duration_ms = round(self.duration * 1000.0, 2)

        html = f"""
        <div class="subtitle-wrap {self.position} {self.style}" id="wvc-timed-wrap" style="opacity:0;">
          <div class="subtitle-box">
            <div class="sub-primary" id="wvc-timed-primary"></div>
            <div class="sub-trans" id="wvc-timed-trans" style="display:none;"></div>
          </div>
        </div>
        """

        css = f"""
        {_font_import_css(self.font_url)}
        body {{
          width: 100vw; height: 100vh;
          background: {"transparent" if self.transparent else "#000"};
          font-family: {_DEFAULT_FONT_SANS};
          overflow: hidden;
        }}
        .subtitle-wrap {{
          position: absolute;
          left: 0; right: 0;
          display: flex;
          justify-content: center;
          align-items: center;
          padding: 0 7vw;
          pointer-events: none;
          transition: none;
        }}
        .subtitle-wrap.bottom {{ bottom: 6.8vh; }}
        .subtitle-wrap.top {{ top: 6.8vh; }}
        .subtitle-wrap.center {{ top: 50%; transform: translateY(-50%); }}

        .subtitle-box {{
          background: rgba(10, 10, 15, 0.72);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border: 1px solid rgba(255, 255, 255, 0.14);
          border-radius: 12px;
          padding: 16px 36px;
          text-align: center;
          max-width: 86%;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }}
        .sub-primary {{
          font-size: {self.font_size};
          font-weight: 700;
          color: #ffffff;
          line-height: 1.45;
          letter-spacing: 1.2px;
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.85);
        }}
        .sub-trans {{
          font-size: calc({self.font_size} * 0.56);
          font-weight: 500;
          color: #d1d5db;
          margin-top: 6px;
          letter-spacing: 0.4px;
          text-shadow: 0 1px 3px rgba(0, 0, 0, 0.85);
        }}
        .wvc-word {{
          transition: none;
          color: rgba(255, 255, 255, 0.82);
        }}
        .wvc-word.spoken {{
          color: #ffffff;
        }}
        .wvc-word.active {{
          color: {self.highlight_color};
          text-shadow: 0 0 12px rgba(251, 191, 36, 0.55);
        }}
        .netflix .subtitle-box {{
          background: transparent;
          backdrop-filter: none;
          border: none;
          box-shadow: none;
        }}
        .netflix .sub-primary {{
          text-shadow: 0 3px 10px rgba(0, 0, 0, 0.95), 0 0 4px rgba(0, 0, 0, 0.95);
        }}
        .neon .subtitle-box {{
          border-color: #06b6d4;
          box-shadow: 0 0 20px rgba(6, 182, 212, 0.35);
        }}
        .cctv .subtitle-box {{
          background: rgba(5, 10, 8, 0.84);
          border: 1px solid #10b981;
          border-radius: 4px;
          font-family: {_DEFAULT_FONT_MONO};
        }}
        """

        js = f"""
        (function() {{
          const cues = {cues_json};
          const offsetMs = {offset_ms};
          const durationMs = {duration_ms};
          const wrapEl = document.getElementById('wvc-timed-wrap');
          const primaryEl = document.getElementById('wvc-timed-primary');
          const transEl = document.getElementById('wvc-timed-trans');

          function renderAtMs(tMs) {{
            if (!wrapEl || !primaryEl || !transEl) return;
            let activeCue = null;
            for (let i = 0; i < cues.length; i++) {{
              const c = cues[i];
              const s = (Number(c.start) * 1000.0) + offsetMs;
              const e = (Number(c.end) * 1000.0) + offsetMs;
              if (tMs >= s && tMs <= e) {{
                activeCue = c;
                break;
              }}
            }}

            if (!activeCue) {{
              wrapEl.style.opacity = '0';
              return;
            }}

            wrapEl.style.opacity = '1';
            if (Array.isArray(activeCue.words) && activeCue.words.length > 0) {{
              primaryEl.innerHTML = '';
              for (let j = 0; j < activeCue.words.length; j++) {{
                const w = activeCue.words[j];
                const ws = (Number(w.start) * 1000.0) + offsetMs;
                const we = (Number(w.end) * 1000.0) + offsetMs;
                const span = document.createElement('span');
                span.className = 'wvc-word';
                if (tMs >= ws && tMs <= we) {{
                  span.className += ' active';
                }} else if (tMs > we) {{
                  span.className += ' spoken';
                }}
                span.textContent = w.word ?? w.text ?? '';
                primaryEl.appendChild(span);
              }}
            }} else {{
              primaryEl.textContent = activeCue.text || '';
            }}

            if (activeCue.translation) {{
              transEl.style.display = 'block';
              transEl.textContent = activeCue.translation;
            }} else {{
              transEl.style.display = 'none';
              transEl.textContent = '';
            }}
          }}

          window.__wvcOnFrame = function(progress, elapsedMs) {{
            const tMs = typeof elapsedMs === 'number' ? elapsedMs : (progress || 0) * durationMs;
            renderAtMs(tMs);
          }};

          // Show first valid state if previewed at t=0
          renderAtMs(0);
        }})();
        """

        object.__setattr__(self, "css", css)
        object.__setattr__(self, "html", html)
        object.__setattr__(self, "js", js)

    @classmethod
    def from_whisper(
        cls,
        whisper_data: Any,
        translation_map: Optional[Dict[int, str]] = None,
        offset: float = 0.0,
        duration: Optional[float] = None,
        **kwargs: Any,
    ) -> "TimedSubtitleScene":
        """
        Creates a TimedSubtitleScene directly from Whisper JSON output
        (either a dict with 'segments' or a list of segment dicts).
        """
        segments = (
            whisper_data.get("segments", [])
            if isinstance(whisper_data, dict)
            else list(whisper_data)
        )
        cues: List[Dict[str, Any]] = []
        max_end = 0.0
        t_map = translation_map or {}
        for idx, seg in enumerate(segments):
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start + 1.0))
            max_end = max(max_end, end)
            cue: Dict[str, Any] = {
                "start": start,
                "end": end,
                "text": str(seg.get("text", "")).strip(),
            }
            if idx in t_map:
                cue["translation"] = t_map[idx]
            elif seg.get("translation"):
                cue["translation"] = seg["translation"]
            if seg.get("words"):
                cue["words"] = [
                    {
                        "word": str(w.get("word", w.get("text", ""))),
                        "start": float(w.get("start", start)),
                        "end": float(w.get("end", end)),
                    }
                    for w in seg["words"]
                ]
            cues.append(cue)

        resolved_duration = duration if duration is not None else max(max_end + offset + 0.5, 1.0)
        return cls(cues=cues, offset=offset, duration=resolved_duration, **kwargs)

    @classmethod
    def from_srt(
        cls,
        srt_text: str,
        offset: float = 0.0,
        duration: Optional[float] = None,
        **kwargs: Any,
    ) -> "TimedSubtitleScene":
        """Parses standard SRT content into a TimedSubtitleScene."""

        def _parse_ts(ts: str) -> float:
            h, m, rest = ts.strip().replace(",", ".").split(":")
            return int(h) * 3600 + int(m) * 60 + float(rest)

        blocks = re.split(r"\r?\n\s*\r?\n", srt_text.strip())
        cues: List[Dict[str, Any]] = []
        max_end = 0.0
        for block in blocks:
            lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
            if len(lines) < 2:
                continue
            time_line_idx = 1 if "-->" in lines[1] else 0
            if "-->" not in lines[time_line_idx]:
                continue
            start_str, end_str = lines[time_line_idx].split("-->", 1)
            start = _parse_ts(start_str)
            end = _parse_ts(end_str)
            max_end = max(max_end, end)
            text_lines = lines[time_line_idx + 1 :]
            primary = text_lines[0] if text_lines else ""
            translation = " ".join(text_lines[1:]) if len(text_lines) > 1 else ""
            cue: Dict[str, Any] = {"start": start, "end": end, "text": primary}
            if translation:
                cue["translation"] = translation
            cues.append(cue)

        resolved_duration = duration if duration is not None else max(max_end + offset + 0.5, 1.0)
        return cls(cues=cues, offset=offset, duration=resolved_duration, **kwargs)


@dataclass
class CompositeScene(Scene):
    """
    Stacks multiple Scenes simultaneously in isolated full-viewport layers
    (e.g. CCTVScene + TimedSubtitleScene + custom watermark),
    synchronizing deterministic frame stepping across every layer in a single pass.
    """

    layers: List[Scene] = field(default_factory=list)
    duration: Optional[float] = None  # type: ignore[assignment]
    transparent: Optional[bool] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.duration is None:
            resolved_duration = max((layer.duration for layer in self.layers), default=5.0)
            object.__setattr__(self, "duration", resolved_duration)
        if self.transparent is None:
            resolved_transparent = (
                all(layer.transparent for layer in self.layers) if self.layers else True
            )
            object.__setattr__(self, "transparent", resolved_transparent)

    def to_html(self) -> str:
        import html as html_lib

        bg_style = "background: transparent !important;" if self.transparent else "background: #000;"
        iframe_tags = []
        for idx, layer in enumerate(self.layers):
            srcdoc = html_lib.escape(layer.to_html(), quote=True)
            iframe_tags.append(
                f'<iframe class="wvc-layer" id="wvc-layer-{idx}" '
                f'allowtransparency="true" srcdoc="{srcdoc}"></iframe>'
            )

        iframes_html = "\n".join(iframe_tags)
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{
  width: 100%;
  height: 100%;
  overflow: hidden;
  {bg_style}
}}
.wvc-stage {{
  position: relative;
  width: 100vw;
  height: 100vh;
}}
.wvc-layer {{
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: none;
  background: transparent;
  pointer-events: none;
}}
</style>
</head>
<body>
<div class="wvc-stage">
{iframes_html}
</div>
<script>
window.__wvcOnFrame = function(progress, elapsedMs, durationMs) {{
  const frames = document.querySelectorAll('iframe.wvc-layer');
  frames.forEach((frame) => {{
    try {{
      const win = frame.contentWindow;
      const doc = frame.contentDocument;
      if (!win || !doc) return;
      if (doc.documentElement) {{
        doc.documentElement.style.setProperty('--hf-progress', String(progress));
      }}
      if (doc.body) {{
        doc.body.style.setProperty('--hf-progress', String(progress));
      }}
      win.__hfProgress = progress;
      win.__wvcTimeMs = elapsedMs;
      win.__wvcDurationMs = durationMs;
      if (typeof win.__wvcOnFrame === 'function') {{
        win.__wvcOnFrame(progress, elapsedMs, durationMs);
      }}
      if (typeof doc.getAnimations === 'function') {{
        doc.getAnimations().forEach((anim) => {{
          anim.pause();
          anim.currentTime = elapsedMs;
        }});
      }}
    }} catch (e) {{}}
  }});
}};
</script>
</body>
</html>"""
