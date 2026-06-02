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
from docxtpl import DocxTemplate

from app.core.config import GENERATED_DIR, REPORT_TEMPLATE_PATH, ensure_runtime_dirs
from app.core.database import get_connection


def ensure_report_template() -> None:
    """
    @brief 确保 docxtpl 报告模板存在。

    @return None。

    没有模板文件时自动创建最小模板，避免项目首次运行时无法生成 Word。
    """
    ensure_runtime_dirs()
    if REPORT_TEMPLATE_PATH.exists():
        return
    document = Document()
    document.add_heading("{{ title }}", level=0)
    document.add_paragraph("生成时间：{{ generated_at }}")
    document.add_paragraph("本报告由 TextTreeDoc 根据文本库资料和文档结构树自动生成。")
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
        document.add_heading(heading, level=min(level, 4))
    content = section.get("content")
    if content:
        document.add_paragraph(content)
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
        for row in rows:
            cells = table.add_row().cells
            for index, value in enumerate(row[: len(headers)]):
                cells[index].text = str(value)


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

