"""文本分段器 — 智能拆分长文本为 TTS 可处理的片段。"""

import re
from typing import List


class TextChunker:
    """长文本智能分段器。

    MiMo TTS 单次输入有长度限制（建议 ≤500 字），
    此分段器在自然断点处拆分文本，保持语义完整。

    用法::

        chunker = TextChunker(max_chars=500)
        chunks = chunker.split(long_text)
    """

    def __init__(self, max_chars: int = 500):
        self.max_chars = max_chars

    def split(self, text: str) -> List[str]:
        """将文本拆分为多个片段。"""
        # 先清洗 Markdown 格式
        text = self._clean_markdown(text)

        # 按段落拆分
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        chunks = []
        current = ""

        for para in paragraphs:
            # 如果单段就超限，按句子进一步拆分
            if len(para) > self.max_chars:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(self._split_paragraph(para))
                continue

            # 尝试合并到当前段
            if current and len(current) + len(para) + 2 > self.max_chars:
                chunks.append(current)
                current = para
            else:
                current = f"{current}\n\n{para}" if current else para

        if current:
            chunks.append(current)

        return [c.strip() for c in chunks if c.strip()]

    def _split_paragraph(self, text: str) -> List[str]:
        """按句子拆分超长段落。"""
        # 中英文句子分隔符
        sentences = re.split(r'(?<=[。！？.!?])\s*', text)
        chunks = []
        current = ""

        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            if current and len(current) + len(sent) + 1 > self.max_chars:
                chunks.append(current)
                current = sent
            else:
                current = f"{current} {sent}" if current else sent

        if current:
            chunks.append(current)

        return chunks

    def _clean_markdown(self, text: str) -> str:
        """清洗 Markdown 格式，使其适合语音合成。"""
        # 移除标题标记
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # 移除粗体/斜体标记
        text = text.replace('**', '').replace('*', '').replace('__', '')
        # 移除代码块
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # 移除图片链接
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        # Wiki 链接转纯文本
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        # 移除特殊标记
        text = re.sub(r'\*\*【[^】]*】\*\*', '', text)
        text = re.sub(r'【[^】]*】', '', text)
        # 移除水平线
        text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
        # 移除引用标记
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
        # 清理多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
