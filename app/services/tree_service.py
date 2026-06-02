"""
@file tree_service.py
@brief 文档结构树生成模块。

该模块根据用户主题和文本库检索结果构建 Python dict 文档树，
并保证输出可直接序列化为 JSON。

@author TextTreeDoc 项目组
@date 2026
"""


def generate_tree(topic: str, related_texts: list[dict]) -> dict:
    """
    @brief 根据主题和相关文本生成文档结构树。

    @param topic 用户输入的文档主题。
    @param related_texts 从文本库检索得到的资料列表。
    @return 文档结构树，包含 title 和 sections 字段。
    """
    snippets = _build_snippets(related_texts)
    return {
        "title": topic,
        "sections": [
            {
                "heading": "1. 项目背景",
                "content": f"{topic} 的文档创建需要围绕主题资料进行整理。{snippets[0]}",
                "children": [],
            },
            {
                "heading": "2. 相关资料分析",
                "content": "系统从文本库中检索到以下相关资料，可作为报告内容来源。",
                "children": [
                    {
                        "heading": f"2.{index + 1} {item.get('title', '资料')}",
                        "content": item.get("summary") or item.get("content", "")[:160],
                        "children": [],
                    }
                    for index, item in enumerate(related_texts[:3])
                ],
            },
            {
                "heading": "3. 核心内容整理",
                "content": snippets[1],
                "children": [],
                "blocks": [
                    {
                        "type": "table",
                        "headers": ["资料标题", "关键词", "来源"],
                        "rows": [
                            [
                                item.get("title", ""),
                                item.get("keywords", ""),
                                item.get("source_type", "") or "manual",
                            ]
                            for item in related_texts[:5]
                        ],
                    }
                ],
            },
            {
                "heading": "4. 应用与实现",
                "content": "该结构树可以被前端展示，也可以交给后端 docx 模块生成 Word 文档。",
                "children": [],
            },
            {
                "heading": "5. 总结",
                "content": f"围绕“{topic}”，系统完成了资料检索、结构化组织和自动文档生成的核心流程。",
                "children": [],
            },
        ],
    }


def _build_snippets(related_texts: list[dict]) -> list[str]:
    """
    @brief 从相关文本中整理可写入章节的内容片段。

    @param related_texts 相关文本资料列表。
    @return 两个内容片段组成的列表。
    """
    if not related_texts:
        return ["当前文本库资料较少，可先添加资料后再生成更丰富的报告。", "暂无更多资料。"]
    summaries = [item.get("summary") or item.get("content", "")[:160] for item in related_texts]
    first = summaries[0] if summaries else ""
    combined = "；".join(summary for summary in summaries[:3] if summary)
    return [first, combined or first]

