# 🎙️ MiMo TTS Toolkit

> 逆向并封装小米 MiMo v2.5 TTS API — 长文本分段、风格注入、WAV 合并

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🔍 发现了什么

小米 MiMo API 中有 3 个**未文档化的 TTS 模型**：

| 模型 | 说明 |
|------|------|
| `mimo-v2-tts` | 基础版 |
| `mimo-v2.5-tts` | 增强版（推荐） |
| `mimo-v2.5-tts-voiceclone` | 声音克隆 |
| `mimo-v2.5-tts-voicedesign` | 声音设计 |

**关键发现**：TTS 使用 Chat Completions API 格式，但有特殊约定——
- 待合成文本放在 `assistant` 角色消息中
- 风格/语气通过 `user` 角色消息注入
- 响应中 `audio.data` 返回 base64 编码的 WAV

## ⚡ 快速开始

### 安装

```bash
pip install -e .
```

### 命令行

```bash
# 设置 API Key
export MIMO_API_KEY="your-key"

# 基础用法
mimo-tts "今天天气真好" -o hello.wav

# 从文件合成（支持 Markdown）
mimo-tts -f article.md -o article.wav

# 雷军风格
mimo-tts "大家好" --style leijun -o leijun.wav

# 自定义风格
mimo-tts "重要内容" --style-prompt "用温柔的女声朗读" -o custom.wav

# 查看可用风格
mimo-tts --list-styles

# 查看可用模型
mimo-tts --models
```

### Python API

```python
from mimo_tts import MiMoTTS

tts = MiMoTTS(api_key="your-key")

# 短文本
wav = tts.synthesize("你好世界")
with open("hello.wav", "wb") as f:
    f.write(wav)

# 长文本（自动分段 + 合并）
wav = tts.synthesize_long(
    open("article.md").read(),
    style="leijun",
    max_chars=500,
    on_progress=lambda cur, tot, dur: print(f"[{cur}/{tot}] {dur/1000:.1f}s"),
)
with open("output.wav", "wb") as f:
    f.write(wav)
```

## 🎨 可用风格

| 风格 | 说明 |
|------|------|
| `neutral` | 默认，清晰自然 |
| `leijun` | 雷军演讲风格 |
| `news` | 新闻播报 |
| `story` | 讲故事 |
| `teach` | 教学讲解 |

## 🔧 技术细节

### API 逆向发现

```
POST https://token-plan-cn.xiaomimimo.com/v1/chat/completions

{
  "model": "mimo-v2.5-tts",
  "messages": [
    {"role": "user", "content": "风格提示词"},
    {"role": "assistant", "content": "待合成文本"}
  ]
}

Response:
{
  "choices": [{
    "message": {
      "audio": {"data": "<base64 WAV>"}
    }
  }]
}
```

### 长文本分段策略

MiMo TTS 单次输入建议 ≤500 字。本工具自动：
1. 按段落拆分
2. 段落过长则按句子拆分
3. 在自然断点处切分，保持语义完整
4. 段间插入静音（默认 500ms）
5. 合并为完整 WAV 文件

### WAV 拼接

纯标准库实现，无需 ffmpeg 或 pydub：
- 解析 WAV header（采样率、声道数、位深）
- 提取 PCM 数据
- 重新构建合并后的 WAV 文件

## 📋 需要什么

- Python 3.10+
- MiMo API Key（https://token-plan-cn.xiaomimimo.com）
- 可选：`httpx`（更快的 HTTP 请求）

## 📄 License

MIT
