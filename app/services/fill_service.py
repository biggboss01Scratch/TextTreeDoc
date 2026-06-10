"""
@file fill_service.py
@brief 文档正文填充服务。

该模块将已经确认的结构树扩展为可直接生成 Word 的正文文档。
结构树负责标题、层级和图片/表格位置；填充阶段负责生成 paragraphs。
"""

from copy import deepcopy
from typing import Any


def fill_document_locally(topic: str, tree: dict[str, Any], related_texts: list[dict]) -> dict[str, Any]:
    """
    @brief 使用本地规则为结构树填充正文段落。

    @param topic 文档主题。
    @param tree 当前结构树。
    @param related_texts 文本库资料。
    @return 填充后的文档树。
    """
    filled = deepcopy(tree)
    filled.setdefault("title", topic)
    material_text = _material_summary(related_texts)
    for index, section in enumerate(filled.get("sections", []), 1):
        _fill_section(section, topic, material_text, level=1, order=str(index))
    return filled


def _fill_section(section: dict[str, Any], topic: str, material_text: str, level: int, order: str) -> None:
    heading = section.get("heading") or f"{order} 未命名章节"
    summary = section.get("content") or section.get("summary") or ""
    if not section.get("paragraphs"):
        section["paragraphs"] = _build_paragraphs(topic, heading, summary, material_text, level, section.get("blocks", []))
    for index, child in enumerate(section.get("children", []), 1):
        _fill_section(child, topic, material_text, level + 1, f"{order}.{index}")


def _build_paragraphs(
    topic: str,
    heading: str,
    summary: str,
    material_text: str,
    level: int,
    blocks: list[dict[str, Any]],
) -> list[str]:
    base = summary or f"本节围绕“{heading}”展开，服务于“{topic}”这一主题。"
    image_note = ""
    if any(block.get("type") == "image" for block in blocks or []):
        image_note = "本节已经配置了插图，正文需要围绕图示内容进行说明，使图片与章节论述形成对应关系。"
    if level == 1:
        return [
            f"{base} 在整体报告中，该部分承担承上启下的作用，需要明确问题背景、设计依据和分析范围。",
            f"从课题内容来看，{material_text} 因此，本节不仅整理相关事实，也进一步说明其对“{topic}”的支撑价值。{image_note}".strip(),
        ]
    return [
        f"{base} 该小节重点对相关内容进行细化说明，并提炼出支撑本报告论述的核心观点。{image_note}".strip()
    ]


def _material_summary(related_texts: list[dict]) -> str:
    if not related_texts:
        return "当前可参考信息较少，正文以课程报告常规逻辑进行补充"
    snippets = []
    for item in related_texts[:4]:
        snippets.append(item.get("summary") or item.get("content", "")[:120] or item.get("title", ""))
    return "；".join(snippet for snippet in snippets if snippet) or "已有内容能够为主题分析提供依据"
