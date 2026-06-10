# 贡献指南

感谢参与 TextTreeDoc。本文档说明本项目的开发、注释和提交规范，便于课程开源项目协作与验收。

## 开发环境

- 推荐环境：WSL/Linux
- 后端：Python 3.10+
- 前端：Node.js 18+
- 数据库：SQLite，本地文件位于 `data/text_tree_doc.db`

安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
```

启动服务：

```bash
source .venv/bin/activate
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
```

另开终端：

```bash
npm run dev
```

## 代码规范

- 后端接口放在 `app/api/`。
- 业务逻辑放在 `app/services/`。
- 数据库和配置相关代码放在 `app/core/`。
- 请求和响应模型放在 `app/models/schemas.py`。
- 前端当前集中在 `frontend/src/App.vue` 和 `frontend/src/style.css`。
- 不要提交 `.env.local`、数据库、上传文件和生成的 Word 文档。

## Doxygen 注释规范

Python 模块、公开函数和关键私有函数使用 Doxygen 风格注释：

```python
def example(name: str) -> dict:
    """
    @brief 示例函数说明。

    @param name 参数说明。
    @return 返回值说明。
    @raises ValueError 异常说明。
    """
```

模块文件头建议包含：

```python
"""
@file example.py
@brief 模块职责说明。

@author TextTreeDoc 项目组
@date 2026
"""
```

注释应说明“为什么”和“模块边界”，不要重复显而易见的语句。

## 提交前检查

建议提交前运行：

```bash
python3 -m compileall main.py app
npm run build
```

如安装了 Doxygen，可生成接口文档：

```bash
doxygen Doxyfile
```

生成结果位于 `docs/doxygen/html/`，该目录不建议提交。

## Git 提交流程

```bash
git status
git add README.md CONTRIBUTING.md Doxyfile docs app frontend
git commit -m "docs: improve project documentation and comments"
git push
```

如果当前分支没有 upstream：

```bash
git push -u origin 当前分支名
```
