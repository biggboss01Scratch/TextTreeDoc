"""
@file image_api.py
@brief 图片素材接口模块。

该模块提供图片上传、列表、元信息更新、预览和删除接口。
"""

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.models.schemas import ImageUpdate
from app.services import image_service

router = APIRouter(prefix="/images", tags=["images"])


@router.get("")
def list_images() -> list[dict]:
    """
    @brief 查询图片素材列表。

    @return 图片素材列表。
    """
    return image_service.list_images()


@router.post("")
async def upload_image(
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    caption: str | None = Form(default=""),
    description: str | None = Form(default=""),
) -> dict:
    """
    @brief 上传图片素材。

    @param file 图片文件。
    @param name 图片名称。
    @param caption 图注。
    @param description 图片说明。
    @return 创建后的图片素材。
    """
    try:
        return image_service.create_image(
            filename=file.filename or "image.png",
            content=await file.read(),
            content_type=file.content_type or "",
            name=name,
            caption=caption,
            description=description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{image_id}")
def update_image(image_id: int, payload: ImageUpdate) -> dict:
    """
    @brief 更新图片素材元信息。

    @param image_id 图片素材 id。
    @param payload 更新请求。
    @return 更新后的图片素材。
    """
    try:
        return image_service.update_image(image_id, payload.name, payload.caption, payload.description)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{image_id}")
def delete_image(image_id: int) -> dict:
    """
    @brief 删除图片素材。

    @param image_id 图片素材 id。
    @return 删除结果。
    """
    try:
        image_service.delete_image(image_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}


@router.get("/{image_id}/file")
def get_image_file(image_id: int) -> FileResponse:
    """
    @brief 返回图片文件内容。

    @param image_id 图片素材 id。
    @return 图片文件响应。
    """
    try:
        path = image_service.get_image_path(image_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not path.exists():
        raise HTTPException(status_code=404, detail="图片文件不存在")
    return FileResponse(path, filename=Path(path).name)
