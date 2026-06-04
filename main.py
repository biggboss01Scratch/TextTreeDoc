"""
@file main.py
@brief TextTreeDoc FastAPI 应用入口。

该文件负责创建 FastAPI 应用、初始化 SQLite 数据库、注册接口路由，
并在前端构建产物存在时托管静态页面。

@author TextTreeDoc 项目组
@date 2026
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import document_api, library_api, template_api, text_api, upload_api
from app.core.config import FRONTEND_DIST_DIR, PROJECT_ROOT, load_local_env
from app.core.database import init_db


app = FastAPI(title="TextTreeDoc", description="基于文本库的文档结构树与 Word 自动生成系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(text_api.router)
app.include_router(upload_api.router)
app.include_router(document_api.router)
app.include_router(library_api.router)
app.include_router(template_api.router)


@app.on_event("startup")
def on_startup() -> None:
    """
    @brief 应用启动时初始化数据库和基础目录。

    @return None。
    """
    load_local_env()
    init_db()


@app.get("/health")
def health_check() -> dict:
    """
    @brief 返回应用健康状态。

    @return 包含 status 字段的 JSON 对象。
    """
    return {"status": "ok"}


if Path(FRONTEND_DIST_DIR).exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
else:
    app.mount("/static", StaticFiles(directory=PROJECT_ROOT), name="static-root")
