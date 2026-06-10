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
    """
    @brief 文本资料创建请求模型。

    用于手动新增资料或文件解析后入库。
    """

    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    summary: str | None = None
    keywords: str | None = None
    source_type: str = "manual"
    source_url: str | None = ""
    library_id: int | None = None
    created_by: str | None = "anonymous"


class TextOut(BaseModel):
    """
    @brief 文本资料响应模型。
    """

    id: int
    title: str
    summary: str | None
    content: str
    keywords: str | None
    source_type: str | None
    source_url: str | None
    library_id: int | None = None
    created_at: str | None
    created_by: str | None


class LibraryCreate(BaseModel):
    """
    @brief 文本库创建请求模型。
    """

    name: str = Field(..., min_length=1)
    description: str | None = ""


class LibraryOut(BaseModel):
    """
    @brief 文本库响应模型。
    """

    id: int
    name: str
    description: str | None
    created_at: str | None
    count: int = 0


class ImageUpdate(BaseModel):
    """
    @brief 图片素材元信息更新请求模型。
    """

    name: str | None = None
    caption: str | None = None
    description: str | None = None


class ImageOut(BaseModel):
    """
    @brief 图片素材响应模型。
    """

    id: int
    name: str
    caption: str | None = ""
    description: str | None = ""
    file_path: str
    content_type: str | None = ""
    created_at: str | None
    created_by: str | None = "anonymous"
    preview_url: str


class TemplateConfigCreate(BaseModel):
    """
    @brief 模板参数配置创建请求模型。
    """

    name: str = Field(..., min_length=1)
    config: dict[str, Any]
    is_default: bool = False


class TemplateConfigUpdate(BaseModel):
    """
    @brief 模板参数配置更新请求模型。
    """

    name: str | None = None
    config: dict[str, Any] | None = None
    is_default: bool | None = None


class TemplateConfigOut(BaseModel):
    """
    @brief 模板参数配置响应模型。
    """

    id: int
    name: str
    config: dict[str, Any]
    is_default: bool = False
    created_at: str | None


class DocumentTemplateBuildRequest(BaseModel):
    """
    @brief Word 格式模板生成请求模型。

    该模型描述格式页中“根据自然语言要求生成 Word 格式配置”的输入。
    """

    template_type: str = Field(..., min_length=1)
    requirement: str | None = ""
    base_config: dict[str, Any] | None = None
    use_llm: bool = False


class FormatDocumentAnalyzeRequest(BaseModel):
    """
    @brief 格式规范文档解析请求模型。
    """

    content: str = Field(..., min_length=1)
    base_config: dict[str, Any] | None = None
    use_llm: bool = False


class TreeRequest(BaseModel):
    """
    @brief 文档结构树生成请求模型。
    """

    topic: str = Field(..., min_length=1)
    use_llm: bool = False
    library_ids: list[int] | None = None
    template_config: dict[str, Any] | None = None
    prompt_delta: str | None = None


class FeedbackOptionsRequest(BaseModel):
    """
    @brief 结构树反馈改进选项生成请求模型。
    """

    topic: str = Field(..., min_length=1)
    tree: dict[str, Any]
    feedback: str


class DocxRequest(BaseModel):
    """
    @brief Word 文档生成请求模型。
    """

    title: str
    tree: dict[str, Any]
    format_config: dict[str, Any] | None = None


class FillDocumentRequest(BaseModel):
    """
    @brief 正文填充请求模型。
    """

    topic: str = Field(..., min_length=1)
    tree: dict[str, Any]
    use_llm: bool = False
    library_ids: list[int] | None = None
    template_config: dict[str, Any] | None = None
