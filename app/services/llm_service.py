"""
@file llm_service.py
@brief 大模型能力适配与本地兜底模块。

当前版本预留 OpenAI-compatible API 接入点；未配置 LLM_API_KEY 时，
使用本地规则生成摘要、关键词和文档结构树，确保课程验收环境可离线运行。

@author TextTreeDoc 项目组
@date 2026
"""

import re
import json
import os
import time
import urllib.error
import urllib.request
from collections import Counter
from typing import Any


def llm_available() -> bool:
    """
    @brief 判断是否配置了大模型 API Key。

    @return 如果环境变量 LLM_API_KEY 存在则返回 True，否则返回 False。
    """
    return bool(_api_key())


def generate_summary(content: str, max_length: int = 160) -> str:
    """
    @brief 为文本生成摘要。

    @param content 正文内容。
    @param max_length 摘要最大长度。
    @return 摘要字符串。
    """
    cleaned = " ".join(content.split())
    if llm_available():
        prompt = f"请为下面文本生成一段不超过 {max_length} 字的中文摘要，只返回摘要正文：\n\n{cleaned[:4000]}"
        result = _chat_completion(prompt, system="你是一个严谨的中文文档摘要助手。")
        if result:
            return result[:max_length]
    return cleaned[:max_length]


def generate_keywords(title: str, content: str, limit: int = 6) -> list[str]:
    """
    @brief 使用本地词频规则提取关键词。

    @param title 文本标题。
    @param content 正文内容。
    @param limit 返回关键词数量上限。
    @return 关键词列表。
    """
    if llm_available():
        prompt = (
            f"请从下面资料中提取 {limit} 个中文关键词。"
            "只返回 JSON 数组，例如：[\"开源\", \"许可证\"]。\n\n"
            f"标题：{title}\n正文：{content[:4000]}"
        )
        result = _chat_completion(prompt, system="你是一个关键词提取助手，必须输出 JSON 数组。")
        keywords = _parse_json_array(result)
        if keywords:
            return [str(item) for item in keywords[:limit]]

    text = f"{title} {content}"
    tokens = re.findall(r"[\u4e00-\u9fa5]{2,}|[A-Za-z][A-Za-z0-9_-]{2,}", text)
    stop_words = {"一个", "可以", "进行", "系统", "文本", "文档", "使用", "生成", "the", "and"}
    counter = Counter(token for token in tokens if token.lower() not in stop_words)
    return [word for word, _ in counter.most_common(limit)]


