"""
@file image_service.py
@brief 图片素材库业务逻辑模块。

该模块负责图片素材的保存、查询、更新和删除。图片素材可以被结构树
中的 image block 引用，并在生成 Word 时插入文档。
"""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.core.config import IMAGE_UPLOAD_DIR, ensure_runtime_dirs
from app.core.database import get_connection

ALLOWED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
ALLOWED_IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg"}


def create_image(
    filename: str,
    content: bytes,
    content_type: str | None = "",
    name: str | None = None,
    caption: str | None = "",
    description: str | None = "",
    created_by: str = "anonymous",
) -> dict:
    """
    @brief 保存图片并创建素材记录。

    @param filename 原始文件名。
    @param content 图片二进制内容。
    @param content_type 文件 MIME 类型。
    @param name 可选图片名称。
    @param caption 可选图注。
    @param description 可选说明。
    @return 创建后的图片素材。
    """
    ensure_runtime_dirs()
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        raise ValueError("仅支持 .png、.jpg、.jpeg 图片")
    if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise ValueError("图片类型不受支持")
    safe_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}{suffix}"
    save_path = IMAGE_UPLOAD_DIR / safe_name
    save_path.write_bytes(content)
    title = (name or Path(filename).stem or "未命名图片").strip()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO images (name, caption, description, file_path, content_type, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                caption or f"图：{title}",
                description or "",
                str(save_path),
                content_type or "",
                created_at,
                created_by,
            ),
        )
        connection.commit()
        return get_image(cursor.lastrowid)


def list_images() -> list[dict]:
    """
    @brief 查询图片素材列表。

    @return 图片素材列表。
    """
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM images ORDER BY id DESC").fetchall()
    return [_row_to_image(row) for row in rows]


def get_image(image_id: int) -> dict:
    """
    @brief 获取图片素材详情。

    @param image_id 图片素材 id。
    @return 图片素材。
    @raises ValueError 图片不存在时抛出。
    """
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
    if row is None:
        raise ValueError("图片素材不存在")
    return _row_to_image(row)


def update_image(image_id: int, name: str | None, caption: str | None, description: str | None) -> dict:
    """
    @brief 更新图片元信息。

    @param image_id 图片素材 id。
    @param name 图片名称。
    @param caption 图注。
    @param description 图片说明。
    @return 更新后的图片素材。
    """
    current = get_image(image_id)
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE images
            SET name = ?, caption = ?, description = ?
            WHERE id = ?
            """,
            (
                name if name is not None else current["name"],
                caption if caption is not None else current["caption"],
                description if description is not None else current["description"],
                image_id,
            ),
        )
        connection.commit()
    return get_image(image_id)


def delete_image(image_id: int) -> None:
    """
    @brief 删除图片素材和本地文件。

    @param image_id 图片素材 id。
    @return None。
    """
    image = get_image(image_id)
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM images WHERE id = ?", (image_id,))
        connection.commit()
    if cursor.rowcount == 0:
        raise ValueError("图片素材不存在")
    path = Path(image["file_path"])
    if path.exists() and IMAGE_UPLOAD_DIR.resolve() in path.resolve().parents:
        path.unlink()


def get_image_path(image_id: int) -> Path:
    """
    @brief 获取图片文件路径。

    @param image_id 图片素材 id。
    @return 图片文件路径。
    """
    image = get_image(image_id)
    return Path(image["file_path"])


def _row_to_image(row) -> dict:
    data = dict(row)
    data["preview_url"] = f"/images/{data['id']}/file"
    return data
