import asyncio
from web_video_creator import HTMLToVideo, TextScene, ImageScene


async def main():
    converter = HTMLToVideo()

    scenes = [
        TextScene(
            text="网页视频生成",
            font_size="72px",
            color="#00d2ff",
            bg_color="#0a0a23",
            duration=3.0,
        ),
        TextScene(
            text="Powered by Playwright + FFmpeg",
            font_size="36px",
            color="#ffffff",
            bg_color="#0a0a23",
            duration=3.0,
            animation="slideIn",
        ),
    ]

    await converter.render_scenes(scenes, "output.mp4")
    print("Done! Check output.mp4")


if __name__ == "__main__":
    asyncio.run(main())
