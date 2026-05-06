#!/usr/bin/env python3
"""MiMo TTS Toolkit — 命令行接口。

用法:
    mimo-tts "你好世界" -o hello.wav
    mimo-tts -f input.txt -o output.wav --style leijun
    mimo-tts --list-styles
    mimo-tts --models
"""

import argparse
import sys
import os


def main():
    parser = argparse.ArgumentParser(
        description="MiMo v2.5 TTS 语音合成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  mimo-tts "今天天气真好" -o weather.wav
  mimo-tts -f article.md -o article.wav --style leijun
  mimo-tts "Hello world" --style news --max-chars 300
  mimo-tts --list-styles
        """,
    )

    parser.add_argument("text", nargs="?", help="要合成的文本")
    parser.add_argument("-f", "--file", help="从文件读取文本（支持 .md/.txt）")
    parser.add_argument("-o", "--output", default="output.wav", help="输出文件路径 (默认: output.wav)")
    parser.add_argument("--style", default="neutral", help="语音风格 (默认: neutral)")
    parser.add_argument("--style-prompt", help="自定义风格提示词")
    parser.add_argument("--max-chars", type=int, default=500, help="每段最大字符数 (默认: 500)")
    parser.add_argument("--model", default="mimo-v2.5-tts", help="TTS 模型")
    parser.add_argument("--api-key", help="API Key (或设置 MIMO_API_KEY 环境变量)")
    parser.add_argument("--api-url", help="自定义 API 地址")
    parser.add_argument("--list-styles", action="store_true", help="列出所有可用风格")
    parser.add_argument("--models", action="store_true", help="列出所有可用 TTS 模型")
    parser.add_argument("--version", action="version", version="mimo-tts 0.1.0")

    args = parser.parse_args()

    # 列出风格
    if args.list_styles:
        from mimo_tts.styles import list_styles
        print("可用语音风格:\n")
        list_styles()
        return

    # 列出模型
    if args.models:
        from mimo_tts.client import MiMoTTS
        print("MiMo 可用 TTS 模型:\n")
        for m in MiMoTTS.AVAILABLE_MODELS:
            marker = " ← 默认" if m == "mimo-v2.5-tts" else ""
            print(f"  {m}{marker}")
        return

    # 获取文本
    text = args.text
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    elif not text:
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            parser.error("请提供文本：直接输入、-f 文件、或管道输入")

    if not text.strip():
        parser.error("文本内容为空")

    # 合成
    from mimo_tts.client import MiMoTTS

    tts = MiMoTTS(
        api_key=args.api_key,
        api_url=args.api_url,
        model=args.model,
    )

    print(f"文本: {len(text)} 字符")
    print(f"风格: {args.style}")
    print(f"模型: {args.model}")
    print()

    def progress(current, total, duration_ms):
        if duration_ms >= 0:
            print(f"  [{current}/{total}] ✓ {duration_ms/1000:.1f}s")
        else:
            print(f"  [{current}/{total}] ✗ 失败，跳过")

    try:
        wav_data = tts.synthesize_long(
            text,
            style=args.style,
            style_prompt=args.style_prompt,
            max_chars=args.max_chars,
            on_progress=progress,
        )

        with open(args.output, "wb") as f:
            f.write(wav_data)

        from mimo_tts.client import get_wav_duration_ms
        duration = get_wav_duration_ms(wav_data)
        size_mb = len(wav_data) / 1024 / 1024

        print(f"\n✅ 完成!")
        print(f"   文件: {args.output}")
        print(f"   时长: {duration/1000:.1f}s ({duration/1000/60:.1f}min)")
        print(f"   大小: {size_mb:.1f}MB")

    except Exception as e:
        print(f"\n❌ 失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
