"""MiMo TTS Toolkit — 逆向并封装小米 MiMo v2.5 TTS API."""

__version__ = "0.1.0"

from .client import MiMoTTS, concatenate_wav_files, get_wav_duration_ms
from .chunker import TextChunker
from .styles import STYLES

__all__ = ["MiMoTTS", "TextChunker", "concatenate_wav_files", "get_wav_duration_ms", "STYLES"]
