"""
@file prompt_service.py
@brief 文档生成与反馈改进 Prompt 构造服务。

该模块只负责拼接提示词，不直接调用大模型。
"""

import json
from typing import Any

from app.services.template_service import merge_with_default_config


def get_default_generation_prompt_template() -> str:
    """
    @brief 获取默认文档生成提示词模板。

    @return 提示词模板字符串。
    """
    return """你是课程报告和技术文档生成助手。
请根据用户主题、文本库资料和模板参数生成文档结构树。

用户主题：
{topic}

文本库资料：
{materials}

模板参数：
- 文本详细程度：{length}/100
- 专业程度：{professionalism}/100
- 语言正式程度：{formality}/100
- 结构清晰程度：{structure}/100
- 资料引用强度：{evidence}/100
- 表格使用程度：{tables}/100
- 创新扩展程度：{creativity}/100

额外改进要求：
{prompt_delta}

输出要求：
- 只输出严格 JSON，不要 Markdown，不要解释文字。
- JSON 必须包含 title 和 sections。
- sections 中每个章节包含 heading、content、children。
- 可以包含 blocks。
- blocks 支持 table 类型，table 必须包含 headers 和 rows。
"""


def build_generation_prompt(
    topic: str,
    materials: list[dict],
    config: dict[str, Any] | None,
    prompt_delta: str | None = None,
) -> str:
    """
    @brief 构造文档生成提示词。

    @param topic 用户主题。
    @param materials 文本资料列表。
    @param config 模板参数。
    @param prompt_delta 额外改进要求。
    @return 最终提示词。
    """
    merged_config = merge_with_default_config(config)
    materials_text = _format_materials(materials)
    return get_default_generation_prompt_template().format(
        topic=topic,
        materials=materials_text,
        length=merged_config["length"],
        professionalism=merged_config["professionalism"],
        formality=merged_config["formality"],
        structure=merged_config["structure"],
        evidence=merged_config["evidence"],
        tables=merged_config["tables"],
        creativity=merged_config["creativity"],
        prompt_delta=prompt_delta or "无",
    )


def get_feedback_options_prompt_template() -> str:
    """
    @brief 获取反馈改进选项提示词模板。

    @return 提示词模板字符串。
    """
    return """当前主题：
{topic}

当前文档结构树：
{tree_json}

用户反馈：
{feedback}

请生成 3-5 个可选择的改进选项。
每个选项要能转化为下一轮文档生成的 prompt_delta。
只输出严格 JSON，不要 Markdown。

格式：
{{
  "question": "...",
  "options": [
    {{
      "label": "...",
      "description": "...",
      "prompt_delta": "..."
    }}
  ]
}}
"""


def build_feedback_options_prompt(topic: str, tree: dict[str, Any], feedback: str) -> str:
    """
    @brief 构造反馈改进选项提示词。

    @param topic 当前主题。
    @param tree 当前结构树。
    @param feedback 用户反馈。
    @return 最终提示词。
    """
    return get_feedback_options_prompt_template().format(
        topic=topic,
        tree_json=json.dumps(tree, ensure_ascii=False, indent=2),
        feedback=feedback or "无",
    )


def _format_materials(materials: list[dict]) -> str:
    """
    @brief 将文本资料整理成提示词可读格式。

    @param materials 文本资料列表。
    @return 资料文本。
    """
    if not materials:
        return "暂无文本库资料。"
    lines = []
    for index, item in enumerate(materials, start=1):
        content = (item.get("content") or "").strip()
        lines.append(
            "\n".join(
                [
                    f"资料 {index}",
                    f"标题：{item.get('title', '')}",
                    f"摘要：{item.get('summary', '')}",
                    f"关键词：{item.get('keywords', '')}",
                    f"正文摘录：{content[:700]}",
                ]
            )
        )
    return "\n\n".join(lines)
