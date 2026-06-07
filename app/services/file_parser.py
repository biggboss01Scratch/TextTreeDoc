"""
@file file_parser.py
@brief 上传文件解析模块。

该模块负责解析 txt、md、docx 和 pdf 文件内容，并将其转换为可入库的纯文本。

@author TextTreeDoc 项目组
@date 2026
"""

from pathlib import Path

from docx import Document
from pypdf import PdfReader


def parse_uploaded_file(path: Path) -> str:
    """
    @brief 解析上传文件内容。

    @param path 上传文件保存路径。
    @return 文件中的纯文本内容。
    @raises ValueError 当文件类型不受支持时抛出。
    """
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".docx":
        document = Document(path)
        return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())
    if suffix == ".pdf":
        reader = PdfReader(path)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(page.strip() for page in pages if page.strip())
    raise ValueError("仅支持 .txt、.md、.docx、.pdf 文件")
