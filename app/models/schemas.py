"""
@file schemas.py
@brief FastAPI 请求与响应数据模型。

该模块定义文本入库、文档树生成和 docx 生成所需的 Pydantic 模型。

@author TextTreeDoc 项目组
@date 2026
"""

from typing import Any

from pydantic import BaseModel, Field


class TextCreate(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    summary: str | None = None
    keywords: str | None = None
    source_type: str = "manual"
    source_url: str | None = ""
    created_by: str | None = "anonymous"


class TextOut(BaseModel):
    id: int
    title: str
    summary: str | None
    content: str
    keywords: str | None
    source_type: str | None
    source_url: str | None
    created_at: str | None
    created_by: str | None


class TreeRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    use_llm: bool = False


class DocxRequest(BaseModel):
    title: str
    tree: dict[str, Any]

