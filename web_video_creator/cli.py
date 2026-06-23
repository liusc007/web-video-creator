import asyncio
import argparse

from .converter import HTMLToVideo
from .scene import TextScene, ImageScene


def main():
    parser = argparse.ArgumentParser(description="HTML to video converter")
    parser.add_argument("input", nargs="?", help="HTML file to convert")
    parser.add_argument("-o", "--output", default="output.mp4", help="Output video path")
    parser.add_argument("-d", "--duration", type=float, default=5.0, help="Duration per scene (seconds)")
    parser.add_argument("--text", help="Create a text scene with this text")
    parser.add_argument("--image", help="Create an image scene with this URL")
    args = parser.parse_args()

    converter = HTMLToVideo()

    if args.text:
        scenes = [TextScene(text=args.text, duration=args.duration)]
    elif args.image:
        scenes = [ImageScene(image_url=args.image, duration=args.duration)]
    else:
        print("Specify --text, --image, or provide an HTML file")
        return

    asyncio.run(converter.render_scenes(scenes, args.output))
    print(f"Video saved to {args.output}")


if __name__ == "__main__":
    main()
