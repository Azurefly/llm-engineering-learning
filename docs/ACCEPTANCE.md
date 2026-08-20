# 当前版本验收边界 / Current Release Acceptance Boundary

本文定义 `llm-engineering-learning` 当前**多用户、本地优先**版本的完成标准。达到这些条件后，后续新增能力应视为新范围，而不是当前版本遗留优化。

## 1. 产品范围 / Product Scope

当前版本定位：

- 多用户账号注册、登录、退出；
- `superadmin` / `user` 两级账号角色；
- 超级管理员账号管理、密码重置与自主注册策略控制；
- 超级管理员全员学习进度报表与大屏；
- 每个用户学习数据物理隔离；
- 本地优先；
- Python 或 Docker 启动；
- SQLite 持久化；
- 中英文学习内容；
- 面向 LLM / RAG / Agent 工程师的 18 周学习、考试与实训系统。

Current scope:

- multi-user registration/login/logout;
- `superadmin` / `user` account roles;
- superadmin account administration, password reset, and runtime registration policy control;
- superadmin all-user learning progress reports and big-screen dashboard;
- physically isolated learning data per account;
- local first;
- Python or Docker runtime;
- SQLite persistence;
- bilingual curriculum;
- an 18-week learning, assessment, and coding-practice system for LLM/RAG/Agent engineering.

## 2. 身份、管理权限与数据隔离 / Identity, Administration & Data Isolation

验收要求：

- 未登录用户不能访问学习数据页面与写接口；
- 首次自主注册默认值可由 `LLM_ALLOW_REGISTRATION` 配置；
- 超级管理员可在后台即时开启/停止自主注册，设置持久化到 `accounts.db` 且无需重启；
- 关闭自主注册后 `/register` 必须返回 403，但已有账号仍可登录，超级管理员仍可手工创建账号；
- 用户名唯一；
- 密码不得明文存储；
- Session 使用随机 Token，浏览器 Cookie 必须 `HttpOnly` + `SameSite=Lax`；
- 全新系统第一个注册账号自动成为 `superadmin`；
- 旧多用户账号库若不存在超级管理员，升级后最早账号自动获得 `superadmin`；
- 普通 `user` 访问 `/admin/users`、`/admin/report`、`/admin/report/data` 和单用户管理员进度页必须返回 403；
- 超级管理员可创建账号、修改用户名/显示名、启停账号、管理角色、重置其他用户密码；
- 密码重置与账号停用必须立即撤销目标用户现有 Session；
- 当前超级管理员不能停用或降低自己的角色，系统必须始终保留至少一个启用的超级管理员；
- 所有用户可在 `/account` 修改自己的账号信息和密码；自助改密后必须注销全部现有 Session；
- `accounts.db` 与学习数据分离；
- 每个用户使用独立 `users/<storage_key>/learning.db`；
- 超级管理员允许跨用户**只读汇总学习进度、考试与代码实训统计**；
- 管理报表不得输出 `password_hash`、`storage_key`、数据库路径、个人思考笔记、外链正文或代码源文件；
- 除上述管理员统计白名单外，不同用户的学习数据、私人知识记录和备份互不可见；
- 第一个注册用户必须能够自动继承旧版单用户 `data/learning.db`；
- 后续新用户必须从空白独立数据库开始。

## 3. 学习闭环 / Learning Loop

验收要求：

```text
课程阅读
→ 系统考试
→ 自动评分
→ 能力画像
→ 薄弱知识点
→ 自适应复习 / CAT
→ 再评分
→ 能力趋势
```

同时支持：

- Markdown 思考记录；
- 外部学习链接；
- 全局搜索；
- Week 2～18 每周代码实训；
- 错题本与阶段考试。

## 4. 评分可信性 / Grading Integrity

当前版本必须满足：

- 分数禁止手工填写；
- 客观题确定性评分；
- 简答题使用透明 Rubric；
- 英文缩写采用术语边界匹配，避免子串误判；
- 代码题使用 pytest 系统评分；
- 历史试卷冻结完整题目快照；
- CAT 同一作答只计算一次曝光。

## 5. 题库 / Question Bank

当前验收基线：

- Week 0～18 全覆盖；
- 约 190+ 题；
- 每周至少 9 题；
- 包含基础、理解、工程场景、排障/治理、设计类题目；
- 中英文题干完整；
- Question ID 唯一；
- 答案、选项、填空 accepted answers、简答 Rubric 自动校验；
- CI 题库质量门禁必须通过。

继续扩充到数千题属于内容规模扩展，不是当前版本缺陷。

## 6. 代码实训 / Coding Labs

当前验收基线：

- Week 2～18 每周至少一个代码实训；
- Starter 与测试代码可编译；
- 中英文题意完整；
- 默认不执行任意用户代码；
- 显式启用 Docker Runner 后使用隔离容器；
- 无网络、资源限制、非 root、只读题目工作区、能力移除；
- CI 必须真实构建沙箱并完成 pytest 自动评分 Smoke Test。

## 7. 管理报表 / Administration Reporting

超级管理员报表验收基线：

