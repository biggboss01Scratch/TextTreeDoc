# 接口说明

## 文本库

### GET /texts

查询文本列表。可选参数：

- `keyword`：搜索关键词

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

使用 `multipart/form-data` 上传 `.txt`、`.md`、`.docx` 或 `.pdf` 文件。

PDF 上传支持文字型 PDF 的文本提取；扫描版 PDF 需要先进行 OCR。

## 文档生成

### POST /documents/tree

```json
{
  "topic": "开源许可证分析报告",
  "use_llm": false
}
```

### POST /documents/docx

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
