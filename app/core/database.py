"""
@file database.py
@brief SQLite 数据库初始化与连接管理模块。

该模块负责创建文本库和文档记录表，并插入少量示例文本，
保证项目在首次启动时即可进行完整演示。

@author TextTreeDoc 项目组
@date 2026
"""

import sqlite3
from datetime import datetime
from typing import Iterable

from app.core.config import DB_PATH, ensure_runtime_dirs


def get_connection() -> sqlite3.Connection:
    """
    @brief 获取 SQLite 数据库连接。

    @return SQLite 连接对象，row_factory 已设置为 sqlite3.Row。
    """
    ensure_runtime_dirs()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """
    @brief 初始化数据库表并写入演示数据。

    @return None。

    首次运行时自动创建 texts 和 documents 表，避免用户需要手动准备文本库。
    """
    ensure_runtime_dirs()
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT,
                content TEXT NOT NULL,
                keywords TEXT,
                source_type TEXT,
                source_url TEXT,
                created_at TEXT,
                created_by TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                topic TEXT,
                tree_json TEXT,
                docx_path TEXT,
                created_at TEXT,
                created_by TEXT
            )
            """
        )
        if connection.execute("SELECT COUNT(*) FROM texts").fetchone()[0] == 0:
            _insert_seed_texts(connection)
        connection.commit()


def _insert_seed_texts(connection: sqlite3.Connection) -> None:
    """
    @brief 插入课程演示用的示例文本。

    @param connection SQLite 数据库连接。
    @return None。
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    seed_texts: Iterable[tuple[str, str, str, str, str, str, str]] = [
        (
            "开源许可证概述",
            "开源许可证用于规定软件使用、复制、修改和分发的权利与义务。",
            "开源许可证是开源软件生态的重要基础。MIT 许可证较为宽松，允许商业使用和再分发；GPL 许可证强调派生作品也应保持开源；Apache-2.0 许可证额外提供专利授权条款。选择许可证时需要结合项目目标、社区协作方式和合规要求。",
            "开源,许可证,MIT,GPL,Apache",
            "seed",
            "",
            now,
        ),
        (
            "课程报告自动生成需求",
            "课程报告通常包含背景、资料分析、实现过程、结果展示和总结。",
            "在课程作业场景中，报告生成系统可以从文本库中提取资料，形成结构化文档树，再根据模板生成 Word 文档。系统重点应保证文本入库、主题检索、结构树生成和 docx 导出流程稳定。",
            "课程报告,文档生成,结构树,Word",
            "seed",
            "",
            now,
        ),
        (
            "表格在技术文档中的作用",
            "表格适合展示模块、功能、状态和对比信息。",
            "技术文档中常使用表格呈现模块清单、接口说明和实验结果。自动生成 Word 时，可以在文档结构树中加入 table 类型块，由后端转换为 Word 表格，增强报告的可读性和验收展示效果。",
            "表格,技术文档,Word,模块",
            "seed",
            "",
            now,
        ),
    ]
    connection.executemany(
        """
        INSERT INTO texts (title, summary, content, keywords, source_type, source_url, created_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'system')
        """,
        seed_texts,
    )

