"""
@file llm_service.py
@brief 大模型能力适配与本地兜底模块。

当前版本预留 OpenAI-compatible API 接入点；未配置 LLM_API_KEY 时，
使用本地规则生成摘要、关键词和文档结构树，确保课程验收环境可离线运行。

@author TextTreeDoc 项目组
@date 2026
"""

import os
import re
from collections import Counter


def llm_available() -> bool:
    """
    @brief 判断是否配置了大模型 API Key。

    @return 如果环境变量 LLM_API_KEY 存在则返回 True，否则返回 False。
    """
    return bool(os.getenv("LLM_API_KEY"))


def generate_summary(content: str, max_length: int = 160) -> str:
    """
    @brief 为文本生成摘要。

    @param content 正文内容。
    @param max_length 摘要最大长度。
    @return 摘要字符串。
    """
    cleaned = " ".join(content.split())
    return cleaned[:max_length]


def generate_keywords(title: str, content: str, limit: int = 6) -> list[str]:
    """
    @brief 使用本地词频规则提取关键词。

    @param title 文本标题。
    @param content 正文内容。
    @param limit 返回关键词数量上限。
    @return 关键词列表。
    """
    text = f"{title} {content}"
    tokens = re.findall(r"[\u4e00-\u9fa5]{2,}|[A-Za-z][A-Za-z0-9_-]{2,}", text)
    stop_words = {"一个", "可以", "进行", "系统", "文本", "文档", "使用", "生成", "the", "and"}
    counter = Counter(token for token in tokens if token.lower() not in stop_words)
    return [word for word, _ in counter.most_common(limit)]

