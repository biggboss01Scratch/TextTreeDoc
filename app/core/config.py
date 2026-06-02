"""
@file config.py
@brief 项目路径和运行配置模块。

该模块集中维护数据库、上传目录、生成目录和模板目录等路径配置。

@author TextTreeDoc 项目组
@date 2026
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = PROJECT_ROOT / "uploaded"
GENERATED_DIR = PROJECT_ROOT / "generated"
TEMPLATE_DIR = PROJECT_ROOT / "templates"
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"

DB_PATH = DATA_DIR / "text_tree_doc.db"
REPORT_TEMPLATE_PATH = TEMPLATE_DIR / "report_template.docx"


def ensure_runtime_dirs() -> None:
    """
    @brief 创建项目运行所需目录。

    @return None。
    """
    for directory in (DATA_DIR, UPLOAD_DIR, GENERATED_DIR, TEMPLATE_DIR):
        directory.mkdir(parents=True, exist_ok=True)

