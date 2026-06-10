"""
@file template_service.py
@brief 模板参数配置业务逻辑模块。

模板配置以 JSON 字符串保存到 SQLite，返回给接口时解析为 dict。
"""

import json
import re
from datetime import datetime
from typing import Any

from app.core.database import get_connection
from app.models.schemas import TemplateConfigCreate, TemplateConfigUpdate
from app.services.llm_service import call_llm


DEFAULT_TEMPLATE_CONFIG: dict[str, int] = {
    "length": 70,
    "professionalism": 80,
    "formality": 75,
    "structure": 85,
    "evidence": 70,
    "tables": 50,
    "creativity": 40,
}


DEFAULT_DOCUMENT_FORMAT: dict[str, Any] = {
    "template_type": "课程报告",
    "style_name": "规范课程报告",
    "heading_numbering": "decimal",
    "cover": False,
    "cover_style": "none",
    "show_title": True,
    "toc": False,
    "abstract": False,
    "references": False,
    "body_font": "宋体",
    "heading_font": "黑体",
    "ascii_font": "Times New Roman",
    "body_size": 12,
    "heading1_size": 16,
    "heading2_size": 14,
    "heading3_size": 12,
    "line_spacing": 1.5,
    "line_spacing_rule": {"type": "multiple", "value": 1.5, "unit": "line"},
    "first_line_indent_chars": 2,
    "paragraph_space_after": 6,
    "body_space_before": {"value": 0, "unit": "pt"},
    "body_space_after": {"value": 6, "unit": "pt"},
    "heading1_space_before": {"value": 18, "unit": "pt"},
    "heading1_space_after": {"value": 12, "unit": "pt"},
    "heading2_space_before": {"value": 12, "unit": "pt"},
    "heading2_space_after": {"value": 6, "unit": "pt"},
    "heading3_space_before": {"value": 6, "unit": "pt"},
    "heading3_space_after": {"value": 6, "unit": "pt"},
    "table_style": "Table Grid",
    "table_title_font": "黑体",
    "table_title_size": 12,
    "table_body_font": "宋体",
    "table_body_size": 10.5,
    "figure_title_font": "宋体",
    "figure_title_size": 12,
}

CHINESE_FONT_SIZE_TO_PT = {
    "初号": 42,
    "小初": 36,
    "一号": 26,
    "小一": 24,
    "二号": 22,
    "小二": 18,
    "三号": 16,
    "小三": 15,
    "四号": 14,
    "小四": 12,
    "五号": 10.5,
    "小五": 9,
    "六号": 7.5,
    "小六": 6.5,
    "七号": 5.5,
    "八号": 5,
}

DOCUMENT_TEMPLATE_PRESETS: dict[str, dict[str, Any]] = {
    "实验报告": {
        "template_type": "实验报告",
        "style_name": "实验报告模板",
        "heading_numbering": "decimal",
        "cover": False,
        "cover_style": "none",
        "show_title": True,
        "toc": False,
        "abstract": False,
        "references": False,
        "line_spacing": 1.5,
        "first_line_indent_chars": 2,
        "table_style": "Table Grid",
    },
    "结课论文": {
        "template_type": "结课论文",
        "style_name": "结课论文模板",
        "heading_numbering": "chinese",
        "cover": False,
        "cover_style": "none",
        "show_title": True,
        "toc": True,
        "abstract": True,
        "references": True,
        "line_spacing": 1.5,
        "first_line_indent_chars": 2,
        "table_style": "Table Grid",
    },
    "技术分析报告": {
        "template_type": "技术分析报告",
        "style_name": "技术分析报告模板",
        "heading_numbering": "decimal",
        "cover": False,
        "cover_style": "none",
        "show_title": True,
        "toc": True,
        "abstract": False,
        "references": True,
        "line_spacing": 1.35,
        "first_line_indent_chars": 2,
        "table_style": "Light Shading Accent 1",
    },
    "项目设计文档": {
        "template_type": "项目设计文档",
        "style_name": "项目设计文档模板",
        "heading_numbering": "decimal",
        "cover": False,
        "cover_style": "none",
        "show_title": True,
        "toc": True,
        "abstract": False,
        "references": False,
        "line_spacing": 1.35,
        "first_line_indent_chars": 0,
        "table_style": "Table Grid",
    },
}


