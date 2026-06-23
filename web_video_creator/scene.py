from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Scene:
    html: str
    duration: float = 5.0
    css: str = ""
    js: str = ""

    def to_html(self) -> str:
        return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>{self.css}</style></head>
<body>{self.html}<script>{self.js}</script></body>
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
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: 1920px; height: 1080px;
  display: flex; align-items: center; justify-content: center;
  background: {self.bg_color};
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
  overflow: hidden;
}}
.text {{
  font-size: {self.font_size}; color: {self.color};
  text-align: center; padding: 60px;
  line-height: 1.6; max-width: 80%;
  animation: {self.animation} 1s ease-out;
}}
@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(30px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes slideIn {{ from {{ opacity: 0; transform: translateX(-60px); }} to {{ opacity: 1; transform: translateX(0); }} }}
@keyframes scaleIn {{ from {{ opacity: 0; transform: scale(0.8); }} to {{ opacity: 1; transform: scale(1); }} }}
"""
        html = f'<div class="text">{self.text}</div>'
        object.__setattr__(self, "css", css)
        object.__setattr__(self, "html", html)


@dataclass
class ImageScene(Scene):
    image_url: str = ""
    caption: str = ""

    def __post_init__(self):
        html = f'<img src="{self.image_url}" style="max-width:100%;max-height:80%;">'
        if self.caption:
            html += f'<p style="color:#fff;font-size:28px;margin-top:20px">{self.caption}</p>'
        css = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  width: 1920px; height: 1080px;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  background: #0f0f23; font-family: sans-serif;
}
"""
        object.__setattr__(self, "css", css)
        object.__setattr__(self, "html", html)
