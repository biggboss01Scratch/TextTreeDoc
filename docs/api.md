# 接口说明

本文档列出 TextTreeDoc 当前主要 HTTP 接口。后端启动后，也可以访问 FastAPI 自动生成的交互式文档：

```text
http://127.0.0.1:8000/docs
```

通用说明：

- 请求体一般使用 JSON。
- 文件上传接口使用 `multipart/form-data`。
- 前端开发环境默认调用 `http://127.0.0.1:8000`。

## 文本库

### GET /libraries

查询文本库列表。

### POST /libraries

创建文本库。

```json
{
  "name": "课程设计资料",
  "description": "数据库课程设计相关资料"
}
```

### DELETE /libraries/{library_id}

删除文本库。删除前请确认是否仍有文本资料依赖该文本库。

### GET /texts

查询文本列表。可选参数：

- `keyword`：搜索关键词
- `library_id`：文本库 id

### POST /texts

新增文本资料。

```json
{
  "title": "开源许可证概述",
  "content": "正文内容",
  "keywords": "开源,许可证"
}
```

### DELETE /texts/{text_id}

删除文本资料。

## 文件上传

### POST /upload

使用 `multipart/form-data` 上传 `.txt`、`.md`、`.docx` 或 `.pdf` 文件。可选表单字段：

- `library_id`：目标文本库 id。

PDF 上传支持文字型 PDF 的文本提取；扫描版 PDF 需要先进行 OCR。

## 格式模板

### POST /templates/document-format/build

根据模板类型和自然语言格式要求生成 Word 格式配置。

```json
{
  "template_type": "实验报告",
  "requirement": "正文宋体小四，1.5 倍行距，一级标题黑体三号。",
  "use_llm": true
}
```

### POST /templates/configs/analyze-format-file

分析格式规范文本，抽取 Word 格式配置、结构要求和元信息字段。

```json
{
  "content": "正文宋体小四，首行缩进两个中文字符，段后 6 磅。",
  "use_llm": false
}
```

## 文档生成

### POST /documents/tree

根据主题和文本库资料生成结构树。

```json
{
  "topic": "开源许可证分析报告",
  "use_llm": true,
  "library_ids": [1],
  "template_config": {
    "body_font": "宋体",
    "body_size": 12
  }
}
```

返回值会包含 `generation_meta`，用于判断本次是否真正调用 AI。

### POST /documents/fill

根据结构树和文本库资料填充正文。

```json
{
  "topic": "开源许可证分析报告",
  "tree": {
    "title": "开源许可证分析报告",
    "sections": []
  },
  "use_llm": true,
  "library_ids": [1]
}
```

### POST /documents/docx

根据已经确认的文档树生成 Word 文件。

```json
{
  "title": "开源许可证分析报告",
  "tree": {
    "title": "开源许可证分析报告",
    "sections": []
  }
}
```

### GET /documents/download/{filename}

下载生成的 docx 文件。

## 图片素材

### GET /images

查询图片素材列表。

### POST /images

上传图片素材。支持 `.png`、`.jpg`、`.jpeg`。

表单字段：

- `file`：图片文件。
- `name`：图片名称。
- `caption`：Word 图注。
- `description`：图片说明。

### PUT /images/{image_id}

更新图片名称、图注或说明。

### DELETE /images/{image_id}

删除图片素材和本地文件。

### GET /images/{image_id}/file

预览图片文件。
