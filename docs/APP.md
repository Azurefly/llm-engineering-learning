# 本地学习应用

这是一个 local-first 大模型工程学习与考试应用，支持**多用户注册、登录以及用户学习数据物理隔离**。稳定运行入口为 `app.current:app`。

完整版本演进与实现细节见：[V5：逐题自适应测试与长期运行](V5.md)。多用户说明见：[多用户登录、注册与数据隔离](MULTI_USER.md)。

## 当前能力

- 多用户自主注册、登录、退出；
- 每个用户独立 SQLite 学习数据库与备份目录；
- Week 0～18 中英文课程阅读与进度记录；
- 系统评分考试，禁止手工填写考试成绩；
- 随机周测、阶段考试、错题复习、计时、自动保存、超时交卷；
- 单选、多选、判断、填空确定性评分；简答题按严格 Rubric 自动评分；
- 约 190+ 道题，并有题库质量门禁；
- 历史考试完整冻结试题内容；
- Week 2～18 Python 代码实训，可选 Docker Sandbox + pytest 自动评分；
- 知识点掌握度、六维能力画像、薄弱项推荐；
- 逐题自适应测试（CAT），每答一题再选择下一题；
- 进行中的 CAT 可恢复或放弃；
- Markdown 思考笔记、标签、课程关联；
- 外部资料链接库；
- 全局搜索课程、当前用户思考和当前用户外链；
- SQLite WAL、自动滚动备份、完整 JSON 导出/恢复；
- 系统诊断与本地 Web 安全硬化。

## 注册与登录

首次打开受保护页面时会自动跳转到：

```text
/login
```

默认允许自主注册：

```text
/register
LLM_ALLOW_REGISTRATION=1
```

如果已经创建完所需账号，不希望继续开放注册：

```text
LLM_ALLOW_REGISTRATION=0
```

关闭注册不会影响已有账号登录。

密码不会明文保存。Session 使用 HttpOnly、SameSite=Lax Cookie；默认有效期 30 天：

```text
LLM_SESSION_DAYS=30
```

HTTPS 反向代理部署时可以启用：

```text
LLM_COOKIE_SECURE=1
```

## 用户数据隔离

账号数据和学习数据分开：

```text
data/
├─ accounts.db
└─ users/
   ├─ <storage-key-A>/
   │  ├─ learning.db
   │  └─ backups/
   └─ <storage-key-B>/
      ├─ learning.db
      └─ backups/
```

`accounts.db` 只保存用户和 Session。每个用户的以下内容都存放在自己的 `learning.db`：

- 学习进度和系统成绩；
- 考试、答题、错题与试卷快照；
- 考试草稿和自动保存状态；
- 代码实训结果；
- 能力画像和 CAT 会话；
- 思考笔记；
- 外部资料；
- 备份恢复相关数据。

因此隔离不依赖所有 SQL 都正确添加 `user_id` 条件，而是不同用户使用不同 SQLite 文件。

### 旧单用户数据升级

如果升级前已经存在：

```text
data/learning.db
```

并且里面有学习记录，第一个成功注册的账号会自动复制并继承该历史数据库。原始 `data/learning.db` 不会自动删除。之后注册的用户从新的独立数据库开始。

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

Python 数据默认位于：

```text
data/accounts.db
data/users/<storage-key>/learning.db
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

其中：

```text
/data/accounts.db
/data/users/<storage-key>/learning.db
/data/users/<storage-key>/backups/
```

普通停止不会删除数据：

```bash
docker compose down
```

只有显式执行下面命令才会删除整个 Docker volume，包含**所有账号和全部用户学习数据**：

```bash
docker compose down -v
```

迁移数据时优先使用应用内“数据与备份”页面，而不是直接复制正在运行的 SQLite 文件。

## 主要页面

| 页面 | 路径 |
|---|---|
| 登录 | `/login` |
| 注册 | `/register` |
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

“数据与备份”仅操作**当前登录用户**的数据，支持：

- 下载当前用户完整 JSON；
- 备份格式校验；
- 恢复前显式确认；
- 恢复前自动生成当前用户安全快照；
- 事务恢复和失败回滚；
- 旧版备份兼容；
- 外链协议和关键字段安全校验。

账号、密码哈希、Session 以及其他用户数据不会进入个人学习 JSON 备份。

启动/首次访问用户空间时默认检查滚动自动备份：

```text
LLM_AUTO_BACKUP=1
LLM_AUTO_BACKUP_HOURS=24
LLM_AUTO_BACKUP_KEEP=10
```

备份同样位于各用户自己的 `backups/` 目录。

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

默认部署仍以本机或受控局域网为目标：

- 未登录不能读取或写入学习数据；
- Python 默认监听 `127.0.0.1`；
- Docker 默认仅映射 `127.0.0.1:8765`；
- 用户密码安全哈希，不保存明文；
- Session Cookie 为 HttpOnly + SameSite=Lax；
- Trusted Host；
- 跨站写请求拦截；
- Markdown HTML 清洗；
- 外链只允许 HTTP(S)；
- 安全响应头；
- 敏感 JSON 禁止缓存。

如果开放到局域网，建议增加 HTTPS 反向代理，并配置：

```text
LLM_ALLOWED_HOSTS=learning.local,192.168.1.10
LLM_COOKIE_SECURE=1
```

不希望开放自主注册时同时设置：

```text
LLM_ALLOW_REGISTRATION=0
```

## 健康与诊断

基础健康检查（无需登录）：

```text
GET /health
```

完整诊断（需要登录，只检查当前用户学习数据库）：

```text
GET /diagnostics
GET /api/diagnostics
```

诊断会检查当前用户 SQLite integrity、WAL、busy timeout、题库质量、代码 Runner 和当前用户备份状态。
