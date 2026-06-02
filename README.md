# TextTreeDoc

基于文本库的文档结构树生成与 Word 自动生成系统。项目面向《开源技术与应用》课程大作业，重点完成“文档创建”方向：维护轻量文本库，根据主题生成文档结构树 JSON，并基于 docxtpl / python-docx 自动导出 Word 文档。

## 功能特性

- 文本资料新增、查询、删除
- txt / md / docx 文件上传解析入库
- SQLite 数据库自动初始化，并内置演示资料
- 根据主题检索文本库并生成文档结构树
- 自动创建最小 docxtpl 模板
- 根据结构树生成包含标题、正文、表格的 docx 文件
- Vue 3 前端页面，支持完整演示流程

## 技术栈

- 后端：Python、FastAPI、SQLite
- 文档生成：docxtpl、python-docx
- 前端：Vite、Vue 3

## 目录结构

```text
TextTreeDoc/
├── main.py
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   └── services/
├── frontend/
│   └── src/
├── data/
├── uploaded/
├── generated/
├── templates/
└── docs/
```

## 安装与运行

安装后端依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

启动后端：

```bash
uvicorn main:app --reload
```

安装前端依赖并启动：

```bash
npm install
npm run dev
```

访问前端：

```text
http://127.0.0.1:5173
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

## 接口说明

- `GET /texts`：查询文本列表，支持 `keyword` 参数
- `POST /texts`：新增文本资料
- `GET /texts/{text_id}`：查看文本详情
- `DELETE /texts/{text_id}`：删除文本资料
- `POST /upload`：上传 txt / md / docx 文件并入库
- `POST /documents/tree`：根据主题生成文档结构树
- `POST /documents/docx`：根据结构树生成 Word 文档
- `GET /documents/download/{filename}`：下载生成的 Word 文档

## 使用示例

1. 启动 FastAPI 后端和 Vue 前端。
2. 打开前端页面。
3. 新增几条文本资料，或上传 txt / md / docx 文件。
4. 输入文档主题，例如“开源许可证分析报告”。
5. 点击“生成结构树”查看 JSON。
6. 点击“生成 Word”，下载生成的 docx 文件。

## 开源说明

本项目为课程作业项目，遵循开源项目的基本组织方式，包含 README、requirements.txt、接口说明、设计文档和参考项目记录。

项目开发过程中参考的第三方开源项目、依赖库和资料统一记录在 `docs/references.md` 中。

如项目中仅使用第三方库作为依赖，不直接复制其源码，则在文档中列出其名称、用途和许可证。如后续直接复制或改写第三方项目源码，将在对应源码文件和 `docs/references.md` 中保留原项目版权与许可证说明。

## License

本项目为《开源技术与应用》课程作业，当前许可证暂定。  
在项目最终提交前，将根据实际使用的第三方开源项目许可证情况，统一选择合适的开源许可证。  
若未直接复制受限制许可证项目的源码，项目默认倾向采用 MIT License。

