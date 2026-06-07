"""
@file template_api.py
@brief 模板配置接口模块。
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    DocumentTemplateBuildRequest,
    TemplateConfigCreate,
    TemplateConfigOut,
    TemplateConfigUpdate,
)
from app.services import template_service

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
