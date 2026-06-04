"""
@file library_service.py
@brief 文本库管理业务逻辑模块。

该模块负责文本库的查询、创建、删除，以及默认文本库管理。
"""

from datetime import datetime

from app.core.database import get_connection
from app.models.schemas import LibraryCreate


DEFAULT_LIBRARY_NAME = "默认文本库"


def list_libraries() -> list[dict]:
    """
    @brief 查询所有文本库，并附带每个文本库下的资料数量。

    @return 文本库列表。
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                l.id,
                l.name,
                l.description,
                l.created_at,
                COUNT(t.id) AS count
            FROM text_libraries l
            LEFT JOIN texts t ON t.library_id = l.id
            GROUP BY l.id
            ORDER BY l.id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def create_library(payload: LibraryCreate) -> dict:
    """
    @brief 创建文本库。

    @param payload 文本库创建请求。
    @return 创建后的文本库。
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO text_libraries (name, description, created_at)
            VALUES (?, ?, ?)
            """,
            (payload.name, payload.description or "", now),
        )
        connection.commit()
        return _get_library(cursor.lastrowid)


def delete_library(library_id: int) -> None:
    """
    @brief 删除非默认文本库，并同步删除该库下的文本。

    @param library_id 文本库 id。
    @return None。
    @raises ValueError 当文本库不存在或试图删除默认文本库时抛出。
    """
    default_id = get_default_library_id()
    if library_id == default_id:
        raise ValueError("默认文本库不允许删除")
    with get_connection() as connection:
        row = connection.execute("SELECT id FROM text_libraries WHERE id = ?", (library_id,)).fetchone()
        if row is None:
            raise ValueError("文本库不存在")
        connection.execute("DELETE FROM texts WHERE library_id = ?", (library_id,))
        connection.execute("DELETE FROM text_libraries WHERE id = ?", (library_id,))
        connection.commit()


def get_library_texts(library_id: int) -> list[dict]:
    """
    @brief 查询指定文本库下的文本资料。

    @param library_id 文本库 id。
    @return 文本资料列表。
    @raises ValueError 当文本库不存在时抛出。
    """
    with get_connection() as connection:
        library = connection.execute("SELECT id FROM text_libraries WHERE id = ?", (library_id,)).fetchone()
        if library is None:
            raise ValueError("文本库不存在")
        rows = connection.execute(
            "SELECT * FROM texts WHERE library_id = ? ORDER BY id DESC",
            (library_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_default_library_id() -> int:
    """
    @brief 获取默认文本库 id，如不存在则自动创建。

    @return 默认文本库 id。
    """
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM text_libraries WHERE name = ? ORDER BY id LIMIT 1",
            (DEFAULT_LIBRARY_NAME,),
        ).fetchone()
        if row:
            return int(row["id"])
        cursor = connection.execute(
            """
            INSERT INTO text_libraries (name, description, created_at)
            VALUES (?, ?, ?)
            """,
            (
                DEFAULT_LIBRARY_NAME,
                "系统初始化创建的默认资料库。",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)


def _get_library(library_id: int) -> dict:
    """
    @brief 查询单个文本库，并附带 count 字段。

    @param library_id 文本库 id。
    @return 文本库字典。
    """
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                l.id,
                l.name,
                l.description,
                l.created_at,
                COUNT(t.id) AS count
            FROM text_libraries l
            LEFT JOIN texts t ON t.library_id = l.id
            WHERE l.id = ?
            GROUP BY l.id
            """,
            (library_id,),
        ).fetchone()
    return dict(row)
