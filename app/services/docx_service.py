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
from docx.shared import Pt
from docxtpl import DocxTemplate

from app.core.config import GENERATED_DIR, REPORT_TEMPLATE_PATH, ensure_runtime_dirs
from app.core.database import get_connection

TEMPLATE_VERSION = "TextTreeDoc Template v2"
BODY_FONT = "宋体"
HEADING_FONT = "黑体"
ASCII_FONT = "Times New Roman"


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


def generate_docx_from_tree(title: str, tree: dict[str, Any]) -> dict:
    """
    @brief 根据文档结构树生成 docx 文件。

    @param title 文档标题。
    @param tree 文档结构树，包含 title、sections、children 和 blocks 字段。
    @return 包含 filename、path 和 download_url 的字典。
    """
    ensure_report_template()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}.docx"
    output_path = GENERATED_DIR / filename

    template = DocxTemplate(REPORT_TEMPLATE_PATH)
    template.render({"title": title, "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    template.save(output_path)

    document = Document(output_path)
    _configure_document_styles(document)
    for section in tree.get("sections", []):
        _append_section(document, section, level=1)
    document.save(output_path)
    _save_document_record(title, tree, output_path)
    return {
        "filename": filename,
        "path": str(output_path),
        "download_url": f"/documents/download/{filename}",
    }


def _append_section(document: Document, section: dict[str, Any], level: int) -> None:
    """
    @brief 递归追加文档章节。

    @param document python-docx 文档对象。
    @param section 单个章节节点。
    @param level 当前标题级别。
    @return None。
    """
    heading = section.get("heading")
    if heading:
        paragraph = document.add_heading(heading, level=min(level, 4))
        _apply_paragraph_font(paragraph, HEADING_FONT, size=max(12, 18 - level * 2), bold=True)
    content = section.get("content")
    if content:
        paragraph = document.add_paragraph(content)
        _apply_paragraph_font(paragraph, BODY_FONT, size=11)
    for block in section.get("blocks", []):
        _append_block(document, block)
    for child in section.get("children", []):
        _append_section(document, child, level=level + 1)


def _append_block(document: Document, block: dict[str, Any]) -> None:
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
        table.style = "Table Grid"
        for index, header in enumerate(headers):
            table.rows[0].cells[index].text = str(header)
            _apply_cell_font(table.rows[0].cells[index], BODY_FONT, bold=True)
        for row in rows:
            cells = table.add_row().cells
            for index, value in enumerate(row[: len(headers)]):
                cells[index].text = str(value)
                _apply_cell_font(cells[index], BODY_FONT)


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


def _configure_document_styles(document: Document) -> None:
    """
    @brief 配置 Word 文档的中文正文和标题样式。

    @param document python-docx 文档对象。
    @return None。
    """
    normal = document.styles["Normal"]
    normal.font.name = ASCII_FONT
    normal.font.size = Pt(11)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
    for style_name, size in (("Title", 22), ("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 12)):
        if style_name in document.styles:
            style = document.styles[style_name]
            style.font.name = ASCII_FONT
            style.font.size = Pt(size)
            style.font.bold = True
            style._element.rPr.rFonts.set(qn("w:eastAsia"), HEADING_FONT)


def _apply_paragraph_font(paragraph, east_asia_font: str, size: int = 11, bold: bool = False) -> None:
    """
    @brief 为段落中的所有 run 设置中英文字体。

    @param paragraph 段落对象。
    @param east_asia_font 中文字体。
    @param size 字号，单位为 pt。
    @param bold 是否加粗。
    @return None。
    """
    for run in paragraph.runs:
        run.font.name = ASCII_FONT
        run.font.size = Pt(size)
        run.font.bold = bold
        run._element.rPr.rFonts.set(qn("w:eastAsia"), east_asia_font)


def _apply_cell_font(cell, east_asia_font: str, bold: bool = False) -> None:
    """
    @brief 设置表格单元格字体。

    @param cell 表格单元格。
    @param east_asia_font 中文字体。
    @param bold 是否加粗。
    @return None。
    """
    for paragraph in cell.paragraphs:
        _apply_paragraph_font(paragraph, east_asia_font, size=10.5, bold=bold)


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
