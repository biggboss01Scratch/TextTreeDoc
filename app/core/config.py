"""
@file config.py
@brief 项目路径和运行配置模块。

该模块集中维护数据库、上传目录、生成目录和模板目录等路径配置。

@author TextTreeDoc 项目组
@date 2026
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = PROJECT_ROOT / "uploaded"
IMAGE_UPLOAD_DIR = UPLOAD_DIR / "images"
GENERATED_DIR = PROJECT_ROOT / "generated"
TEMPLATE_DIR = PROJECT_ROOT / "templates"
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"

DB_PATH = DATA_DIR / "text_tree_doc.db"
REPORT_TEMPLATE_PATH = TEMPLATE_DIR / "report_template.docx"
ENV_LOCAL_PATH = PROJECT_ROOT / ".env.local"


def ensure_runtime_dirs() -> None:
    """
    @brief 创建项目运行所需目录。

    @return None。
    """
    for directory in (DATA_DIR, UPLOAD_DIR, IMAGE_UPLOAD_DIR, GENERATED_DIR, TEMPLATE_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def load_local_env() -> None:
    """
    @brief 从 .env.local 加载本地环境变量。

    @return None。

    该函数只在环境变量尚未存在时写入，避免覆盖服务器或终端中显式配置的值。
    """
    if not ENV_LOCAL_PATH.exists():
        return
    for line in ENV_LOCAL_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
