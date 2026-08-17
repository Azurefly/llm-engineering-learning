# 本地学习应用

这是一个面向个人长期学习的 local-first 大模型工程学习与考试应用。稳定运行入口为 `app.current:app`。

完整版本演进与实现细节见：[V5：逐题自适应测试与长期运行](V5.md)。

## 当前能力

- Week 0～18 中英文课程阅读与进度记录；
- 系统评分考试，禁止手工填写考试成绩；
- 随机周测、阶段考试、错题复习、计时、自动保存、超时交卷；
- 单选、多选、判断、填空确定性评分；简答题按严格 Rubric 自动评分；
- 约 190+ 道题，并有题库质量门禁；
- 历史考试完整冻结试题内容；
- Python 代码实训，可选 Docker Sandbox + pytest 自动评分；
- 知识点掌握度、六维能力画像、薄弱项推荐；
- 逐题自适应测试（CAT），每答一题再选择下一题；
- 进行中的 CAT 可恢复或放弃；
- Markdown 思考笔记、标签、课程关联；
- 外部资料链接库；
- 全局搜索课程、思考和外链；
- SQLite 本地存储、自动滚动备份、完整 JSON 导出/恢复；
- 系统诊断与本地 Web 安全硬化。

## Python 启动

建议 Python 3.11 或 3.12，优先使用已经过 CI 验证的依赖固定版本：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.lock.txt
python run.py
```

Linux / macOS：

```bash
source .venv/bin/activate
pip install -r requirements.lock.txt
python run.py
```

打开：`http://127.0.0.1:8765`。

Python 模式数据默认保存在：

```text
data/learning.db
```

`data/*` 已被 Git 忽略，不会正常提交到仓库。

## Docker Compose

```bash
docker compose up -d --build
```

打开：`http://127.0.0.1:8765`。

Docker 默认使用 named volume：

```text
llm-engineering-learning-data
```

数据库位于容器 `/data/learning.db`。named volume 用于避免 Linux、macOS、Windows 上 bind mount 的 UID/权限差异。

普通停止不会删除数据：

```bash
docker compose down
```

只有显式执行下面命令才会删除 Docker volume：

```bash
docker compose down -v
```

迁移数据时优先使用应用内“数据与备份”页面，而不是直接复制 SQLite 文件。

## 主要页面

| 页面 | 路径 |
|---|---|
| 学习总览 | `/` |
| 自适应学习画像 | `/adaptive` |
| 逐题自适应测试 | `/adaptive-test` |
| 考试中心 | `/exam-lab` |
| 代码实训 | `/coding-labs` |
| 错题本 | `/mistakes` |
| 成绩趋势 | `/exam-history` |
| 思考笔记 | `/thoughts` |
| 外部资料 | `/resources` |
| 全局搜索 | `/search` |
| 数据与备份 | `/data-management` |
| 系统诊断 | `/diagnostics` |

## 数据保护

“数据与备份”支持：

- 下载完整 JSON；
- 备份格式校验；
- 恢复前显式确认；
- 恢复前自动生成安全快照；
- 事务恢复和失败回滚；
- 旧版备份兼容；
- 外链协议和关键字段安全校验。

启动时默认还会生成滚动自动备份：

```text
LLM_AUTO_BACKUP=1
LLM_AUTO_BACKUP_HOURS=24
LLM_AUTO_BACKUP_KEEP=10
```

## 代码实训

任意学习者代码默认不会执行。启用 Docker 代码沙箱前先构建：

```bash
docker build -t llm-learning-sandbox:py312 sandbox
```

然后设置：

```text
LLM_CODE_RUNNER=docker
LLM_CODE_RUNNER_IMAGE=llm-learning-sandbox:py312
```

代码沙箱使用无网络、资源限制、非 root、只读工作区、能力移除等边界，并由 CI 真实执行 Smoke Test。

## 安全边界

本项目默认是单用户本地应用：

- Python 默认监听 `127.0.0.1`；
- Docker 仅映射 `127.0.0.1:8765`；
- Trusted Host；
- 跨站写请求拦截；
- Markdown HTML 清洗；
- 外链只允许 HTTP(S)；
- 安全响应头；
- 敏感 JSON 禁止缓存。

若需要放到局域网或公网，应额外增加认证和反向代理；那属于多用户/网络部署范围，不是当前本地单用户默认模式。

## 健康与诊断

基础健康检查：

```text
GET /health
```

完整诊断：

```text
GET /diagnostics
GET /api/diagnostics
```

诊断会检查 SQLite integrity、WAL、busy timeout、题库质量、代码 Runner 和备份状态。
