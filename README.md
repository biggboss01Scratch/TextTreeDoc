# TextTreeDoc

TextTreeDoc 是一个基于文本库的 Word 文档自动生成工作台。系统支持导入资料、构建 Word 格式配置、生成文档结构树、安排图片位置、填充正文，并最终导出 `.docx` 文档。

项目用于课程报告、实验报告、结课论文、项目设计文档等场景。没有大模型 API Key 时，系统会使用本地规则兜底；配置 DeepSeek 后，可以让 AI 辅助生成格式、结构树和正文内容。

## 主要功能

- 文本库管理：支持新建文本库、选择文本库、查看资料列表。
- 资料导入：支持 `.txt`、`.md`、`.docx`、文字型 `.pdf`。
- 格式配置：支持模板类型选择、自然语言格式要求、格式规范文件解析。
- 结构树生成：根据主题和文本库资料生成目录结构。
- 图片编排：上传图片素材，并插入到结构树指定章节。
- 正文填充：在结构树确认后，根据文本库资料填充正式正文。
- Word 导出：生成并下载 `.docx` 文档。
- DeepSeek 可选接入：用于 AI 生成格式、结构树、正文和反馈改进。

## 技术栈

- 后端：Python、FastAPI、SQLite
- 文档处理：python-docx、docxtpl、pypdf
- 前端：Vue 3、Vite
- 数据存储：本地 SQLite 数据库

## 目录结构

```text
TextTreeDoc/
├── main.py                 # FastAPI 入口
├── app/
│   ├── api/                # 后端接口
│   ├── core/               # 配置与数据库初始化
│   ├── models/             # 请求/响应模型
│   └── services/           # 文本、模板、图片、docx 等业务逻辑
├── frontend/
│   ├── index.html
│   └── src/                # Vue 前端
├── docs/                   # 项目文档与需求说明
├── data/                   # SQLite 数据库，运行时生成
├── uploaded/               # 上传文件，运行时生成
├── generated/              # 生成的 Word 文档，运行时生成
└── templates/              # Word 基础模板，运行时生成
```

## 安装依赖

建议在 WSL/Linux 环境运行。

### 1. 后端依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 前端依赖

```bash
npm install
```

## 启动项目

需要分别启动后端和前端。

### 1. 启动后端

```bash
source .venv/bin/activate
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
```

后端接口文档：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```text
http://127.0.0.1:8000/health
```

### 2. 启动前端

另开一个终端，在项目根目录运行：

```bash
npm run dev
```

前端访问地址通常是：

```text
http://127.0.0.1:5173
```

如果 5173 被占用，Vite 会自动使用 5174、5175 等端口。

## 使用流程

前端页面按实际文档生成流程拆成 5 步：

### 1. 文本库

在“文本库”页面选择或新建文本库，然后导入资料。

支持上传：

- `.txt`
- `.md`
- `.docx`
- `.pdf`

注意：PDF 目前只支持文字型 PDF。扫描版 PDF 需要先 OCR，再上传识别后的文本或文档。

### 2. 格式

在“格式”页面配置 Word 文档格式。

可以选择基础模板类型：

- 实验报告
- 结课论文
- 技术分析报告
- 项目设计文档

也可以直接输入格式要求，例如：

```text
正文宋体小四，首行缩进两个中文字符，固定行距 23 磅，一级标题黑体三号，标题编号使用 1 / 1.1 / 1.1.1。
```

还可以上传或粘贴格式规范文档，系统会尝试抽取字体、字号、行距、段前段后、封面、目录、摘要等要求。

### 3. 结构树

在“结构树”页面输入文档主题，点击“生成结构树”。

结构树只负责文档骨架，例如：

- 标题
- 一级章节
- 二级章节
- 章节说明
- 表格或图片区块位置

结构树生成后，可以查看图形化目录树，也可以通过弹窗查看原始 JSON。

### 4. 图片

在“图片”页面上传图片素材，并选择要插入的章节。

支持图片格式：

- `.png`
- `.jpg`
- `.jpeg`

图片可以维护：

- 图片名称
- Word 图注
- 图片说明

插入章节后，生成 Word 时会把图片和图注写入对应位置。

### 5. 填充导出

在“填充导出”页面点击“填充正文”，系统会根据结构树、图片和文本库资料生成正文段落。

正文填充完成后，点击“生成 Word”，页面会显示下载入口。

## DeepSeek 配置

项目可以不配置 DeepSeek，未配置时会使用本地规则兜底。

如果需要 AI 生成能力，请在项目根目录创建 `.env.local`：

```bash
cp .env.example .env.local
```

然后编辑 `.env.local`：

```env
DEEPSEEK_API_KEY=你的 DeepSeek API Key
LLM_API_BASE=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

启动后端时会自动读取 `.env.local`。

注意：`.env.local` 已被 `.gitignore` 忽略，不要把真实 API Key 提交到 GitHub。

## 生产构建

如果只想构建前端：

```bash
npm run build
```

构建产物会输出到：

```text
frontend/dist/
```

当 `frontend/dist/` 存在时，FastAPI 会自动托管前端静态页面。

## 常见问题

### 端口 8000 被占用

说明已经有一个后端服务在使用 8000 端口。可以关闭旧进程，或换端口启动：

```bash
python3 -m uvicorn main:app --host 127.0.0.1 --port 8001
```

如果换了后端端口，需要同步设置前端 API 地址。

### 前端报 Failed to fetch

通常是后端没有启动，或前端访问的 API 地址不对。请确认：

- 后端运行在 `http://127.0.0.1:8000`
- 前端运行在 `http://127.0.0.1:5173` 或 Vite 自动分配的端口
- 浏览器控制台没有跨域或网络错误

### 上传 PDF 后内容为空

目前只支持文字型 PDF。扫描版 PDF 需要先使用 OCR 工具识别成文字。

### 目录没有自动显示页码

Word 目录使用的是目录域。生成后打开 Word，可能需要右键目录并选择“更新域”。

## 注意事项

- 本项目默认使用本地 SQLite 数据库，数据会保存在 `data/text_tree_doc.db`。
- `data/`、`uploaded/`、`generated/`、`frontend/dist/` 等运行产物默认不提交。
- 当前 Word 模板能力以参数化生成为主，不是完整复刻任意 `.docx` 模板。
- 封面、目录、摘要等复杂格式仍在持续完善中。

## 开源说明

本项目为课程作业项目。项目使用到的第三方依赖和参考资料记录在 `docs/references.md` 中。

请不要提交真实 API Key、个人隐私资料或不应公开的课程/学校内部文件。
