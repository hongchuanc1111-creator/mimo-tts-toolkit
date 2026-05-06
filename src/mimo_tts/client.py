"""MiMo TTS API client — 逆向小米 MiMo v2.5 TTS 接口."""

import json
import base64
import os
import time
import struct
from typing import Optional

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False
    import urllib.request


class MiMoTTS:
    """小米 MiMo TTS 客户端。

    MiMo TTS 使用 Chat Completions API 格式，但有特殊约定：
    - 待合成文本放在 assistant 角色的消息中
    - 风格/语气通过 user 角色消息注入
    - 响应中 audio.data 返回 base64 编码的 WAV 音频

    用法::

        tts = MiMoTTS(api_key="your-key")
        wav_bytes = tts.synthesize("你好世界")
        with open("output.wav", "wb") as f:
            f.write(wav_bytes)
    """

    API_URL = "https://token-plan-cn.xiaomimimo.com/v1/chat/completions"
    MODEL = "mimo-v2.5-tts"

    # 可用模型（逆向发现）
    AVAILABLE_MODELS = [
        "mimo-v2-tts",
        "mimo-v2.5-tts",
        "mimo-v2.5-tts-voiceclone",
        "mimo-v2.5-tts-voicedesign",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: str = "mimo-v2.5-tts",
        timeout: int = 120,
        max_retries: int = 3,
    ):
        self.api_key = api_key or os.environ.get("MIMO_API_KEY", "")
        self.api_url = api_url or self.API_URL
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        if not self.api_key:
            raise ValueError(
                "需要提供 api_key 或设置 MIMO_API_KEY 环境变量。\n"
                "获取方式: https://token-plan-cn.xiaomimimo.com"
            )

    def synthesize(
        self,
        text: str,
        style: str = "neutral",
        style_prompt: Optional[str] = None,
    ) -> bytes:
        """合成单段文本为 WAV 音频。

        Args:
            text: 要合成的文本
            style: 预设风格名称（见 styles.py），或 "custom"
            style_prompt: 自定义风格提示词（style="custom" 时使用）

        Returns:
            WAV 音频数据（bytes）
        """
        from .styles import STYLES

        if style_prompt:
            system_msg = style_prompt
        elif style in STYLES:
            system_msg = STYLES[style]
        else:
            system_msg = STYLES.get("neutral", "")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": system_msg},
                {"role": "assistant", "content": text},
            ],
        }

        for attempt in range(self.max_retries):
            try:
                resp_data = self._request(payload)
                msg = resp_data["choices"][0]["message"]
                if "audio" in msg and msg["audio"]:
                    return base64.b64decode(msg["audio"]["data"])
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise RuntimeError(f"TTS 合成失败（{self.max_retries} 次重试后）: {e}")

        raise RuntimeError("TTS 合成失败: 未返回音频数据")

    def synthesize_long(
        self,
        text: str,
        style: str = "neutral",
        style_prompt: Optional[str] = None,
        max_chars: int = 500,
        pause_ms: int = 500,
        on_progress=None,
    ) -> bytes:
        """合成长文本（自动分段 + 合并）。

        MiMo TTS 单次输入有长度限制，此方法自动将长文本
        拆分为多段分别合成，然后拼接为完整 WAV 文件。

        Args:
            text: 长文本（可以是 Markdown）
            style: 预设风格名称
            style_prompt: 自定义风格提示词
            max_chars: 每段最大字符数（建议 300-500）
            pause_ms: 段间停顿（毫秒），默认 500ms
            on_progress: 进度回调 fn(current, total, duration_ms)

        Returns:
            合并后的 WAV 音频数据（bytes）
        """
        from .chunker import TextChunker

        chunker = TextChunker(max_chars=max_chars)
        chunks = chunker.split(text)
        wav_list = []

        for i, chunk in enumerate(chunks):
            try:
                wav = self.synthesize(chunk, style=style, style_prompt=style_prompt)
                duration = get_wav_duration_ms(wav)
                wav_list.append(wav)
                if on_progress:
                    on_progress(i + 1, len(chunks), duration)
            except Exception as e:
                # 跳过失败的段，记录但继续
                if on_progress:
                    on_progress(i + 1, len(chunks), -1)
                continue

            # 段间停顿
            if i < len(chunks) - 1 and pause_ms > 0:
                wav_list.append(generate_silence_wav(
                    duration_ms=pause_ms,
                    sample_rate=get_wav_sample_rate(wav) if wav else 24000,
                ))

        if not wav_list:
            raise RuntimeError("所有段落合成失败")

        return concatenate_wav_files(wav_list)

    def _request(self, payload: dict) -> dict:
        """发送 API 请求。"""
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if _HAS_HTTPX:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self.api_url, content=data, headers=headers)
                resp.raise_for_status()
                return resp.json()
        else:
            req = urllib.request.Request(self.api_url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))


# ── WAV 工具函数 ──────────────────────────────────────────────

def get_wav_duration_ms(wav_data: bytes) -> int:
    """获取 WAV 音频时长（毫秒）。"""
    if len(wav_data) < 44:
        return 0
    try:
        byte_rate = struct.unpack("<I", wav_data[28:32])[0]
        data_size = struct.unpack("<I", wav_data[40:44])[0]
        return int(data_size / byte_rate * 1000) if byte_rate > 0 else 0
    except Exception:
        return 0


def get_wav_sample_rate(wav_data: bytes) -> int:
    """获取 WAV 采样率。"""
    if len(wav_data) < 28:
        return 24000
    try:
        return struct.unpack("<I", wav_data[24:28])[0]
    except Exception:
        return 24000


def generate_silence_wav(duration_ms: int = 500, sample_rate: int = 24000) -> bytes:
    """生成静音 WAV 片段。"""
    num_samples = int(sample_rate * duration_ms / 1000)
    data_size = num_samples * 2  # 16-bit mono
    file_size = 36 + data_size

    header = struct.pack("<4sI4s", b"RIFF", file_size, b"WAVE")
    fmt = struct.pack("<4sIHHIIHH", b"fmt ", 16, 1, 1, sample_rate,
                      sample_rate * 2, 2, 16)
    data_header = struct.pack("<4sI", b"data", data_size)
    silence = b"\x00" * data_size

    return header + fmt + data_header + silence


def concatenate_wav_files(wav_list: list[bytes]) -> bytes:
    """合并多个 WAV 文件。"""
    if not wav_list:
        return b""

    first = wav_list[0]
    if len(first) < 44:
        return b""

    sr = struct.unpack("<I", first[24:28])[0]
    nc = struct.unpack("<H", first[22:24])[0]
    bps = struct.unpack("<H", first[34:36])[0]
    bps_bytes = bps // 8

    all_data = b""
    for wav in wav_list:
        if len(wav) > 44:
            all_data += wav[44:]

    data_size = len(all_data)
    file_size = 36 + data_size

    header = struct.pack("<4sI4s", b"RIFF", file_size, b"WAVE")
    fmt = struct.pack("<4sIHHIIHH", b"fmt ", 16, 1, nc, sr,
                      sr * nc * bps_bytes, nc * bps_bytes, bps)
    dh = struct.pack("<4sI", b"data", data_size)

    return header + fmt + dh + all_data
