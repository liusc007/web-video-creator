from web_video_creator.audio import AudioProcessor
from web_video_creator.scene import (
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


def test_text_scene_creates_html():
    scene = TextScene(text="你好，世界", font_size="64px", color="#ff0000")
    html = scene.to_html()
    assert "你好，世界" in html
    assert "64px" in html
    assert "#ff0000" in html
    assert "@keyframes fadeIn" in html
    assert "100vw" in html


def test_image_scene_creates_html():
    scene = ImageScene(image_url="https://example.com/img.png", caption="Test")
    html = scene.to_html()
    assert "https://example.com/img.png" in html
    assert "Test" in html


def test_text_scene_different_animation():
    scene = TextScene(text="Hello", animation="slideIn")
    html = scene.to_html()
    assert "slideIn" in html


def test_full_html_document_passthrough():
    raw_doc = "<!DOCTYPE html><html><head><title>X</title></head><body>Hi</body></html>"
    scene = Scene(html=raw_doc, transparent=True)
    rendered = scene.to_html()
    assert rendered.count("<!DOCTYPE html>") == 1
    assert "background:transparent !important" in rendered


def test_hud_scene_transparent_and_targets():
    targets = [
        {
            "x": 30,
            "y": 40,
            "w": 25,
            "h": 35,
            "label": "SUBJECT-01",
            "confidence": "99.4%",
            "metrics": {"STATUS": "LOCKED", "PULSE": "120"},
        }
    ]
    scene = HUDScene(
        title="CAM-02 EAST",
        location="HALLWAY A",
        targets=targets,
        color_theme="amber",
    )
    html = scene.to_html()
    assert scene.transparent is True
    assert "CAM-02 EAST" in html
    assert "HALLWAY A" in html
    assert "SUBJECT-01" in html
    assert "99.4%" in html
    assert "PULSE" in html
    assert "#f59e0b" in html
    assert "window.__wvcOnFrame" in html
    assert "fonts.googleapis.com" not in html


def test_cctv_and_cyber_hud_presets():
    cctv = CCTVScene()
    cctv_html = cctv.to_html()
    assert cctv.transparent is True
    assert "CAM-03" in cctv_html
    assert "REC ●" in cctv_html
    assert "#10b981" in cctv_html
    assert "hud-scanlines" in cctv_html

    cyber = CyberHUDScene()
    cyber_html = cyber.to_html()
    assert cyber.transparent is True
    assert "cyber-scanbeam" in cyber_html
    assert "cyber-radar" in cyber_html
    assert "#06b6d4" in cyber_html


def test_subtitle_scene_styles():
    scene = SubtitleScene(
        text="原始字幕对白",
        translation="English subtitle translation",
        position="bottom",
        style="cinema",
    )
    html = scene.to_html()
    assert scene.transparent is True
    assert "原始字幕对白" in html
    assert "English subtitle translation" in html
    assert "subtitle-wrap bottom cinema" in html


def test_timed_subtitle_from_whisper_and_srt():
    whisper_json = {
        "segments": [
            {
                "start": 0.2,
                "end": 1.6,
                "text": "第一句台词",
                "words": [
                    {"word": "第一句", "start": 0.2, "end": 0.8},
                    {"word": "台词", "start": 0.8, "end": 1.6},
                ],
            }
        ]
    }
    scene = TimedSubtitleScene.from_whisper(
        whisper_json, translation_map={0: "First line"}, offset=0.35
    )
    html = scene.to_html()
    assert scene.transparent is True
    assert "第一句台词" in html
    assert "First line" in html
    assert "350.0" in html
    assert scene.duration >= 2.4

    srt = "1\n00:00:00,500 --> 00:00:02,000\n第二句台词\nSecond line\n"
    srt_scene = TimedSubtitleScene.from_srt(srt, offset=0.25)
    srt_html = srt_scene.to_html()
    assert "第二句台词" in srt_html
    assert "Second line" in srt_html


def test_composite_scene_isolates_layers():
    cctv = CCTVScene(duration=4.0)
    sub = SubtitleScene(text="Layered", duration=5.5)
    comp = CompositeScene(layers=[cctv, sub])
    assert comp.duration == 5.5
    assert comp.transparent is True
    html = comp.to_html()
    assert 'id="wvc-layer-0"' in html
    assert 'id="wvc-layer-1"' in html
    assert "Layered" in html
    assert "CAM-03" in html


def test_audio_processor_presets():
    assert "aecho" in AudioProcessor.REVERB_PRESETS["hall"]
    assert "aecho" in AudioProcessor.REVERB_PRESETS["cathedral"]
    assert "aecho" in AudioProcessor.REVERB_PRESETS["corridor"]
    assert "highpass" in AudioProcessor.REVERB_PRESETS["cctv_speaker"]
    assert "highpass" in AudioProcessor.REVERB_PRESETS["radio"]
