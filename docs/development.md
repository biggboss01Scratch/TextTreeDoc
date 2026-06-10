# 开发说明

## 架构概览

TextTreeDoc 采用前后端分离的开发方式：

- 前端使用 Vue 3 + Vite，负责流程导航、文本库管理、格式配置、结构树展示、图片编排和文档导出操作。
- 后端使用 FastAPI，负责资料入库、文本检索、AI 调用、本地兜底、Word 文档生成和文件下载。
- 数据持久化使用 SQLite，便于课程项目本地部署和演示。

## 核心流程

```text
文本库 -> 格式配置 -> 结构树 -> 图片编排 -> 正文填充 -> Word 导出
```

各阶段职责：

- 文本库：提供生成文档的资料来源。
- 格式配置：决定 Word 字体、字号、行距、段前段后、封面、目录等格式。
- 结构树：决定文档目录骨架和章节层级。
- 图片编排：决定图片素材插入到哪些章节。
- 正文填充：根据结构树和资料生成段落内容。
- Word 导出：将结构、正文、图片和格式配置合成为 `.docx` 文件。

## 后端模块

| 模块 | 职责 |
| --- | --- |
| `main.py` | FastAPI 应用入口、路由注册、静态资源托管 |
| `app/core/config.py` | 路径配置、运行目录创建、环境变量加载 |
| `app/core/database.py` | SQLite 表结构初始化、默认数据写入 |
| `app/models/schemas.py` | Pydantic 请求与响应模型 |
| `app/api/` | HTTP 接口层 |
| `app/services/text_service.py` | 文本资料增删查与摘要关键词生成 |
| `app/services/template_service.py` | Word 格式配置生成与解析 |
| `app/services/tree_service.py` | 本地结构树生成 |
| `app/services/fill_service.py` | 本地正文填充 |
| `app/services/docx_service.py` | Word 文档生成 |
| `app/services/image_service.py` | 图片素材管理 |
| `app/services/llm_service.py` | DeepSeek/OpenAI-compatible API 调用 |

## AI 与本地兜底

项目允许不配置 API Key 运行。未配置 DeepSeek 或调用失败时，后端会使用本地规则继续完成流程，并在接口返回的 `generation_meta` 中标明是否使用 AI。

典型字段：

```json
{
  "provider": "deepseek",
  "used_llm": true,
  "fallback": false,
  "fallback_reason": "",
  "stage": "tree"
}
```

如果调用失败：

```json
{
  "provider": "local",
  "used_llm": false,
  "fallback": true,
  "fallback_reason": "DeepSeek 请求超时",
  "stage": "fill"
}
```

## 文档生成格式

Word 格式配置以 JSON 形式在前后端传递。常见字段包括：

- `cover`：是否生成封面。
- `show_title`：没有封面时是否生成正文标题。
- `toc`：是否生成目录占位。
- `abstract`：是否生成摘要页。
- `body_font` / `heading_font`：正文和标题中文字体。
- `body_size` / `heading1_size`：字号，单位为 pt。
- `line_spacing_rule`：行距，可使用倍数或固定磅值。
- `body_space_before` / `body_space_after`：正文段前段后。
- `heading1_space_before` / `heading1_space_after`：一级标题段前段后。

## 生成开发文档

本项目提供 `Doxyfile`。安装 Doxygen 后运行：

```bash
doxygen Doxyfile
```

输出目录：

```text
docs/doxygen/html/
```

该目录属于生成产物，不建议提交到 Git。