def list_template_configs() -> list[dict]:
    """
    @brief 查询所有模板配置。

    @return 模板配置列表。
    """
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM template_configs ORDER BY is_default DESC, id").fetchall()
    return [_row_to_template(row) for row in rows]


def get_default_template_config() -> dict:
    """
    @brief 获取默认模板配置。

    @return 默认模板配置。
    """
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM template_configs WHERE is_default = 1 ORDER BY id LIMIT 1"
        ).fetchone()
        if row is None:
            row = connection.execute("SELECT * FROM template_configs ORDER BY id LIMIT 1").fetchone()
        if row is None:
            cursor = connection.execute(
                """
                INSERT INTO template_configs (name, config_json, is_default, created_at)
                VALUES (?, ?, 1, ?)
                """,
                (
                    "默认模板配置",
                    json.dumps(DEFAULT_TEMPLATE_CONFIG, ensure_ascii=False),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            connection.commit()
            row = connection.execute("SELECT * FROM template_configs WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _row_to_template(row)


def create_template_config(payload: TemplateConfigCreate) -> dict:
    """
    @brief 创建模板配置。

    @param payload 创建请求。
    @return 创建后的模板配置。
    """
    with get_connection() as connection:
        if payload.is_default:
            connection.execute("UPDATE template_configs SET is_default = 0")
        cursor = connection.execute(
            """
            INSERT INTO template_configs (name, config_json, is_default, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                payload.name,
                json.dumps(_normalize_config(payload.config), ensure_ascii=False),
                1 if payload.is_default else 0,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        connection.commit()
        return _get_template_config(cursor.lastrowid)


def update_template_config(config_id: int, payload: TemplateConfigUpdate) -> dict:
    """
    @brief 更新模板配置。

    @param config_id 模板配置 id。
    @param payload 更新请求。
    @return 更新后的模板配置。
    @raises ValueError 当模板配置不存在时抛出。
    """
    current = _get_template_config(config_id)
    name = payload.name if payload.name is not None else current["name"]
    config = payload.config if payload.config is not None else current["config"]
    with get_connection() as connection:
        if payload.is_default:
            connection.execute("UPDATE template_configs SET is_default = 0")
        connection.execute(
            """
            UPDATE template_configs
            SET name = ?, config_json = ?, is_default = CASE WHEN ? IS NULL THEN is_default ELSE ? END
            WHERE id = ?
            """,
            (
                name,
                json.dumps(_normalize_config(config), ensure_ascii=False),
                payload.is_default,
                1 if payload.is_default else 0,
                config_id,
            ),
        )
        connection.commit()
    return _get_template_config(config_id)


def set_default_template_config(config_id: int) -> dict:
    """
    @brief 将指定模板配置设为默认。

    @param config_id 模板配置 id。
    @return 更新后的模板配置。
    @raises ValueError 当模板配置不存在时抛出。
    """
    _get_template_config(config_id)
    with get_connection() as connection:
        connection.execute("UPDATE template_configs SET is_default = 0")
        connection.execute("UPDATE template_configs SET is_default = 1 WHERE id = ?", (config_id,))
        connection.commit()
    return _get_template_config(config_id)


def delete_template_config(config_id: int) -> None:
    """
    @brief 删除非默认模板配置。

    @param config_id 模板配置 id。
    @return None。
    @raises ValueError 当配置不存在或为默认配置时抛出。
    """
    current = _get_template_config(config_id)
    if current["is_default"]:
        raise ValueError("默认模板配置不允许删除")
    with get_connection() as connection:
        connection.execute("DELETE FROM template_configs WHERE id = ?", (config_id,))
        connection.commit()


def merge_with_default_config(config: dict[str, Any] | None) -> dict[str, Any]:
    """
    @brief 将外部模板参数与默认参数合并。

    @param config 外部配置。
    @return 补齐后的配置。
    """
    merged: dict[str, Any] = dict(DEFAULT_TEMPLATE_CONFIG)
    if config:
        merged.update(config)
    return merged


def build_document_format_config(
    template_type: str,
    requirement: str | None = "",
    base_config: dict[str, Any] | None = None,
    use_llm: bool = False,
) -> dict[str, Any]:
    """
    @brief 根据模板类型和用户格式需求生成 Word 格式配置。

    @param template_type 基础模板类型，如实验报告、结课论文。
    @param requirement 用户对格式的自然语言要求。
    @param base_config 前端当前格式配置。
    @param use_llm 是否尝试调用大模型生成配置。
    @return 可直接用于 Word 生成的格式配置。
    """
    fallback = _build_fallback_document_format(template_type, requirement, base_config)
    if not use_llm:
        return fallback
    prompt = _build_document_format_prompt(template_type, requirement or "", fallback)
    parsed = _parse_json_object(call_llm(prompt))
    if not parsed:
        return fallback
    merged = _normalize_document_format({**fallback, **parsed})
    merged["prompt_preview"] = prompt
    return merged


def analyze_format_document(
    content: str,
    base_config: dict[str, Any] | None = None,
    use_llm: bool = False,
) -> dict[str, Any]:
    """
    @brief 分析格式规范文本，抽取格式配置、结构要求和元信息字段。

    @param content 格式规范文本。
    @param base_config 当前格式配置。
    @param use_llm 是否使用 DeepSeek 分析。
    @return 分析结果。
    """
    config = dict(DEFAULT_DOCUMENT_FORMAT)
    if base_config:
        config.update(base_config)
    extracted_rules: list[str] = []
    warnings: list[str] = []
    source_text = content or ""
    text = source_text
    if use_llm:
        extracted_requirement = _extract_requirement_with_llm(source_text)
        if extracted_requirement:
            text = extracted_requirement
            extracted_rules.append("DeepSeek：已提取模板格式要求")
        else:
            warnings.append("DeepSeek 未返回可用提取结果，已使用上传文档原文解析。")
    _apply_font_size_requirement(config, text)
    _apply_spacing_requirement(config, text)
    _apply_format_document_rules(config, text, extracted_rules)
    structure_requirements = _extract_structure_requirements(text)
    metadata_fields = _extract_metadata_fields(text)
    if use_llm and text != source_text:
        config = build_document_format_config(
            str(config.get("template_type") or "课程报告"),
            text,
            config,
            True,
        )
    if not extracted_rules:
        warnings.append("未识别到明确格式规则，请检查规范文本是否包含字体、字号、行距等说明。")
    return {
        "format_config": _normalize_document_format(config),
        "structure_requirements": structure_requirements,
        "metadata_fields": metadata_fields,
        "extracted_rules": extracted_rules,
        "warnings": warnings,
        "requirement_text": text.strip(),
    }


def _extract_requirement_with_llm(content: str) -> str:
    """
    @brief 使用 DeepSeek 从规范文档原文中提炼可用于模板生成的格式要求。

    @param content 规范文档原文。
    @return 提炼后的格式要求；失败时返回空字符串。
    """
    if not content.strip():
        return ""
    prompt = f"""
请从下面的格式规范文档中提取“Word 模板格式要求”，不要写正文内容要求。

输出要求：
1. 只返回 JSON，不要 Markdown。
2. JSON 结构为：{{"requirement_text": "一段中文格式要求"}}。
3. requirement_text 应包含能用于生成 Word 模板的具体要求，例如封面、摘要、目录、标题编号、标题字体字号、正文字体字号、行距、首行缩进、段前段后、表题图题、参考文献等。
4. 忽略与格式无关的课程说明、评分说明、提交说明、代码说明。
5. 如果原文没有明确写某项格式，不要编造具体数值。

规范文档原文：
{content[:8000]}
"""
    parsed = _parse_json_object(call_llm(prompt))
    requirement = parsed.get("requirement_text") if parsed else ""
    return str(requirement or "").strip()


def _build_fallback_document_format(
    template_type: str,
    requirement: str | None,
    base_config: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    @brief 构建本地兜底 Word 格式配置。

    @param template_type 基础模板类型。
    @param requirement 用户自然语言要求。
    @param base_config 当前配置。
    @return 格式配置。
    """
    config = dict(DEFAULT_DOCUMENT_FORMAT)
    config.update(DOCUMENT_TEMPLATE_PRESETS.get(template_type, {"template_type": template_type}))
    if base_config:
        config.update(base_config)
    text = requirement or ""
    if "不空" in text or "不要空" in text or "首行不缩进" in text:
        config["first_line_indent_chars"] = 0
    elif "空两" in text or "缩进两" in text or "空2" in text:
        config["first_line_indent_chars"] = 2
    if "单倍" in text:
        config["line_spacing"] = 1.0
    elif "1.25" in text:
        config["line_spacing"] = 1.25
    elif "1.5" in text or "一点五" in text:
        config["line_spacing"] = 1.5
    elif "2倍" in text or "两倍" in text:
        config["line_spacing"] = 2.0
    if "宋体" in text:
        config["body_font"] = "宋体"
    if "仿宋" in text:
        config["body_font"] = "仿宋"
    if "黑体" in text:
        config["heading_font"] = "黑体"
    if "楷体" in text:
        config["heading_font"] = "楷体"
    if "一、" in text or "中文编号" in text:
        config["heading_numbering"] = "chinese"
    if "1.1" in text or "阿拉伯" in text:
        config["heading_numbering"] = "decimal"
    _apply_font_size_requirement(config, text)
    _apply_spacing_requirement(config, text)
    return _normalize_document_format(config)


def _build_document_format_prompt(template_type: str, requirement: str, fallback: dict[str, Any]) -> str:
    """
    @brief 构建 AI 文档格式模板生成提示词。

    @param template_type 基础模板类型。
    @param requirement 用户格式需求。
    @param fallback 兜底配置。
    @return 提示词。
    """
    return f"""
请根据用户需求生成 Word 文档格式模板配置。注意：这里解决的是 Word 格式，不是正文内容。

只返回 JSON，不要 Markdown 代码块。字段必须使用下列结构：
{{
  "template_type": "实验报告/结课论文/技术分析报告/项目设计文档等",
  "style_name": "模板名称",
  "heading_numbering": "decimal 或 chinese",
  "cover": true,
  "cover_style": "none 或 wuhan_cs_course_design",
  "show_title": true,
  "toc": true,
  "abstract": false,
  "references": false,
  "body_font": "宋体",
  "heading_font": "黑体",
  "ascii_font": "Times New Roman",
  "body_size": 12,
  "heading1_size": 16,
  "heading2_size": 14,
  "heading3_size": 12,
  "line_spacing": 1.5,
  "line_spacing_rule": {{"type": "multiple", "value": 1.5, "unit": "line"}},
  "first_line_indent_chars": 2,
  "paragraph_space_after": 6,
  "body_space_before": {{"value": 0, "unit": "pt"}},
  "body_space_after": {{"value": 6, "unit": "pt"}},
  "heading1_space_before": {{"value": 18, "unit": "pt"}},
  "heading1_space_after": {{"value": 12, "unit": "pt"}},
  "heading2_space_before": {{"value": 12, "unit": "pt"}},
  "heading2_space_after": {{"value": 6, "unit": "pt"}},
  "heading3_space_before": {{"value": 6, "unit": "pt"}},
  "heading3_space_after": {{"value": 6, "unit": "pt"}},
  "table_style": "Table Grid"
}}

约束：
1. 字号必须是数字，单位为 pt。中文字号映射：三号=16pt，小三=15pt，四号=14pt，小四=12pt，五号=10.5pt，小五=9pt。
2. line_spacing 必须是 1.0、1.25、1.35、1.5、2.0 之一。
3. first_line_indent_chars 表示正文段首缩进几个中文字符。
4. heading_numbering 为 decimal 表示 1 / 1.1 / 1.1.1；chinese 表示 一、/ （一）/ 1.
5. body_space_before/body_space_after 和 heading*_space_before/after 表示段前段后间距。
6. 段前段后间距必须使用对象结构：{{"value": 数字, "unit": "pt 或 line"}}。pt 表示磅，line 表示行。
7. 如果用户写“磅”，unit 用 pt；如果用户写“行”，unit 用 line。
8. 如果用户需求不完整，请基于基础模板给出合理默认值。

基础模板类型：{template_type}
用户需求：{requirement or "无"}
当前参考配置：{json.dumps(fallback, ensure_ascii=False)}
"""


def _normalize_document_format(config: dict[str, Any]) -> dict[str, Any]:
    """
    @brief 规范化 Word 格式配置。

    @param config 原始配置。
    @return 规范化配置。
    """
    normalized = dict(DEFAULT_DOCUMENT_FORMAT)
    normalized.update(config)
    normalized["heading_numbering"] = (
        "chinese" if normalized.get("heading_numbering") == "chinese" else "decimal"
    )
    for key in ("cover", "show_title", "toc", "abstract", "references"):
        normalized[key] = bool(normalized.get(key))
    for key, default in (
        ("body_size", 12),
        ("heading1_size", 16),
        ("heading2_size", 14),
        ("heading3_size", 12),
        ("paragraph_space_after", 6),
        ("first_line_indent_chars", 2),
    ):
        normalized[key] = _coerce_number(normalized.get(key), default)
    if "body_space_after" not in normalized and "paragraph_space_after" in normalized:
        normalized["body_space_after"] = {"value": normalized["paragraph_space_after"], "unit": "pt"}
    for key in (
        "body_space_before",
        "body_space_after",
        "heading1_space_before",
        "heading1_space_after",
        "heading2_space_before",
        "heading2_space_after",
        "heading3_space_before",
        "heading3_space_after",
    ):
        normalized[key] = _normalize_spacing_setting(normalized.get(key), DEFAULT_DOCUMENT_FORMAT[key])
    normalized["line_spacing"] = _closest_line_spacing(normalized.get("line_spacing"))
    normalized["line_spacing_rule"] = _normalize_line_spacing_rule(normalized.get("line_spacing_rule"), normalized["line_spacing"])
    for key in ("body_font", "heading_font", "ascii_font", "table_style", "template_type", "style_name", "cover_style"):
        normalized[key] = str(normalized.get(key) or DEFAULT_DOCUMENT_FORMAT[key])
    for key in ("table_title_font", "table_body_font", "figure_title_font"):
        normalized[key] = str(normalized.get(key) or DEFAULT_DOCUMENT_FORMAT[key])
    for key, default in (("table_title_size", 12), ("table_body_size", 10.5), ("figure_title_size", 12)):
        normalized[key] = _coerce_number(normalized.get(key), default)
    return normalized


def _coerce_number(value: Any, default: float) -> float:
    """
    @brief 将任意值转换为数字。

    @param value 原始值。
    @param default 默认值。
    @return 数字。
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _normalize_spacing_setting(value: Any, default: dict[str, Any]) -> dict[str, Any]:
    """
    @brief 规范段前段后间距配置。

    @param value 原始值。
    @param default 默认值。
    @return {"value": 数字, "unit": "pt/line"}。
    """
    if isinstance(value, dict):
        number = _coerce_number(value.get("value"), default["value"])
        unit = str(value.get("unit") or default["unit"]).lower()
    else:
        number = _coerce_number(value, default["value"])
        unit = str(default["unit"]).lower()
    if unit in ("磅", "point", "points"):
        unit = "pt"
    if unit in ("行", "lines"):
        unit = "line"
    if unit not in ("pt", "line"):
        unit = default["unit"]
    return {"value": max(0, number), "unit": unit}


def _apply_spacing_requirement(config: dict[str, Any], text: str) -> None:
    """
    @brief 从用户自然语言中提取常见段前段后间距。

    @param config 当前格式配置。
    @param text 用户需求。
    @return None。
    """
    level_aliases = {
        "heading1": ("一级标题", "一标题", "1级标题"),
        "heading2": ("二级标题", "二标题", "2级标题"),
        "heading3": ("三级标题", "三标题", "3级标题"),
        "body": ("正文",),
    }
    edge_aliases = {"before": ("段前",), "after": ("段后",)}
    for target, aliases in level_aliases.items():
        for edge, edge_words in edge_aliases.items():
            for alias in aliases:
                for edge_word in edge_words:
                    match = re.search(
                        rf"{alias}[^，。,；;\n]*{edge_word}\s*(\d+(?:\.\d+)?)\s*(磅|pt|行)?",
                        text,
                        flags=re.I,
                    )
                    if match:
                        unit = match.group(2) or "pt"
                        if unit == "磅":
                            unit = "pt"
                        config[f"{target}_space_{edge}"] = {
                            "value": float(match.group(1)),
                            "unit": "line" if unit == "行" else unit.lower(),
                        }


def _apply_font_size_requirement(config: dict[str, Any], text: str) -> None:
    """
    @brief 从自然语言中解析中文字号。

    @param config 当前格式配置。
    @param text 用户需求。
    @return None。
    """
    for label, size in CHINESE_FONT_SIZE_TO_PT.items():
        if f"正文{label}" in text or f"正文字号{label}" in text or f"正文为{label}" in text or f"正文用{label}" in text:
            config["body_size"] = size
        if f"一级标题{label}" in text or f"一级标题字号{label}" in text or f"一级标题用{label}" in text:
            config["heading1_size"] = size
        if f"二级标题{label}" in text or f"二级标题字号{label}" in text or f"二级标题用{label}" in text:
            config["heading2_size"] = size
        if f"三级标题{label}" in text or f"三级标题字号{label}" in text or f"三级标题用{label}" in text:
            config["heading3_size"] = size
    title_match = re.search(r"标题[^，。,；;\n]*(初号|小初|小一|小二|小三|小四|小五|小六|一号|二号|三号|四号|五号|六号|七号|八号)", text)
    if title_match and not any(word in text for word in ("一级标题", "二级标题", "三级标题")):
        config["heading1_size"] = CHINESE_FONT_SIZE_TO_PT[title_match.group(1)]
    body_match = re.search(r"正文[^，。,；;\n]*(初号|小初|小一|小二|小三|小四|小五|小六|一号|二号|三号|四号|五号|六号|七号|八号)", text)
    if body_match:
        config["body_size"] = CHINESE_FONT_SIZE_TO_PT[body_match.group(1)]


def _apply_format_document_rules(config: dict[str, Any], text: str, extracted_rules: list[str]) -> None:
    """
    @brief 从格式规范全文中提取常见格式规则。

    @param config 当前格式配置。
    @param text 规范文本。
    @param extracted_rules 已识别规则说明列表。
    @return None。
    """
    if "正文行间距固定为23磅" in text or re.search(r"正文[^。；;\n]*行间距固定为\s*23\s*磅", text):
        config["line_spacing_rule"] = {"type": "exact", "value": 23, "unit": "pt"}
        config["line_spacing"] = 1.5
        extracted_rules.append("正文行间距：固定 23 磅")
    line_match = re.search(r"行间距固定为\s*(\d+(?:\.\d+)?)\s*磅", text)
    if line_match and not any(rule.startswith("正文行间距") for rule in extracted_rules):
        config["line_spacing_rule"] = {"type": "exact", "value": float(line_match.group(1)), "unit": "pt"}
        extracted_rules.append(f"固定行距：{line_match.group(1)} 磅")
    if "正文" in text and "宋体" in text and ("小4" in text or "小四" in text):
        config["body_font"] = "宋体"
        config["body_size"] = 12
        extracted_rules.append("正文：宋体小四")
    if "黑体小2" in text or "黑体小二" in text:
        config["heading_font"] = "黑体"
        config["heading1_size"] = 18
        extracted_rules.append("章标题：黑体小二")
    if "黑体4号" in text or "黑体四号" in text:
        config["heading2_size"] = 14
        extracted_rules.append("节标题：黑体四号")
    if "黑体小4" in text or "黑体小四" in text:
        config["heading3_size"] = 12
        extracted_rules.append("三级标题：黑体小四")
    chapter_spacing = re.search(
        r"章标题段前为\s*(\d+(?:\.\d+)?)\s*行[、,，]\s*段后为\s*(\d+(?:\.\d+)?)\s*行",
        text,
    )
    if chapter_spacing:
        config["heading1_space_before"] = {"value": float(chapter_spacing.group(1)), "unit": "line"}
        config["heading1_space_after"] = {"value": float(chapter_spacing.group(2)), "unit": "line"}
        extracted_rules.append(
            f"章标题段前 {chapter_spacing.group(1)} 行，段后 {chapter_spacing.group(2)} 行"
        )
    if "表标题中文黑体小4" in text or "表标题中文黑体小四" in text:
        config["table_title_font"] = "黑体"
        config["table_title_size"] = 12
        extracted_rules.append("表标题：中文黑体小四")
    if "表内容宋体" in text and ("5号" in text or "五号" in text):
        config["table_body_font"] = "宋体"
        config["table_body_size"] = 10.5
        extracted_rules.append("表内容：宋体五号")
    if "图" in text and ("图1.2" in text or "图2.2" in text):
        config["figure_title_font"] = "宋体"
        config["figure_title_size"] = 12
        extracted_rules.append("图题：按章节编号生成")
    if "目录" in text:
        config["toc"] = True
    if "摘要" in text:
        config["abstract"] = True
    if "参考文献" in text:
        config["references"] = True
    if "封面" in text:
        config["cover"] = True
        config["cover_style"] = "wuhan_cs_course_design"
        extracted_rules.append("封面：武汉大学计算机学院课程设计封面样式")


def _extract_structure_requirements(text: str) -> list[dict[str, Any]]:
    """
    @brief 从规范文本中提取结构要求。

    @param text 规范文本。
    @return 结构要求列表。
    """
    candidates = [
        ("cover", "封面"),
        ("declaration", "学术声明"),
        ("abstract", "中文摘要"),
        ("keywords", "关键词"),
        ("toc", "目录"),
        ("body", "正文"),
        ("conclusion", "结论"),
        ("references", "参考文献"),
        ("appendix", "附录"),
        ("teacher_comment", "教师评语评分"),
    ]
    return [{"key": key, "label": label} for key, label in candidates if label in text]


def _extract_metadata_fields(text: str) -> list[dict[str, str]]:
    """
    @brief 从规范文本中提取封面元信息字段。

    @param text 规范文本。
    @return 字段列表。
    """
    fields = [
        ("major_name", "专业名称"),
        ("course_name", "课程名称"),
        ("advisor_1", "指导教师一"),
        ("advisor_2", "指导教师二"),
        ("student_id", "学生学号"),
        ("student_name", "学生姓名"),
    ]
    compact_text = re.sub(r"\s+", "", text)
    return [
        {"key": key, "label": label}
        for key, label in fields
        if label in text or label.replace(" ", "") in compact_text
    ]


def _closest_line_spacing(value: Any) -> float:
    """
    @brief 将行距规范到允许选项。

    @param value 原始行距。
    @return 规范行距。
    """
    allowed = [1.0, 1.25, 1.35, 1.5, 2.0]
    number = _coerce_number(value, 1.5)
    return min(allowed, key=lambda item: abs(item - number))


def _normalize_line_spacing_rule(value: Any, default_multiple: float = 1.5) -> dict[str, Any]:
    """
    @brief 规范行距规则。

    @param value 原始行距规则。
    @param default_multiple 默认倍数行距。
    @return 规范后的行距规则。
    """
    if isinstance(value, dict):
        rule_type = str(value.get("type") or "multiple").lower()
        number = _coerce_number(value.get("value"), default_multiple)
        unit = str(value.get("unit") or ("pt" if rule_type == "exact" else "line")).lower()
    else:
        rule_type = "multiple"
        number = default_multiple
        unit = "line"
    if rule_type not in ("multiple", "exact"):
        rule_type = "multiple"
    if unit in ("磅", "point", "points"):
        unit = "pt"
    if unit in ("行", "lines"):
        unit = "line"
    if rule_type == "exact":
        unit = "pt"
    return {"type": rule_type, "value": max(0, number), "unit": unit}


def _parse_json_object(value: str | None) -> dict[str, Any] | None:
    """
    @brief 从模型输出中解析 JSON 对象。

    @param value 模型输出文本。
    @return JSON 对象；失败时返回 None。
    """
    if not value:
        return None
    cleaned = re.sub(r"^```(?:json)?|```$", "", value.strip(), flags=re.I).strip()
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


def _get_template_config(config_id: int) -> dict:
    """
    @brief 查询单个模板配置。

    @param config_id 模板配置 id。
    @return 模板配置字典。
    @raises ValueError 当配置不存在时抛出。
    """
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM template_configs WHERE id = ?", (config_id,)).fetchone()
    if row is None:
        raise ValueError("模板配置不存在")
    return _row_to_template(row)


def _row_to_template(row) -> dict:
    """
    @brief 将 SQLite 行转换为接口返回结构。

    @param row SQLite 行。
    @return 模板配置字典。
    """
    try:
        config = json.loads(row["config_json"])
    except json.JSONDecodeError:
        config = {}
    return {
        "id": row["id"],
        "name": row["name"],
        "config": merge_with_default_config(config),
        "is_default": bool(row["is_default"]),
        "created_at": row["created_at"],
    }


def _normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    @brief 规范化模板配置，补齐缺省字段。

    @param config 原始配置。
    @return 规范化后的配置。
    """
    return merge_with_default_config(config)
