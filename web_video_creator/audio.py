import subprocess
from typing import Dict, Optional


class AudioProcessor:
    """
    Spatial Audio & Acoustic Engine for AI Video Post-Production.
    Transforms flat, dry TTS dialogue into immersive, scene-grounded cinematic soundscapes.
    """

    REVERB_PRESETS: Dict[str, str] = {
        "hall": "aecho=0.8:0.88:60:0.4",
        "cathedral": "aecho=0.85:0.9:120|200:0.45|0.28",
        "room": "aecho=0.8:0.75:25:0.2",
        "corridor": "aecho=0.8:0.82:42|95:0.36|0.22",
        "cctv_speaker": "highpass=f=400,lowpass=f=3200,volume=1.15",
        "radio": "highpass=f=500,lowpass=f=2600,acompressor=threshold=-18dB:ratio=4,alimiter=limit=0.75,volume=1.15",
        "none": "anull",
    }

    @classmethod
    def apply_preset(
        cls,
        input_audio: str,
        output_audio: str,
        preset: str = "hall",
        extra_filter: Optional[str] = None,
        volume: float = 1.0,
        fade_in: float = 0.0,
        fade_out: float = 0.0,
        delay: float = 0.0,
        target_duration: Optional[float] = None,
    ) -> str:
        """
        Applies a spatial acoustic preset (e.g. hall, cathedral, room, corridor, cctv_speaker)
        to an audio file, with optional delay, volume scaling, fade-in/fade-out protection,
        and optional duration padding so muxing with -shortest never truncates padded video.
        """
        filter_str = cls.REVERB_PRESETS.get(preset, "anull")
        filters = []
        if filter_str != "anull":
            filters.append(filter_str)
        if volume != 1.0:
            filters.append(f"volume={volume}")
        if fade_in > 0:
            filters.append(f"afade=t=in:st=0:d={fade_in}")
        if fade_out > 0:
            filters.append(f"areverse,afade=t=in:st=0:d={fade_out},areverse")
        if extra_filter:
            filters.append(extra_filter)
        delay_ms = max(int(round(delay * 1000)), 0)
        if delay_ms > 0:
            filters.append(f"adelay={delay_ms}:all=1")
        if target_duration is not None and target_duration > 0:
            filters.append(f"apad,atrim=0:{target_duration:.6f}")

        af_arg = ",".join(filters) if filters else "anull"

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_audio),
            "-af",
            af_arg,
            "-c:a",
            "aac",
            str(output_audio),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return str(output_audio)

    @classmethod
    def mix_dialogue_and_ambience(
        cls,
        dialogue_path: str,
        ambience_path: str,
        output_path: str,
        dialogue_delay: float = 0.35,
        ambience_volume: float = 0.18,
        dialogue_preset: str = "hall",
        target_duration: Optional[float] = None,
    ) -> str:
        """
        Mixes a dry dialogue track with a looped background ambient room tone.
        Applies dialogue delay (to sync with smart video tpad breathing space) and scene reverb.
        When target_duration is set, pads silence after dialogue and trims the mix to match
        the full video duration so room tone continues smoothly through breathing tail frames.
        """
        dialogue_reverb = cls.REVERB_PRESETS.get(dialogue_preset, "anull")
        delay_ms = max(int(round(dialogue_delay * 1000)), 0)

        dia_chain = dialogue_reverb
        if delay_ms > 0:
            dia_chain = f"{dia_chain},adelay={delay_ms}:all=1"

        if target_duration is not None and target_duration > 0:
            filter_complex = (
                f"[0:a]{dia_chain},apad[dia];"
                f"[1:a]volume={ambience_volume}[amb];"
                f"[dia][amb]amix=inputs=2:duration=shortest:dropout_transition=2,"
                f"atrim=0:{target_duration:.6f}[out]"
            )
        else:
            filter_complex = (
                f"[0:a]{dia_chain}[dia];"
                f"[1:a]volume={ambience_volume}[amb];"
                f"[dia][amb]amix=inputs=2:duration=first:dropout_transition=2[out]"
            )

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(dialogue_path),
            "-stream_loop",
            "-1",
            "-i",
            str(ambience_path),
            "-filter_complex",
            filter_complex,
            "-map",
            "[out]",
            "-c:a",
            "aac",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return str(output_path)

    @staticmethod
    def generate_room_tone(
        output_path: str,
        duration: float = 5.0,
        amplitude: float = 0.012,
        tone: str = "indoor",
    ) -> str:
        """
        Synthesizes subtle natural room tone so voiceovers never sit over dead silence.
        tone options: 'indoor' (warm low room air), 'hall' (deep spacious air), 'cctv' (subtle mic hum).
        """
        shaping = {
            "indoor": "highpass=f=60,lowpass=f=450",
            "hall": "highpass=f=45,lowpass=f=320,aecho=0.8:0.85:50:0.3",
            "cctv": "highpass=f=220,lowpass=f=2400",
        }.get(tone, "highpass=f=60,lowpass=f=450")

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anoisesrc=color=pink:duration={duration}:amplitude={amplitude}",
            "-af",
            shaping,
            "-c:a",
            "aac",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return str(output_path)

    @staticmethod
    def generate_transition_click(
        output_path: str,
        style: str = "cctv_static",
        duration: float = 0.12,
    ) -> str:
        """
        Synthesizes a crisp cut transition sound effect (e.g. CCTV static burst or mechanical relay click).
        """
        if style == "mechanical":
            af = f"highpass=f=800,lowpass=f=4200,afade=t=out:st=0:d={duration},volume=0.5"
        else:
            af = f"highpass=f=1200,lowpass=f=6500,afade=t=in:st=0:d=0.01,afade=t=out:st=0.02:d={max(duration - 0.02, 0.02)},volume=0.35"

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anoisesrc=color=white:duration={duration}:amplitude=0.35",
            "-af",
            af,
            "-c:a",
            "aac",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return str(output_path)
