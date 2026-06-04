"""
@file library_api.py
@brief 文本库管理接口模块。
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import LibraryCreate, LibraryOut, TextOut
from app.services import library_service

router = APIRouter(prefix="/libraries", tags=["libraries"])


@router.get("", response_model=list[LibraryOut])
def list_libraries() -> list[dict]:
    """
    @brief 查询文本库列表。

    @return 文本库列表。
    """
    return library_service.list_libraries()


@router.post("", response_model=LibraryOut)
def create_library(payload: LibraryCreate) -> dict:
    """
    @brief 创建文本库。

    @param payload 文本库创建请求。
    @return 创建后的文本库。
    """
    return library_service.create_library(payload)


@router.delete("/{library_id}")
def delete_library(library_id: int) -> dict:
    """
    @brief 删除文本库。

    @param library_id 文本库 id。
    @return 操作结果。
    """
    try:
        library_service.delete_library(library_id)
        return {"ok": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{library_id}/texts", response_model=list[TextOut])
def get_library_texts(library_id: int) -> list[dict]:
    """
    @brief 查询指定文本库下的文本资料。

    @param library_id 文本库 id。
    @return 文本资料列表。
    """
    try:
        return library_service.get_library_texts(library_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
