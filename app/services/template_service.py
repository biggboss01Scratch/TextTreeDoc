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
    "cover": True,
    "toc": False,
    "abstract": False,
    "references": False,
    "body_font": "宋体",
    "heading_font": "黑体",
    "ascii_font": "Times New Roman",
    "body_size": 11,
    "heading1_size": 16,
    "heading2_size": 14,
    "heading3_size": 12,
    "line_spacing": 1.5,
    "first_line_indent_chars": 2,
    "paragraph_space_after": 6,
    "table_style": "Table Grid",
}

DOCUMENT_TEMPLATE_PRESETS: dict[str, dict[str, Any]] = {
    "实验报告": {
        "template_type": "实验报告",
        "style_name": "实验报告模板",
        "heading_numbering": "decimal",
        "cover": True,
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
        "cover": True,
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
        "cover": True,
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
        "cover": True,
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
  "toc": true,
  "abstract": false,
  "references": false,
  "body_font": "宋体",
  "heading_font": "黑体",
  "ascii_font": "Times New Roman",
  "body_size": 11,
  "heading1_size": 16,
  "heading2_size": 14,
  "heading3_size": 12,
  "line_spacing": 1.5,
  "first_line_indent_chars": 2,
  "paragraph_space_after": 6,
  "table_style": "Table Grid"
}}

约束：
1. 字号必须是数字，单位为 pt。
2. line_spacing 必须是 1.0、1.25、1.35、1.5、2.0 之一。
3. first_line_indent_chars 表示正文段首缩进几个中文字符。
4. heading_numbering 为 decimal 表示 1 / 1.1 / 1.1.1；chinese 表示 一、/ （一）/ 1.
5. 如果用户需求不完整，请基于基础模板给出合理默认值。

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
    for key in ("cover", "toc", "abstract", "references"):
        normalized[key] = bool(normalized.get(key))
    for key, default in (
        ("body_size", 11),
        ("heading1_size", 16),
        ("heading2_size", 14),
        ("heading3_size", 12),
        ("paragraph_space_after", 6),
        ("first_line_indent_chars", 2),
    ):
        normalized[key] = _coerce_number(normalized.get(key), default)
    normalized["line_spacing"] = _closest_line_spacing(normalized.get("line_spacing"))
    for key in ("body_font", "heading_font", "ascii_font", "table_style", "template_type", "style_name"):
        normalized[key] = str(normalized.get(key) or DEFAULT_DOCUMENT_FORMAT[key])
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


def _closest_line_spacing(value: Any) -> float:
    """
    @brief 将行距规范到允许选项。

    @param value 原始行距。
    @return 规范行距。
    """
    allowed = [1.0, 1.25, 1.35, 1.5, 2.0]
    number = _coerce_number(value, 1.5)
    return min(allowed, key=lambda item: abs(item - number))


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
