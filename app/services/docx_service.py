"""
@file docx_service.py
@brief Word 文档生成模块。

该模块优先使用 docxtpl 渲染基础模板，再使用 python-docx 动态追加
文档结构树中的多级标题、正文和表格。

@author TextTreeDoc 项目组
@date 2026
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document
from docx.oxml.ns import qn
from docx.shared import RGBColor
from docx.shared import Pt
from docxtpl import DocxTemplate

from app.core.config import GENERATED_DIR, REPORT_TEMPLATE_PATH, ensure_runtime_dirs
from app.core.database import get_connection

TEMPLATE_VERSION = "TextTreeDoc Template v3"
BODY_FONT = "宋体"
HEADING_FONT = "黑体"
ASCII_FONT = "Times New Roman"
TEXT_COLOR = RGBColor(0, 0, 0)
DEFAULT_FORMAT_CONFIG: dict[str, Any] = {
    "heading_numbering": "decimal",
    "body_font": BODY_FONT,
    "heading_font": HEADING_FONT,
    "ascii_font": ASCII_FONT,
    "body_size": 11,
    "heading1_size": 16,
    "heading2_size": 14,
    "heading3_size": 12,
    "line_spacing": 1.5,
    "first_line_indent_chars": 2,
    "paragraph_space_after": 6,
    "table_style": "Table Grid",
}


def ensure_report_template() -> None:
    """
    @brief 确保 docxtpl 报告模板存在。

    @return None。

    没有模板文件时自动创建最小模板，避免项目首次运行时无法生成 Word。
    """
    ensure_runtime_dirs()
    if REPORT_TEMPLATE_PATH.exists() and _template_is_current():
        return
    document = Document()
    _configure_document_styles(document)
    document.core_properties.comments = TEMPLATE_VERSION
    title_paragraph = document.add_heading("{{ title }}", level=0)
    _apply_paragraph_font(title_paragraph, HEADING_FONT, size=22, bold=True)
    meta_paragraph = document.add_paragraph("生成时间：{{ generated_at }}")
    _apply_paragraph_font(meta_paragraph, BODY_FONT, size=11)
    intro_paragraph = document.add_paragraph("本报告由 TextTreeDoc 根据文本库资料和文档结构树自动生成。")
    _apply_paragraph_font(intro_paragraph, BODY_FONT, size=11)
    document.add_page_break()
    document.save(REPORT_TEMPLATE_PATH)


def generate_docx_from_tree(title: str, tree: dict[str, Any], format_config: dict[str, Any] | None = None) -> dict:
    """
    @brief 根据文档结构树生成 docx 文件。

    @param title 文档标题。
    @param tree 文档结构树，包含 title、sections、children 和 blocks 字段。
    @return 包含 filename、path 和 download_url 的字典。
    """
    config = _merge_format_config(format_config)
    ensure_report_template()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}.docx"
    output_path = GENERATED_DIR / filename

    template = DocxTemplate(REPORT_TEMPLATE_PATH)
    template.render({"title": title, "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    template.save(output_path)

    document = Document(output_path)
    _configure_document_styles(document, config)
    _normalize_existing_paragraphs(document, config)
    for index, section in enumerate(tree.get("sections", []), 1):
        _append_section(document, section, level=1, config=config, path=[index])
    document.save(output_path)
    _save_document_record(title, tree, output_path)
    return {
        "filename": filename,
        "path": str(output_path),
        "download_url": f"/documents/download/{filename}",
    }


def _append_section(
    document: Document,
    section: dict[str, Any],
    level: int,
    config: dict[str, Any],
    path: list[int],
) -> None:
    """
    @brief 递归追加文档章节。

    @param document python-docx 文档对象。
    @param section 单个章节节点。
    @param level 当前标题级别。
    @return None。
    """
    heading = section.get("heading")
    if heading:
        paragraph = document.add_heading(_format_heading(heading, level, path, config), level=min(level, 4))
        _apply_paragraph_font(
            paragraph,
            config["heading_font"],
            config["ascii_font"],
            size=_heading_size(level, config),
            bold=True,
        )
    content = section.get("content")
    if content:
        paragraph = document.add_paragraph(content)
        _apply_paragraph_font(
            paragraph,
            config["body_font"],
            config["ascii_font"],
            size=config["body_size"],
            first_line_indent_chars=config["first_line_indent_chars"],
            line_spacing=config["line_spacing"],
            space_after=config["paragraph_space_after"],
        )
    for block in section.get("blocks", []):
        _append_block(document, block, config)
    for index, child in enumerate(section.get("children", []), 1):
        _append_section(document, child, level=level + 1, config=config, path=[*path, index])


def _append_block(document: Document, block: dict[str, Any], config: dict[str, Any]) -> None:
    """
    @brief 将结构树 block 写入 Word。

    @param document python-docx 文档对象。
    @param block 支持 table 类型，预留 image 类型。
    @return None。
    """
    if block.get("type") == "table":
        headers = block.get("headers", [])
        rows = block.get("rows", [])
        if not headers:
            return
        table = document.add_table(rows=1, cols=len(headers))
        try:
            table.style = config["table_style"]
        except (KeyError, ValueError):
            table.style = "Table Grid"
        for index, header in enumerate(headers):
            table.rows[0].cells[index].text = str(header)
            _apply_cell_font(table.rows[0].cells[index], config, bold=True)
        for row in rows:
            cells = table.add_row().cells
            for index, value in enumerate(row[: len(headers)]):
                cells[index].text = str(value)
                _apply_cell_font(cells[index], config)


def _template_is_current() -> bool:
    """
    @brief 判断当前模板是否为最新版本。

    @return 模板版本匹配时返回 True。
    """
    try:
        document = Document(REPORT_TEMPLATE_PATH)
    except Exception:
        return False
    return document.core_properties.comments == TEMPLATE_VERSION


def _configure_document_styles(document: Document, config: dict[str, Any] | None = None) -> None:
    """
    @brief 配置 Word 文档的中文正文和标题样式。

    @param document python-docx 文档对象。
    @return None。
    """
    config = _merge_format_config(config)
    normal = document.styles["Normal"]
    normal.font.name = config["ascii_font"]
    normal.font.size = Pt(config["body_size"])
    normal.font.color.rgb = TEXT_COLOR
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), config["body_font"])
    for style_name, size in (
        ("Title", config["heading1_size"] + 6),
        ("Heading 1", config["heading1_size"]),
        ("Heading 2", config["heading2_size"]),
        ("Heading 3", config["heading3_size"]),
    ):
        if style_name in document.styles:
            style = document.styles[style_name]
            style.font.name = config["ascii_font"]
            style.font.size = Pt(size)
            style.font.bold = True
            style.font.color.rgb = TEXT_COLOR
            style._element.rPr.rFonts.set(qn("w:eastAsia"), config["heading_font"])


def _normalize_existing_paragraphs(document: Document, config: dict[str, Any] | None = None) -> None:
    """
    @brief 统一模板渲染后已有段落的字体和颜色。

    @param document python-docx 文档对象。
    @return None。

    docxtpl 渲染出的封面标题和生成时间来自模板段落，需要额外规范 run，
    避免 Word 主题样式造成中文字体或颜色不一致。
    """
    config = _merge_format_config(config)
    for paragraph in document.paragraphs:
        style_name = paragraph.style.name if paragraph.style else ""
        if style_name == "Title":
            _apply_paragraph_font(
                paragraph,
                config["heading_font"],
                config["ascii_font"],
                size=config["heading1_size"] + 6,
                bold=True,
            )
        elif style_name.startswith("Heading"):
            _apply_paragraph_font(
                paragraph,
                config["heading_font"],
                config["ascii_font"],
                size=config["heading1_size"],
                bold=True,
            )
        else:
            _apply_paragraph_font(paragraph, config["body_font"], config["ascii_font"], size=config["body_size"])


def _apply_paragraph_font(
    paragraph,
    east_asia_font: str,
    ascii_font: str = ASCII_FONT,
    size: float = 11,
    bold: bool = False,
    first_line_indent_chars: float | None = None,
    line_spacing: float | None = None,
    space_after: float | None = None,
) -> None:
    """
    @brief 为段落中的所有 run 设置中英文字体。

    @param paragraph 段落对象。
    @param east_asia_font 中文字体。
    @param size 字号，单位为 pt。
    @param bold 是否加粗。
    @return None。
    """
    for run in paragraph.runs:
        run.font.name = ascii_font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = TEXT_COLOR
        run._element.rPr.rFonts.set(qn("w:eastAsia"), east_asia_font)
    if first_line_indent_chars is not None:
        paragraph.paragraph_format.first_line_indent = Pt(size * first_line_indent_chars)
    if line_spacing is not None:
        paragraph.paragraph_format.line_spacing = line_spacing
    if space_after is not None:
        paragraph.paragraph_format.space_after = Pt(space_after)


def _apply_cell_font(cell, config: dict[str, Any], bold: bool = False) -> None:
    """
    @brief 设置表格单元格字体。

    @param cell 表格单元格。
    @param east_asia_font 中文字体。
    @param bold 是否加粗。
    @return None。
    """
    for paragraph in cell.paragraphs:
        _apply_paragraph_font(
            paragraph,
            config["body_font"],
            config["ascii_font"],
            size=max(9, config["body_size"] - 0.5),
            bold=bold,
            line_spacing=1.15,
            space_after=0,
        )


def _merge_format_config(config: dict[str, Any] | None) -> dict[str, Any]:
    """
    @brief 合并并规范化 Word 格式配置。

    @param config 外部格式配置。
    @return 完整格式配置。
    """
    merged = dict(DEFAULT_FORMAT_CONFIG)
    if config:
        merged.update(config)
    for key in ("body_size", "heading1_size", "heading2_size", "heading3_size", "paragraph_space_after"):
        merged[key] = _as_float(merged.get(key), DEFAULT_FORMAT_CONFIG[key])
    merged["first_line_indent_chars"] = _as_float(merged.get("first_line_indent_chars"), 2)
    merged["line_spacing"] = _as_float(merged.get("line_spacing"), 1.5)
    for key in ("body_font", "heading_font", "ascii_font", "table_style", "heading_numbering"):
        merged[key] = str(merged.get(key) or DEFAULT_FORMAT_CONFIG[key])
    return merged


def _as_float(value: Any, default: float) -> float:
    """
    @brief 将值转换为浮点数。

    @param value 原始值。
    @param default 默认值。
    @return 浮点数。
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _heading_size(level: int, config: dict[str, Any]) -> float:
    """
    @brief 根据标题层级获取字号。

    @param level 标题层级。
    @param config 格式配置。
    @return 字号。
    """
    if level <= 1:
        return config["heading1_size"]
    if level == 2:
        return config["heading2_size"]
    return config["heading3_size"]


