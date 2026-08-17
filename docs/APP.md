# 本地学习应用

仓库除了 Markdown 课程，还内置一个本地优先的轻量学习与考试应用。

## 功能

- 中英文课程切换，学习进度跨语言共享。
- 课程阅读进度记录；阅读进度最多只能手工记录到 99%。
- 独立考试中心：开始考试、正式作答、提交、系统判分、成绩单、重考。
- 课程成绩**禁止手工录入**，只有考试系统可以写入。
- 达到试卷及格线后，系统自动将课程标为 100% / 已完成；未通过则保持学习中。
- 单选、多选、判断、填空采用确定性规则自动判分。
- 简答题按照知识点 Rubric 自动给部分分，并显示命中与缺失知识点。
- 每次考试独立保存 Attempt、答题明细、逐题得分、总分和通过状态。
- Markdown 思考笔记，可关联任意课程并添加标签。
- 外部学习链接库，可保存论文、教程、视频、博客与 GitHub 项目。
- SQLite 本地存储，无需额外数据库。
- JSON 备份包含课程进度、思考、链接、考试记录和答题明细。
- Python 直接启动；支持 Docker / Docker Compose。

## 考试流程

```text
学习课程
  ↓
进入考试中心 / 课程右侧考试卡片
  ↓
开始考试（生成独立 Attempt）
  ↓
在线作答
  ↓
提交
  ↓
系统自动判分
  ↓
成绩单 + 逐题反馈
  ↓
通过 → 课程 100% / 已完成
未通过 → 保持学习中，可重新考试
```

当前 Week 0～2 使用混合题型试卷；Week 3～18 已配置基础 Checkpoint 试卷。考试引擎本身支持继续扩充更大的题库。

## 评分规则

### 客观题

单选、多选、判断、填空由程序按标准答案确定性评分，不调用大模型，因此相同答案会得到相同分数。

### 简答题

简答题按照预设知识点 Rubric 自动评分。例如一道题要求覆盖 4 个概念点，回答命中 3 个，则按覆盖比例获得部分分。成绩单会明确显示：

- 命中的知识点；
- 缺失的知识点；
- 本题实际得分 / 满分。

这种方式的优点是离线、可复现、透明。后续可以在此基础上增加可选的本地 LLM / LiteLLM 语义评分器，但系统最终成绩仍应有固定 Rubric 和可审计记录。

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

- `lesson_progress`：课程状态、阅读/完成百分比、考试系统产生的最佳成绩。
- `exam_attempts`：每一次考试的开始时间、提交时间、总分、百分比、及格线和通过状态。
- `exam_answers`：每一道题的原始答案、得分、满分、判定与 Rubric 反馈。
- `thoughts`：个人思考、Markdown 内容、标签、关联课程。
- `resources`：外部 URL、说明、标签、关联课程。

## 备份

左侧点击“导出备份”，或者访问：`http://127.0.0.1:8765/backup.json`

备份会同时包含考试 Attempt 和答题明细。

## 健康检查

`GET /health`

## 安全边界

当前版本定位为个人本地学习工具，因此默认没有登录系统。若要把 Docker 端口暴露给局域网或公网，请增加认证和反向代理。用户 Markdown 渲染会进行 HTML 清洗，外部链接仅允许 `http://` 和 `https://`。
