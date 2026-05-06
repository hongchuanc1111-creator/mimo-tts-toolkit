#!/usr/bin/env python3
"""示例：用 MiMo TTS 合成一段语音。

运行前设置环境变量:
    export MIMO_API_KEY="your-key"

运行:
    python examples/basic_usage.py
"""

from mimo_tts import MiMoTTS

def main():
    # 初始化客户端
    tts = MiMoTTS()  # 从环境变量读取 API_KEY

    # 短文本合成
    print("=== 短文本合成 ===")
    wav = tts.synthesize("大家好，我是小米的雷军。今天给大家介绍一个非常好的产品。")
    with open("demo_short.wav", "wb") as f:
        f.write(wav)
    print(f"✅ 已保存 demo_short.wav ({len(wav)/1024:.0f}KB)")

    # 长文本合成（自动分段）
    print("\n=== 长文本合成 ===")
    long_text = """
    人工智能正在改变我们的生活方式。从智能手机上的语音助手，
    到自动驾驶汽车，再到医疗诊断，AI 技术已经深入到各个领域。

    小米作为一家科技公司，一直在 AI 领域持续投入。
    MiMo 大语言模型就是我们最新的成果之一。
    它不仅能够理解和生成文本，还支持语音合成等多模态能力。

    未来，我们将继续探索 AI 的更多可能性，
    让技术更好地服务于每一位用户。
    """

    wav = tts.synthesize_long(
        long_text,
        style="leijun",
        max_chars=500,
        on_progress=lambda cur, tot, dur: print(f"  [{cur}/{tot}] {dur/1000:.1f}s"),
    )
    with open("demo_long.wav", "wb") as f:
        f.write(wav)
    print(f"✅ 已保存 demo_long.wav ({len(wav)/1024/1024:.1f}MB)")


if __name__ == "__main__":
    main()
