import subprocess
import tempfile
from pathlib import Path

class HTMLToVideo:
    def __init__(self, width=1920, height=1080, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
    
    def render(self, html_path, output_path, duration=10):
        frames_dir = tempfile.mkdtemp()
        self._capture_frames(html_path, frames_dir, duration)
        self._encode_video(frames_dir, output_path)
        return output_path
    
    def _capture_frames(self, html_path, frames_dir, duration):
        total_frames = duration * self.fps
        print(f"Capturing {total_frames} frames from {html_path}...")
    
    def _encode_video(self, frames_dir, output_path):
        print(f"Encoding video to {output_path}...")
    
    def add_audio(self, video_path, audio_path, output_path):
        cmd = [
            'ffmpeg', '-i', video_path, '-i', audio_path,
            '-c:v', 'copy', '-c:a', 'aac',
            '-map', '0:v:0', '-map', '1:a:0',
            '-shortest', output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

if __name__ == '__main__':
    converter = HTMLToVideo()
    converter.render('index.html', 'output.mp4', duration=15)
