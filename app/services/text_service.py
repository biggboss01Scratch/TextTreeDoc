"""
@file text_service.py
@brief 文本库业务逻辑模块。

该模块负责文本资料的新增、查询、详情读取和删除。
文本资料是后续文档结构树生成的主要数据来源。

@author TextTreeDoc 项目组
@date 2026
"""

import re
from datetime import datetime

from app.core.database import get_connection
from app.models.schemas import TextCreate
from app.services.llm_service import generate_keywords, generate_summary


def create_text(payload: TextCreate) -> dict:
    """
    @brief 新增一条文本资料。

    @param payload 文本创建请求体。
    @return 新增后的文本资料字典。
    """
    summary = payload.summary or generate_summary(payload.content)
    keywords = payload.keywords or ",".join(generate_keywords(payload.title, payload.content))
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO texts (title, summary, content, keywords, source_type, source_url, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.title,
                summary,
                payload.content,
                keywords,
                payload.source_type,
                payload.source_url or "",
                created_at,
                payload.created_by or "anonymous",
            ),
        )
        connection.commit()
        return get_text(cursor.lastrowid)


def list_texts(keyword: str | None = None) -> list[dict]:
    """
    @brief 查询文本资料列表。

    @param keyword 可选搜索关键词，会匹配标题、摘要、关键词和正文。
    @return 文本资料字典列表。
    """
    with get_connection() as connection:
        if keyword:
            pattern = f"%{keyword}%"
            rows = connection.execute(
                """
                SELECT * FROM texts
                WHERE title LIKE ? OR summary LIKE ? OR keywords LIKE ? OR content LIKE ?
                ORDER BY id DESC
                """,
                (pattern, pattern, pattern, pattern),
            ).fetchall()
        else:
            rows = connection.execute("SELECT * FROM texts ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]


def get_text(text_id: int) -> dict:
    """
    @brief 根据编号读取文本详情。

    @param text_id 文本资料编号。
    @return 文本资料字典。
    @raises ValueError 当文本不存在时抛出。
    """
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM texts WHERE id = ?", (text_id,)).fetchone()
    if row is None:
        raise ValueError("文本资料不存在")
    return dict(row)


def delete_text(text_id: int) -> None:
    """
    @brief 删除指定文本资料。

    @param text_id 文本资料编号。
    @return None。
    @raises ValueError 当文本不存在时抛出。
    """
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM texts WHERE id = ?", (text_id,))
        connection.commit()
    if cursor.rowcount == 0:
        raise ValueError("文本资料不存在")


def search_related_texts(topic: str, limit: int = 5) -> list[dict]:
    """
    @brief 根据主题检索相关文本资料。

    @param topic 用户输入的文档主题。
    @param limit 返回数量上限。
    @return 相关文本资料列表。

    优先按主题关键词匹配；如果没有命中，则返回最近的资料作为演示兜底。
    """
    keywords = _split_topic_keywords(topic)
    with get_connection() as connection:
        clauses = []
        values = []
        for word in keywords:
            pattern = f"%{word}%"
            clauses.append("(title LIKE ? OR keywords LIKE ? OR summary LIKE ? OR content LIKE ?)")
            values.extend([pattern, pattern, pattern, pattern])
        rows = connection.execute(
            f"SELECT * FROM texts WHERE {' OR '.join(clauses)} ORDER BY id DESC LIMIT ?",
            (*values, limit),
        ).fetchall()
        if not rows:
            rows = connection.execute("SELECT * FROM texts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]


def _split_topic_keywords(topic: str) -> list[str]:
    """
    @brief 将文档主题拆分为适合 SQLite LIKE 检索的关键词。

    @param topic 用户输入的文档主题。
    @return 去重后的关键词列表。

    中文主题常常没有空格，因此额外生成 2 到 4 字窗口，提升“开源许可证分析报告”
    对“开源许可证概述”等资料的命中率。
    """
    normalized = topic.replace("，", " ").replace(",", " ")
    words = [word for word in normalized.split() if word]
    chinese_chunks = re.findall(r"[\u4e00-\u9fa5]{2,}", topic)
    for chunk in chinese_chunks:
        for size in (4, 3, 2):
            for index in range(0, max(len(chunk) - size + 1, 0)):
                words.append(chunk[index : index + size])
    unique_words = []
    for word in words or [topic]:
        if word and word not in unique_words:
            unique_words.append(word)
    return unique_words[:12]
