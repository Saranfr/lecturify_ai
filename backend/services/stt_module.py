"""
Lecturify AI - Speech-to-Text Module (Whisper)
Transcribes audio/video to text. Supports multilingual.
Extraction: 1) imageio-ffmpeg, 2) system ffmpeg, 3) moviepy, 4) PyAV.
"""
import os
import sys
import subprocess
from typing import Optional, Tuple

try:
    from backend.config import WHISPER_MODEL, WHISPER_LANGUAGE
except ImportError:
    from config import WHISPER_MODEL, WHISPER_LANGUAGE

# Whisper expects 16kHz mono PCM
TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1

# Cache ffmpeg path and ensure PATH is set at import
_FFMPEG_PATH: Optional[str] = None


def _get_ffmpeg_path() -> str:
    """Get ffmpeg path: imageio-ffmpeg (bundled) first, then 'ffmpeg' from PATH."""
    global _FFMPEG_PATH
    if _FFMPEG_PATH is not None:
        return _FFMPEG_PATH
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(exe)
        if ffmpeg_dir:
            path_env = os.environ.get("PATH", "")
            if ffmpeg_dir not in path_env:
                os.environ["PATH"] = ffmpeg_dir + os.pathsep + path_env
        _FFMPEG_PATH = exe
        return exe
    except Exception as e:
        print(f"[STT] imageio-ffmpeg not available: {e}. Install: pip install imageio-ffmpeg")
        _FFMPEG_PATH = "ffmpeg"
        return "ffmpeg"


def transcribe_audio(
    audio_path: str,
    model_name: Optional[str] = None,
    language: Optional[str] = None,
) -> str:
    """
    Transcribe audio file to text using Whisper.
    language=None enables auto-detect (multilingual).
    """
    try:
        import whisper
    except ImportError:
        return ""

    model_name = model_name or WHISPER_MODEL
    language = language or WHISPER_LANGUAGE

    if not os.path.isfile(audio_path):
        return ""

    try:
        model = whisper.load_model(model_name)
        result = model.transcribe(audio_path, language=language, fp16=False)
        return result.get("text", "").strip()
    except Exception as e:
        print(f"[STT] Whisper transcription failed: {e}")
        return ""


def _extract_audio_pyav(video_path: str, output_audio_path: str) -> Optional[str]:
    """Extract audio using PyAV (works without ffmpeg in PATH)."""
    try:
        import av
    except ImportError:
        return None

    try:
        with av.open(video_path) as container:
            if not container.streams.audio:
                return None
            out_container = av.open(output_audio_path, "w", format="wav")
            try:
                out_stream = out_container.add_stream("pcm_s16le", rate=TARGET_SAMPLE_RATE)
                out_stream.channels = TARGET_CHANNELS
                resampler = av.audio.resampler.AudioResampler(
                    format="s16", layout="mono", rate=TARGET_SAMPLE_RATE
                )
                for frame in container.decode(audio=0):
                    resampled = resampler.resample(frame)
                    if resampled:
                        try:
                            frames_out = list(resampled)
                        except (TypeError, ValueError):
                            frames_out = [resampled]
                        for r in frames_out:
                            r.pts = None
                            for packet in out_stream.encode(r):
                                out_container.mux(packet)
                for packet in out_stream.encode(None):
                    out_container.mux(packet)
            finally:
                out_container.close()
        return output_audio_path
    except Exception as e:
        print(f"[STT] PyAV extraction failed: {e}")
        return None


def _run_ffmpeg_extract(ffmpeg_exe: str, video_path: str, output_path: str) -> Tuple[bool, str]:
    """Run ffmpeg to extract audio. Returns (success, error_msg)."""
    cmd = [
        ffmpeg_exe, "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", str(TARGET_SAMPLE_RATE), "-ac", str(TARGET_CHANNELS),
        "-loglevel", "error",
        output_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=300, text=True, encoding="utf-8", errors="replace")
        err = (result.stderr or "").strip()[:500]
        # Accept returncode 0 or 1 (ffmpeg sometimes returns 1 for minor issues)
        ok = result.returncode in (0, 1) and os.path.isfile(output_path) and os.path.getsize(output_path) > 100
        return (ok, err if not ok else "")
    except subprocess.TimeoutExpired as e:
        return (False, "ffmpeg timed out")
    except FileNotFoundError:
        return (False, f"ffmpeg not found at {ffmpeg_exe}")
    except OSError as e:
        return (False, str(e))


def _extract_audio_moviepy(video_path: str, output_audio_path: str) -> Optional[str]:
    """Extract audio using moviepy (uses ffmpeg, may find it via imageio-ffmpeg)."""
    try:
        try:
            from moviepy import VideoFileClip
        except ImportError:
            from moviepy.editor import VideoFileClip
        with VideoFileClip(video_path) as clip:
            if clip.audio is None:
                return None
            clip.audio.write_audiofile(output_audio_path, fps=TARGET_SAMPLE_RATE, nbytes=2, verbose=False, logger=None)
        return output_audio_path if os.path.isfile(output_audio_path) and os.path.getsize(output_audio_path) > 100 else None
    except Exception as e:
        print(f"[STT] moviepy extraction failed: {e}")
        return None


def extract_audio_from_video(video_path: str, output_audio_path: str) -> Optional[str]:
    """Extract audio from video. Tries: 1) imageio-ffmpeg, 2) system ffmpeg, 3) moviepy, 4) PyAV."""
    ffmpeg_exe = _get_ffmpeg_path()
    ok, err = _run_ffmpeg_extract(ffmpeg_exe, video_path, output_audio_path)
    if ok:
        return output_audio_path

    if err:
        print(f"[STT] ffmpeg ({ffmpeg_exe}) failed: {err}")

    if ffmpeg_exe != "ffmpeg":
        ok, _ = _run_ffmpeg_extract("ffmpeg", video_path, output_audio_path)
        if ok:
            return output_audio_path

    if sys.platform == "win32":
        try:
            subprocess.run(
                f'ffmpeg -y -i "{video_path}" -vn -acodec pcm_s16le -ar {TARGET_SAMPLE_RATE} -ac {TARGET_CHANNELS} -loglevel error "{output_audio_path}"',
                shell=True, check=True, capture_output=True, timeout=300
            )
            if os.path.isfile(output_audio_path) and os.path.getsize(output_audio_path) > 100:
                return output_audio_path
        except Exception:
            pass

    result = _extract_audio_moviepy(video_path, output_audio_path)
    if result:
        return result
    return _extract_audio_pyav(video_path, output_audio_path)


def transcribe_video(video_path: str, temp_dir: str) -> str:
    """Transcribe video: extract audio -> Whisper. Falls back to Whisper on video directly."""
    os.makedirs(temp_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(video_path))[0]
    base = "".join(c for c in base if c.isalnum() or c in "-_")[:30] or "audio"
    audio_path = os.path.join(temp_dir, f"{base}_audio.wav")

    extracted = extract_audio_from_video(video_path, audio_path)
    if extracted:
        text = transcribe_audio(extracted)
        try:
            os.remove(extracted)
        except Exception:
            pass
        if text and len(text.strip()) > 3:
            return text

    # Last resort: pass video directly to Whisper (uses ffmpeg internally)
    text = transcribe_audio(video_path)
    return text or ""
