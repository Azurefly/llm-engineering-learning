# 本地学习应用

仓库除了 Markdown 课程，还内置一个本地优先的轻量学习应用。

## 功能

- 中英文课程切换，学习进度跨语言共享。
- 课程阅读与 0～100% 进度记录。
- 每周测试得分记录。
- Markdown 思考笔记，可关联任意课程并添加标签。
- 外部学习链接库，可保存论文、教程、视频、博客与 GitHub 项目。
- SQLite 本地存储，无需额外数据库。
- JSON 数据备份导出。
- Python 直接启动。
- Docker / Docker Compose 启动。

## 界面设计参考

界面定位为“学习工作区”，而不是传统后台。设计语言参考 Memos 的快速记录、AFFiNE 的知识工作区层级，以及 Tabler 的导航和卡片模式；实现使用原创 CSS，不直接复制第三方页面。

## Python 启动

建议 Python 3.11+：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Linux / macOS：

```bash
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

打开：`http://127.0.0.1:8765`

Python 默认只监听本机 `127.0.0.1`。

## Docker Compose

```bash
docker compose up -d --build
```

打开：`http://127.0.0.1:8765`

停止：

```bash
docker compose down
```

学习数据保存在 `data/learning.db`。Compose 将 `./data` 映射到容器 `/data`，重新构建镜像不会删除学习记录。

## 数据结构

- `lesson_progress`：课程状态、完成百分比、测试分数。
- `thoughts`：个人思考、Markdown 内容、标签、关联课程。
- `resources`：外部 URL、说明、标签、关联课程。

## 备份

左侧点击“导出备份”，或者访问：`http://127.0.0.1:8765/backup.json`

## 健康检查

`GET /health`

## 安全边界

当前版本定位为个人本地学习工具，因此默认没有登录系统。若要把 Docker 端口暴露给局域网或公网，请增加认证和反向代理。用户 Markdown 渲染会进行 HTML 清洗，外部链接仅允许 `http://` 和 `https://`。
