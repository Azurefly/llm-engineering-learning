# 多用户登录、注册与数据隔离

当前应用支持多用户自主注册、登录、退出，并对每个用户的学习数据做物理隔离；超级管理员额外拥有账号治理、学习进度报表和自主注册策略控制能力。

## 数据布局

```text
data/
├─ accounts.db
└─ users/
   ├─ <storage_key-A>/
   │  ├─ learning.db
   │  └─ backups/
   └─ <storage_key-B>/
      ├─ learning.db
      └─ backups/
```

`accounts.db` 保存账号、Session 和全局系统设置；课程进度、考试、答题、错题、代码实训、思考、外链、能力画像、自适应测试和备份全部保存在各自用户目录中。

因此用户数据不是依赖应用层 `WHERE user_id=?` 做逻辑隔离，而是位于不同 SQLite 文件中。

## 注册与注册策略

首次启动、尚未保存管理员策略时，默认值来自：

```text
LLM_ALLOW_REGISTRATION=1
```

第一个成功注册的账号自动成为 `SUPERADMIN`。超级管理员可进入：

```text
/admin/users
```

直接点击“停止自主注册 / 开启自主注册”。该设置写入 `accounts.db.system_settings`，立即生效，无需重启。

关闭后：

- `/register` 返回 `403`；
- 已有用户仍可登录；
- 超级管理员仍可手工创建用户。

一旦后台保存过策略，`accounts.db` 中的值优先于 `LLM_ALLOW_REGISTRATION` 环境变量。

注册规则：

- 用户名 3～32 个字符；
- 支持 Unicode 字母/数字，以及 `. _ -`；
- 显示名称可选，最长 64 字符；
- 密码 8～128 字符；
- 用户名经 NFKC + casefold 规范化后保证唯一。

## 密码与 Session

密码不会明文保存，使用随机 Salt 的 PBKDF2-HMAC-SHA256 哈希。

登录成功后生成随机 Session Token；数据库只保存 Token 的 SHA-256 摘要。浏览器 Cookie 使用：

- `HttpOnly`；
- `SameSite=Lax`；
- HTTPS 或显式配置时启用 `Secure`。

默认 Session 有效期 30 天，可配置：

```text
LLM_SESSION_DAYS=30
```

允许范围 1～90 天。

如果通过 HTTPS 反向代理部署，可显式启用：

```text
LLM_COOKIE_SECURE=1
```

## 超级管理员进度报表

超级管理员可以打开：

```text
/admin/report
/admin/report/data
/admin/users/<id>/progress
```

查看全体用户的学习总进度、Week 0～18 推进、系统考试、代码实训、活跃度和单用户逐周进度。

跨用户读取严格限制在统计白名单：

```text
lesson_progress
exam_attempts
code_attempts
```

不会输出：

- 思考笔记正文；
- 外部链接/资料正文；
- 用户代码源文件；
- 密码摘要；
- storage key；
- 用户数据库路径。

因此“用户数据库物理隔离”仍然成立；超级管理员只是拥有受控的跨用户**只读统计能力**，不是任意浏览私人学习记录的权限。

## 旧单用户数据迁移

升级到多用户版本时，如果原来的 `data/learning.db` 已存在学习记录：

1. 应用首先要求创建/注册账号；
2. 第一个成功注册的账号自动复制并认领旧 `learning.db`；
3. 后续新用户创建空白独立学习数据库；
4. 原始 `data/learning.db` 不会被直接删除。

因此已有单用户学习历史不会因为升级注册功能而丢失。

## 隔离范围

下列内容均按用户独立数据库保存：

- 课程阅读进度与系统成绩；
- 考试 Attempt、逐题答案、随机试卷快照；
- 倒计时草稿与自动保存状态；
- 错题本与成绩趋势；
- 代码实训提交与 pytest 成绩；
- 能力画像与自适应测试会话；
- Markdown 思考；
- 外部资料链接；
- JSON 导出、恢复前安全快照、滚动自动备份。

课程 Markdown、题库定义和代码实训题目属于应用公共内容，不属于用户私有数据。

## Docker

Docker Compose 使用一个 named volume 保存 `/data`，但 volume 内部继续按用户目录隔离：

```text
/data/accounts.db
/data/users/<storage_key>/learning.db
/data/users/<storage_key>/backups/
```

`docker compose down` 不删除账号和学习数据；`docker compose down -v` 会删除整个 named volume，包括所有用户账号和学习数据，请谨慎使用。

## 安全边界

默认仍只绑定 `127.0.0.1:8765`。如果开放到局域网：

- 建议使用 HTTPS 反向代理；
- 配置 `LLM_ALLOWED_HOSTS`；
- 建议将 `LLM_COOKIE_SECURE=1`；
- 自主注册策略优先通过超级管理员后台控制；环境变量仅用于初始默认值。

多用户登录解决的是应用内身份、受控管理权限与学习数据隔离，不替代公网部署时的 TLS、防火墙、反向代理和主机安全策略。