- `/admin/report` 提供可全屏展示的大屏报表；
- 默认展示注册用户数、启用用户数、已开始学习人数、近 7 天活跃人数、平均总进度；
- 展示 Week 0～18 每周平均进度、开始人数、完成人数；
- 展示系统考试次数/通过率和代码实训次数/通过率；
- 展示用户总体进度分布；
- 展示每个用户的总进度、完成课程数、当前周、考试表现、代码实训表现和最近活动；
- `/admin/users/<id>/progress` 提供逐用户 Week 0～18 进度详情；
- `/admin/report/data` 提供同一统计模型的 JSON 数据；
- 大屏不得读取/展示 `thoughts`、资源正文、代码源文件或认证敏感字段；
- 大屏与管理员详情页必须设置 `Cache-Control: no-store`。

## 8. 数据可靠性 / Data Reliability

当前验收基线：

- SQLite WAL；
- busy timeout；
- 外键开启；
- Python 模式本地 `data/` 不进入 Git；
- Docker 使用 permission-safe named volume；
- Docker 容器重启后账号、Session、系统注册策略与学习数据仍存在；
- 每个用户独立 JSON 导出；
- 每个用户独立恢复前安全快照与滚动自动备份；
- 备份不包含其他用户和认证账号数据；
- 备份格式校验；
- 恢复前显式确认；
- 事务恢复与失败回滚。

## 9. 本地安全边界 / Local Security Boundary

当前验收基线：

- 默认只监听/发布 localhost；
- Trusted Host；
- 跨站写请求阻断；
- Markdown HTML 清洗；
- 外链仅 HTTP(S)；
- 恢复数据同样执行 URL 与关键范围校验；
- 安全响应头；
- 密码使用带随机 Salt 的强哈希；
- Session Token 数据库只保存摘要；
- 超级管理员路由必须进行服务端角色校验，而非只隐藏菜单；
- 管理员重置密码/停用账号必须撤销目标 Session；
- 管理员报表只可读取明确白名单的进度统计字段；
- 管理员页面和 JSON 不得缓存；
- Docker `cap_drop: ALL`；
- Docker `no-new-privileges`；
- 代码执行默认关闭。

## 10. 可维护性 / Maintainability

当前验收基线：

- 稳定入口 `app.current:app`；
- 历史 `main_v*.py` 不参与正式启动链；
- 用户数据库 schema 可在登录后自动创建/升级；
- `accounts.db` 可自动迁移 `role` 字段和超级管理员；
- 系统运行时设置使用独立 `system_settings` 表；
- 管理报表逻辑集中在独立模块，不直接复用私人内容查询；
- 已验证直接依赖固定版本；
- Dependabot 定期提出升级；
- 系统诊断页面与 API；
- README / APP / MULTI_USER / ADMIN / V5 中英文说明与真实行为一致。

## 11. CI 发布门禁 / CI Release Gate

`main` 应同时通过：

1. Ubuntu + Python 3.11 完整 pytest；
2. Ubuntu + Python 3.12 完整 pytest；
3. Windows + Python 3.12 完整 pytest；
4. 注册、错误密码、Session 测试；
5. 两用户物理数据库隔离测试；
6. 首用户旧单用户数据迁移测试；
7. 首账号超级管理员、旧账号库角色迁移测试；
8. 普通用户访问超级管理员接口 403 测试；
9. 管理员修改注册信息、启停账号、角色保护、密码重置与 Session 撤销测试；
10. 用户自助改密与 Session 撤销测试；
11. 管理员跨用户学习进度汇总、逐用户进度详情测试；
12. 管理报表认证字段/私人笔记/代码源文件不泄露测试；
13. 管理员即时停止/恢复自主注册测试；
14. 真实 Docker Coding Sandbox Smoke Test；
15. 完整 Docker Compose Smoke Test，包括首个超级管理员、大屏、普通用户 403、用户隔离、注册策略切换、SQLite 写入、容器重启、Session 与用户数据持久化验证；
16. `pip check` 依赖一致性验证。

任何一项失败，都不应视为当前版本完成。

## 12. 明确属于新范围的能力 / Explicit Future Scope

以下能力如果未来需要，应作为新需求单独设计：

- 组织 / 租户层级；
- 超出 `superadmin/user` 两级模型的细粒度 RBAC；
- 用户硬删除、数据保留期限与审计审批工作流；
- 邮箱验证、找回密码邮件、OAuth/OIDC/企业 SSO；
- 云端同步和多设备实时协作；
- LMS/SCORM/xAPI 等教育平台标准集成；
- 原生 iOS / Android 客户端；
- 在线远程多租户代码判题集群；
- 使用外部大模型作为主观题裁判；
- 基于大规模真实考生数据的 IRT/心理测量标定；
- 教师端题库编辑、班级、作业和运营后台。

这些都是有效的产品扩展方向，但不属于当前“多用户、本地优先、工程学习系统”的基础完成条件。

## 完成定义 / Definition of Done

当本文件第 2～11 节全部满足，并且最新 `main` CI 全绿时，当前产品范围内可视为完成；之后的工作应以新需求、新课程内容或新部署范围立项。
