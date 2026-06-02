# 项目设计说明

## 系统目标

TextTreeDoc 聚焦课程题目“文档创建”：从轻量文本库中检索资料，动态生成文档结构树 JSON，再基于 docxtpl / python-docx 生成 Word 文档。

## 数据库设计

### texts 表

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| id | INTEGER | 文本资料唯一编号 |
| title | TEXT | 文本标题 |
| summary | TEXT | 文本摘要 |
| content | TEXT | 正文内容 |
| keywords | TEXT | 关键词，使用逗号分隔 |
| source_type | TEXT | 来源类型，如 manual、upload、seed |
| source_url | TEXT | 来源地址，可为空 |
| created_at | TEXT | 创建时间 |
| created_by | TEXT | 创建用户 |

### documents 表

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| id | INTEGER | 文档记录唯一编号 |
| title | TEXT | 文档标题 |
| topic | TEXT | 生成主题 |
| tree_json | TEXT | 文档结构树 JSON |
| docx_path | TEXT | 生成 docx 文件路径 |
| created_at | TEXT | 创建时间 |
| created_by | TEXT | 创建用户 |

## 核心模块

- `app/core/database.py`：初始化 SQLite 数据库和演示数据。
- `app/services/text_service.py`：文本资料新增、查询、删除和主题检索。
- `app/services/tree_service.py`：根据主题和相关文本生成文档结构树。
- `app/services/docx_service.py`：自动创建模板，并根据结构树生成 docx。
- `app/services/file_parser.py`：解析 txt、md、docx 上传文件。
- `app/api/*.py`：FastAPI 接口层。

## 文档结构树 JSON

```json
{
  "title": "开源许可证分析报告",
  "sections": [
    {
      "heading": "1. 项目背景",
      "content": "介绍报告背景。",
      "children": [],
      "blocks": [
        {
          "type": "table",
          "headers": ["资料标题", "关键词", "来源"],
          "rows": [["开源许可证概述", "开源,许可证", "seed"]]
        }
      ]
    }
  ]
}
```

当前版本支持 `text` 章节、递归 `children` 和 `table` 类型 blocks。图片 blocks 作为后续扩展。

## 模板策略

项目要求基于 docxtemplate / docxtpl 模板生成 docx。为了保证首次运行可用，后端会在 `templates/report_template.docx` 不存在时自动创建最小模板，再使用 docxtpl 渲染标题和生成时间，最后使用 python-docx 追加动态章节与表格。

