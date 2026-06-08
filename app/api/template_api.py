"""
@file template_api.py
@brief 模板配置接口模块。
"""

import json
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.schemas import (
    DocumentTemplateBuildRequest,
    FormatDocumentAnalyzeRequest,
    TemplateConfigCreate,
    TemplateConfigOut,
    TemplateConfigUpdate,
)
from app.services import template_service
from app.services.file_parser import parse_uploaded_file

router = APIRouter(prefix="/templates/configs", tags=["template-configs"])


@router.get("", response_model=list[TemplateConfigOut])
def list_template_configs() -> list[dict]:
    """
    @brief 查询模板配置列表。

    @return 模板配置列表。
    """
    return template_service.list_template_configs()


@router.get("/default", response_model=TemplateConfigOut)
def get_default_template_config() -> dict:
    """
    @brief 获取默认模板配置。

    @return 默认模板配置。
    """
    return template_service.get_default_template_config()


@router.post("", response_model=TemplateConfigOut)
def create_template_config(payload: TemplateConfigCreate) -> dict:
    """
    @brief 创建模板配置。

    @param payload 模板配置创建请求。
    @return 创建后的模板配置。
    """
    return template_service.create_template_config(payload)


@router.put("/{config_id}", response_model=TemplateConfigOut)
def update_template_config(config_id: int, payload: TemplateConfigUpdate) -> dict:
    """
    @brief 更新模板配置。

    @param config_id 模板配置 id。
    @param payload 更新请求。
    @return 更新后的模板配置。
    """
    try:
        return template_service.update_template_config(config_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{config_id}/default", response_model=TemplateConfigOut)
def set_default_template_config(config_id: int) -> dict:
    """
    @brief 设置默认模板配置。

    @param config_id 模板配置 id。
    @return 更新后的模板配置。
    """
    try:
        return template_service.set_default_template_config(config_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{config_id}")
def delete_template_config(config_id: int) -> dict:
    """
    @brief 删除模板配置。

    @param config_id 模板配置 id。
    @return 操作结果。
    """
    try:
        template_service.delete_template_config(config_id)
        return {"ok": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/document-format")
def build_document_format_config(request: DocumentTemplateBuildRequest) -> dict:
    """
    @brief 根据基础模板和用户格式需求生成 Word 格式配置。

    @param request 包含模板类型、自然语言格式需求和是否使用大模型。
    @return 文档格式配置 JSON。
    """
    return template_service.build_document_format_config(
        request.template_type,
        request.requirement,
        request.base_config,
        request.use_llm,
    )


@router.post("/analyze-format-document")
def analyze_format_document(request: FormatDocumentAnalyzeRequest) -> dict:
    """
    @brief 分析粘贴的格式规范文本。

    @param request 包含规范文本和当前格式配置。
    @return 格式分析结果。
    """
    return template_service.analyze_format_document(request.content, request.base_config, request.use_llm)


@router.post("/analyze-format-file")
async def analyze_format_file(
    file: UploadFile = File(...),
    base_config_json: str | None = Form(default=None),
    use_llm: bool = Form(default=False),
) -> dict:
    """
    @brief 上传格式规范文件并分析。

    @param file 支持 txt、md、docx、pdf。
    @param base_config_json 当前格式配置 JSON。
    @param use_llm 是否预留使用 AI。
    @return 格式分析结果。
    """
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".txt", ".md", ".docx", ".pdf"}:
        raise HTTPException(status_code=400, detail="仅支持 .txt、.md、.docx、.pdf 格式规范文件")
    temp_path = Path("/tmp") / f"format_rule_{Path(file.filename or f'upload{suffix}').name}"
    temp_path.write_bytes(await file.read())
    try:
        content = parse_uploaded_file(temp_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    base_config = None
    if base_config_json:
        try:
            base_config = json.loads(base_config_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="base_config_json 不是有效 JSON") from exc
    return template_service.analyze_format_document(content, base_config, use_llm)
