"""
@file document_api.py
@brief 文档结构树和 Word 生成接口模块。

该模块提供根据主题生成文档结构树、根据结构树生成 docx、
以及下载生成文件的接口。

@author TextTreeDoc 项目组
@date 2026
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import GENERATED_DIR
from app.models.schemas import DocxRequest, TreeRequest
from app.services.docx_service import generate_docx_from_tree
from app.services.text_service import search_related_texts
from app.services.tree_service import generate_tree

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/tree")
def create_document_tree(request: TreeRequest) -> dict:
    """
    @brief 根据主题生成文档结构树。

    @param request 包含 topic 和 use_llm 字段的请求体。
    @return 文档结构树 JSON。
    """
    related_texts = search_related_texts(request.topic)
    return generate_tree(request.topic, related_texts)


@router.post("/docx")
def create_docx(request: DocxRequest) -> dict:
    """
    @brief 根据文档结构树生成 Word 文件。

    @param request 包含标题和文档树的请求体。
    @return 文件名和下载地址。
    """
    return generate_docx_from_tree(request.title, request.tree)


@router.get("/download/{filename}")
def download_docx(filename: str) -> FileResponse:
    """
    @brief 下载生成的 Word 文件。

    @param filename generated 目录下的文件名。
    @return docx 文件响应。
    """
    path = (GENERATED_DIR / filename).resolve()
    generated_root = GENERATED_DIR.resolve()
    if generated_root not in path.parents or not path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