def generate_tree_with_llm(topic: str, related_texts: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    @brief 调用 DeepSeek / OpenAI-compatible API 生成文档结构树。

    @param topic 用户输入的文档主题。
    @param related_texts 从文本库检索出的相关资料。
    @return 结构树字典；调用失败或解析失败时返回 None。
    """
    if not llm_available():
        return None
    compact_texts = [
        {
            "title": item.get("title", ""),
            "summary": item.get("summary", ""),
            "keywords": item.get("keywords", ""),
            "content": (item.get("content", "") or "")[:700],
        }
        for item in related_texts[:5]
    ]
    prompt = f"""
请根据主题和资料生成一个中文课程报告文档结构树。

要求：
1. 只返回 JSON，不要 Markdown 代码块。
2. JSON 顶层必须包含 title 和 sections。
3. sections 中每个节点包含 heading、content、children。
4. 可以在合适章节加入 blocks，其中 table block 使用 type、headers、rows 字段。
5. 内容要基于给定资料，不要编造具体来源。

主题：{topic}

资料：
{json.dumps(compact_texts, ensure_ascii=False)}
"""
    result = _chat_completion(prompt, system="你是一个文档结构树生成助手，必须输出合法 JSON。")
    parsed = _parse_json_object(result)
    if parsed and isinstance(parsed.get("sections"), list):
        parsed.setdefault("title", topic)
        return parsed
    return None


def call_llm(prompt: str) -> str | None:
    """
    @brief 调用 OpenAI-compatible 大模型接口。

    @param prompt 用户提示词。
    @return 模型返回文本；未配置 API Key 或调用失败时返回 None。
    """
    if not llm_available():
        return None
    result = _chat_completion(prompt, system="你是一个严谨的中文文档生成助手，必须遵循用户输出格式要求。")
    return result or None


def call_llm_with_status(prompt: str) -> tuple[str | None, dict[str, Any]]:
    """
    @brief 调用大模型并返回调用状态。

    @param prompt 用户提示词。
    @return 模型文本和状态信息。
    """
    if not llm_available():
        return None, {
            "provider": "local",
            "used_llm": False,
            "fallback": True,
            "fallback_reason": "未配置 DeepSeek API Key",
        }
    result, error = _chat_completion_with_error(
        prompt,
        system="你是一个严谨的中文文档生成助手，必须遵循用户输出格式要求。",
    )
    if result:
        return result, {
            "provider": "deepseek",
            "model": _model(),
            "used_llm": True,
            "fallback": False,
            "fallback_reason": "",
        }
    return None, {
        "provider": "local",
        "model": _model(),
        "used_llm": False,
        "fallback": True,
        "fallback_reason": error or "DeepSeek 未返回有效内容",
    }


def _api_key() -> str:
    """
    @brief 读取大模型 API Key。

    @return API Key 字符串。
    """
    return os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY") or ""


def _api_base_url() -> str:
    """
    @brief 读取 OpenAI-compatible API 基础地址。

    @return API 基础地址。
    """
    return (os.getenv("LLM_API_BASE") or os.getenv("LLM_BASE_URL") or "https://api.deepseek.com").rstrip("/")


def _model() -> str:
    """
    @brief 读取模型名称。

    @return 模型名称。
    """
    return os.getenv("LLM_MODEL") or "deepseek-chat"


def _request_timeout() -> int:
    """
    @brief 读取大模型请求超时时间。

    @return 超时时间，单位秒。
    """
    return _read_positive_int_env("LLM_TIMEOUT_SECONDS", 90)


def _retry_count() -> int:
    """
    @brief 读取大模型网络失败重试次数。

    @return 重试次数。
    """
    return _read_positive_int_env("LLM_RETRY_COUNT", 1)


def _read_positive_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return parsed if parsed >= 0 else default


def _chat_completion(prompt: str, system: str) -> str:
    """
    @brief 调用 OpenAI-compatible Chat Completions 接口。

    @param prompt 用户提示词。
    @param system 系统提示词。
    @return 模型返回文本；失败时返回空字符串。
    """
    result, _error = _chat_completion_with_error(prompt, system)
    return result


def _chat_completion_with_error(prompt: str, system: str) -> tuple[str, str]:
    """
    @brief 调用 OpenAI-compatible Chat Completions 接口并保留错误原因。

    @param prompt 用户提示词。
    @param system 系统提示词。
    @return 模型返回文本和错误原因。成功时错误原因为空。
    """
    payload = {
        "model": _model(),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "temperature": 0.3,
    }
    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    last_error = ""
    for attempt in range(_retry_count() + 1):
        request = urllib.request.Request(
            f"{_api_base_url()}/chat/completions",
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {_api_key()}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=_request_timeout()) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")[:200]
            return "", f"DeepSeek HTTP {exc.code}: {detail or exc.reason}"
        except urllib.error.URLError as exc:
            last_error = f"DeepSeek 网络请求失败: {exc.reason}"
        except TimeoutError:
            last_error = f"DeepSeek 请求超时（超过 {_request_timeout()} 秒）"
        except json.JSONDecodeError:
            return "", "DeepSeek 响应不是有效 JSON"
        if attempt < _retry_count():
            time.sleep(1.2)
    else:
        return "", last_error or "DeepSeek 请求失败"
    choices = data.get("choices") or []
    if not choices:
        return "", "DeepSeek 响应缺少 choices"
    message = choices[0].get("message") or {}
    content = str(message.get("content") or "").strip()
    if not content:
        return "", "DeepSeek 返回内容为空"
    return content, ""


def _parse_json_object(value: str) -> dict[str, Any] | None:
    """
    @brief 从模型输出中解析 JSON 对象。

    @param value 模型输出文本。
    @return JSON 对象；失败时返回 None。
    """
    if not value:
        return None
    cleaned = _strip_code_fence(value)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


def _parse_json_array(value: str) -> list[Any]:
    """
    @brief 从模型输出中解析 JSON 数组。

    @param value 模型输出文本。
    @return JSON 数组；失败时返回空列表。
    """
    if not value:
        return []
    cleaned = _strip_code_fence(value)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", cleaned, flags=re.S)
        if not match:
            return []
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []
    return parsed if isinstance(parsed, list) else []


def _strip_code_fence(value: str) -> str:
    """
    @brief 去除模型可能返回的 Markdown 代码块包裹。

    @param value 模型输出文本。
    @return 清理后的文本。
    """
    return re.sub(r"^```(?:json)?|```$", "", value.strip(), flags=re.I).strip()
