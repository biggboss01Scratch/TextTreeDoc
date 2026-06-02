"""
@file text_api.py
@brief 文本库接口模块。

该模块提供文本新增、查询、详情和删除接口。

@author TextTreeDoc 项目组
@date 2026
"""

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import TextCreate, TextOut
from app.services import text_service

router = APIRouter(prefix="/texts", tags=["texts"])


@router.post("", response_model=TextOut)
def create_text(payload: TextCreate) -> dict:
    """
    @brief 新增文本资料。

    @param payload 文本标题、正文、摘要和关键词等信息。
    @return 新增后的文本资料。
    """
    return text_service.create_text(payload)


@router.get("", response_model=list[TextOut])
def list_texts(keyword: str | None = Query(default=None)) -> list[dict]:
    """
    @brief 查询文本资料列表。

    @param keyword 可选搜索关键词。
    @return 文本资料列表。
    """
    return text_service.list_texts(keyword)


@router.get("/{text_id}", response_model=TextOut)
def get_text(text_id: int) -> dict:
    """
    @brief 获取文本详情。

    @param text_id 文本资料编号。
    @return 文本资料详情。
    """
    try:
        return text_service.get_text(text_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{text_id}")
def delete_text(text_id: int) -> dict:
    """
    @brief 删除文本资料。

    @param text_id 文本资料编号。
    @return 操作结果。
    """
    try:
        text_service.delete_text(text_id)
        return {"ok": True}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

