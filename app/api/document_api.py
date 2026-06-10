"""
@file document_api.py
@brief 文档结构树和 Word 生成接口模块。

该模块提供根据主题生成文档结构树、根据结构树生成 docx、
以及下载生成文件的接口。

@author TextTreeDoc 项目组
@date 2026
"""

import json
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import GENERATED_DIR
from app.models.schemas import DocxRequest, FeedbackOptionsRequest, FillDocumentRequest, TreeRequest
from app.services.docx_service import generate_docx_from_tree
from app.services.fill_service import fill_document_locally
from app.services.llm_service import call_llm_with_status
from app.services.prompt_service import build_feedback_options_prompt, build_fill_document_prompt, build_generation_prompt
from app.services.template_service import get_default_template_config
from app.services.text_service import search_related_texts
from app.services.tree_service import generate_tree

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/tree")
def create_document_tree(request: TreeRequest) -> dict:
    """
    @brief 根据主题生成文档结构树。

    @param request 包含 topic 和 use_llm 字段的请求体。
    @return 文档结构树 JSON。
    """
    related_texts = search_related_texts(request.topic, library_ids=request.library_ids)
    config = request.template_config or get_default_template_config()["config"]
    prompt_preview = build_generation_prompt(
        request.topic,
        related_texts,
        config,
        request.prompt_delta,
    )
    if request.use_llm:
        llm_text, generation_meta = call_llm_with_status(prompt_preview)
        llm_tree = _parse_json_object(llm_text)
        if llm_tree:
            llm_tree.setdefault("title", request.topic)
            llm_tree["prompt_preview"] = prompt_preview
            llm_tree["generation_meta"] = {
                **generation_meta,
                "stage": "tree",
            }
            return llm_tree
        generation_meta = {
            **generation_meta,
            "provider": "local",
            "used_llm": False,
            "fallback": True,
            "fallback_reason": generation_meta.get("fallback_reason") or "DeepSeek 返回内容不是合法结构树 JSON",
            "stage": "tree",
        }
    else:
        generation_meta = {
            "provider": "local",
            "used_llm": False,
            "fallback": False,
            "fallback_reason": "",
            "stage": "tree",
        }
    tree = generate_tree(request.topic, related_texts)
    tree["prompt_preview"] = prompt_preview
    tree["generation_meta"] = generation_meta
    return tree


@router.post("/fill")
def fill_document_content(request: FillDocumentRequest) -> dict:
    """
    @brief 根据结构树和文本库资料填充正式正文。

    @param request 包含 topic、tree 和模板参数。
    @return 填充 paragraphs 后的文档树。
    """
    related_texts = search_related_texts(request.topic, library_ids=request.library_ids, limit=8)
    config = request.template_config or get_default_template_config()["config"]
    prompt_preview = build_fill_document_prompt(request.topic, request.tree, related_texts, config)
    if request.use_llm:
        llm_text, generation_meta = call_llm_with_status(prompt_preview)
        llm_document = _parse_json_object(llm_text)
        if llm_document:
            llm_document.setdefault("title", request.tree.get("title") or request.topic)
            llm_document["prompt_preview"] = prompt_preview
            llm_document["generation_meta"] = {
                **generation_meta,
                "stage": "fill",
            }
            return llm_document
        generation_meta = {
            **generation_meta,
            "provider": "local",
            "used_llm": False,
            "fallback": True,
            "fallback_reason": generation_meta.get("fallback_reason") or "DeepSeek 返回内容不是合法正文 JSON",
            "stage": "fill",
        }
    else:
        generation_meta = {
            "provider": "local",
            "used_llm": False,
            "fallback": False,
            "fallback_reason": "",
            "stage": "fill",
        }
    filled = fill_document_locally(request.topic, request.tree, related_texts)
    filled["prompt_preview"] = prompt_preview
    filled["generation_meta"] = generation_meta
    return filled


@router.post("/docx")
def create_docx(request: DocxRequest) -> dict:
    """
    @brief 根据文档结构树生成 Word 文件。

    @param request 包含标题和文档树的请求体。
    @return 文件名和下载地址。
    """
    return generate_docx_from_tree(request.title, request.tree, request.format_config)


@router.post("/feedback-options")
def create_feedback_options(request: FeedbackOptionsRequest) -> dict:
    """
    @brief 根据用户反馈生成可选改进方向。

    @param request 包含主题、当前结构树和用户反馈。
    @return 改进选项及 prompt 预览。
    """
    prompt_preview = build_feedback_options_prompt(request.topic, request.tree, request.feedback)
    llm_text, generation_meta = call_llm_with_status(prompt_preview)
    llm_result = _parse_json_object(llm_text)
    if llm_result and isinstance(llm_result.get("options"), list):
        llm_result["prompt_preview"] = prompt_preview
        llm_result["generation_meta"] = {
            **generation_meta,
            "stage": "feedback-options",
        }
        return llm_result
    return {
        "question": "你希望如何改进当前文档？",
        "options": [
            {
                "label": "扩展章节内容",
                "description": "增加每个章节的说明和分析。",
                "prompt_delta": "提高文本详细程度，扩展每个章节正文。",
            },
            {
                "label": "提升正式程度",
                "description": "让语言更规范、更适合课程报告。",
                "prompt_delta": "提高语言正式程度和专业程度。",
            },
            {
                "label": "增强资料引用",
                "description": "更多结合文本库资料进行归纳分析。",
                "prompt_delta": "提高资料引用强度，增加对资料内容的分析。",
            },
        ],
        "prompt_preview": prompt_preview,
        "generation_meta": {
            **generation_meta,
            "provider": "local",
            "used_llm": False,
            "fallback": True,
            "fallback_reason": generation_meta.get("fallback_reason") or "DeepSeek 返回内容不是合法反馈选项 JSON",
            "stage": "feedback-options",
        },
    }


@router.get("/download/{filename}")
def download_docx(filename: str) -> FileResponse:
    """
    @brief 下载生成的 Word 文件。

    @param filename generated 目录下的文件名。
    @return docx 文件响应。
    """
    path = (GENERATED_DIR / filename).resolve()
    generated_root = GENERATED_DIR.resolve()
    if generated_root not in path.parents or not path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def _parse_json_object(value: str | None) -> dict[str, Any] | None:
    """
    @brief 从模型输出中解析 JSON 对象。

    @param value 模型输出文本。
    @return JSON 对象；失败时返回 None。
    """
    if not value:
        return None
    cleaned = re.sub(r"^```(?:json)?|```$", "", value.strip(), flags=re.I).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None
