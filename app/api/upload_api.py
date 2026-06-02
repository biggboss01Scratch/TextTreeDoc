"""
@file upload_api.py
@brief 文件上传入库接口模块。

该模块支持 txt、md、docx 文件上传，并将解析后的文本保存到文本库。

@author TextTreeDoc 项目组
@date 2026
"""

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import UPLOAD_DIR, ensure_runtime_dirs
from app.models.schemas import TextCreate
from app.services.file_parser import parse_uploaded_file
from app.services.text_service import create_text

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("")
async def upload_file(file: UploadFile = File(...)) -> dict:
    """
    @brief 上传文件并解析入库。

    @param file 上传的 txt、md 或 docx 文件。
    @return 入库后的文本资料。
    """
    ensure_runtime_dirs()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".txt", ".md", ".docx"}:
        raise HTTPException(status_code=400, detail="仅支持 .txt、.md、.docx 文件")
    save_path = UPLOAD_DIR / Path(file.filename or f"upload{suffix}").name
    save_path.write_bytes(await file.read())
    try:
        content = parse_uploaded_file(save_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not content.strip():
        raise HTTPException(status_code=400, detail="文件内容为空")
    text = create_text(
        TextCreate(
            title=save_path.stem,
            content=content,
            source_type="upload",
            source_url=str(save_path),
        )
    )
    return text