def _format_heading(heading: str, level: int, path: list[int], config: dict[str, Any]) -> str:
    """
    @brief 根据编号样式格式化标题文本。

    @param heading 原始标题。
    @param level 标题层级。
    @param path 章节序号路径。
    @param config 格式配置。
    @return 格式化标题。
    """
    title = _strip_heading_prefix(heading)
    if config.get("heading_numbering") == "chinese":
        prefix = _chinese_heading_prefix(level, path)
    else:
        prefix = ".".join(str(item) for item in path) + " "
    return f"{prefix}{title}"


def _strip_heading_prefix(heading: str) -> str:
    """
    @brief 移除已有标题编号。

    @param heading 原始标题。
    @return 去掉编号后的标题。
    """
    import re

    return re.sub(r"^(\d+(?:\.\d+)*[.、]?\s*|[一二三四五六七八九十]+、\s*|（[一二三四五六七八九十]+）\s*)", "", heading).strip()


def _chinese_heading_prefix(level: int, path: list[int]) -> str:
    """
    @brief 生成中文混合编号前缀。

    @param level 标题层级。
    @param path 章节序号路径。
    @return 编号前缀。
    """
    if level <= 1:
        return f"{_to_chinese_number(path[0])}、"
    if level == 2:
        return f"（{_to_chinese_number(path[-1])}）"
    return f"{path[-1]}. "


def _to_chinese_number(number: int) -> str:
    """
    @brief 将 1 到 99 的数字转换为中文序号。

    @param number 数字。
    @return 中文数字。
    """
    digits = "零一二三四五六七八九"
    if number <= 10:
        return "十" if number == 10 else digits[number]
    if number < 20:
        return f"十{digits[number % 10]}"
    tens, ones = divmod(number, 10)
    return f"{digits[tens]}十{digits[ones] if ones else ''}"


def _save_document_record(title: str, tree: dict[str, Any], output_path: Path) -> None:
    """
    @brief 保存生成文档记录。

    @param title 文档标题。
    @param tree 文档结构树。
    @param output_path 生成文件路径。
    @return None。
    """
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (title, topic, tree_json, docx_path, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                tree.get("title", title),
                json.dumps(tree, ensure_ascii=False),
                str(output_path),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "anonymous",
            ),
        )
        connection.commit()
