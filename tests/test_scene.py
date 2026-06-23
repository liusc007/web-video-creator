from web_video_creator.scene import TextScene, ImageScene


def test_text_scene_creates_html():
    scene = TextScene(text="你好，世界", font_size="64px", color="#ff0000")
    html = scene.to_html()
    assert "你好，世界" in html
    assert "64px" in html
    assert "#ff0000" in html
    assert "@keyframes fadeIn" in html


def test_image_scene_creates_html():
    scene = ImageScene(image_url="https://example.com/img.png", caption="Test")
    html = scene.to_html()
    assert "https://example.com/img.png" in html
    assert "Test" in html


def test_text_scene_different_animation():
    scene = TextScene(text="Hello", animation="slideIn")
    html = scene.to_html()
    assert "slideIn" in html
