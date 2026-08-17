# 当前版本验收边界 / Current Release Acceptance Boundary

本文定义 `llm-engineering-learning` 当前单用户、本地优先版本的完成标准。达到这些条件后，后续新增能力应视为**新范围 / 新产品需求**，而不是当前版本遗留优化。

## 1. 产品范围 / Product Scope

当前版本定位：

- 单用户；
- 本地优先；
- Python 或 Docker 启动；
- SQLite 持久化；
- 中英文学习内容；
- 面向 LLM / RAG / Agent 工程师的 18 周学习、考试与实训系统。

Current scope:

- single user;
- local first;
- Python or Docker runtime;
- SQLite persistence;
- bilingual curriculum;
- an 18-week learning, assessment, and coding-practice system for LLM/RAG/Agent engineering.

## 2. 学习闭环 / Learning Loop

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

## 3. 评分可信性 / Grading Integrity

当前版本必须满足：

- 分数禁止手工填写；
- 客观题确定性评分；
- 简答题使用透明 Rubric；
- 英文缩写采用术语边界匹配，避免子串误判；
- 代码题使用 pytest 系统评分；
- 历史试卷冻结完整题目快照；
- CAT 同一作答只计算一次曝光。

## 4. 题库 / Question Bank

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

## 5. 代码实训 / Coding Labs

当前验收基线：

- Week 2～18 每周至少一个代码实训；
- Starter 与测试代码可编译；
- 中英文题意完整；
- 默认不执行任意用户代码；
- 显式启用 Docker Runner 后使用隔离容器；
- 无网络、资源限制、非 root、只读题目工作区、能力移除；
- CI 必须真实构建沙箱并完成 pytest 自动评分 Smoke Test。

## 6. 数据可靠性 / Data Reliability

当前验收基线：

- SQLite WAL；
- busy timeout；
- 外键开启；
- Python 模式本地 `data/` 不进入 Git；
- Docker 使用 permission-safe named volume；
- Docker 容器重启后学习数据仍存在；
- 完整 JSON 导出；
- 备份格式校验；
- 恢复前显式确认；
- 恢复前安全快照；
- 事务恢复与失败回滚；
- 启动滚动自动备份。

## 7. 本地安全边界 / Local Security Boundary

当前验收基线：

- 默认只监听/发布 localhost；
- Trusted Host；
- 跨站写请求阻断；
- Markdown HTML 清洗；
- 外链仅 HTTP(S)；
- 恢复数据同样执行 URL 与关键范围校验；
- 安全响应头；
- Docker `cap_drop: ALL`；
- Docker `no-new-privileges`；
- 代码执行默认关闭。

## 8. 可维护性 / Maintainability

当前验收基线：

- 稳定入口 `app.current:app`；
- 历史 `main_v*.py` 不参与正式启动链；
- 已验证直接依赖固定版本；
- Dependabot 定期提出升级；
- 系统诊断页面与 API；
- README / APP / V5 中英文说明与真实行为一致。

## 9. CI 发布门禁 / CI Release Gate

`main` 应同时通过：

1. Ubuntu + Python 3.11 完整 pytest；
2. Ubuntu + Python 3.12 完整 pytest；
3. Windows + Python 3.12 完整 pytest；
4. 真实 Docker Coding Sandbox Smoke Test；
5. 完整 Docker Compose Smoke Test，包括：启动、主要页面、诊断、SQLite 写入、容器重启、数据持久化验证；
6. `pip check` 依赖一致性验证。

任何一项失败，都不应视为当前版本完成。

## 10. 明确属于新范围的能力 / Explicit Future Scope

以下能力如果未来需要，应作为新需求单独设计，不应被解释为当前版本“尚未优化完”：

- 多用户、组织、角色和权限系统；
- 公网账号登录与身份认证；
- 云端同步和多设备实时协作；
- LMS/SCORM/xAPI 等教育平台标准集成；
- 原生 iOS / Android 客户端；
- 在线远程多租户代码判题集群；
- 使用外部大模型作为主观题裁判；
- 基于大规模真实考生数据的 IRT/心理测量标定；
- 教师端题库编辑、班级、作业和运营后台。

这些都是有效的产品扩展方向，但会改变当前“个人、本地、工程学习工具”的产品边界。

## 完成定义 / Definition of Done

当本文件第 2～9 节全部满足，并且最新 `main` CI 全绿时，当前产品范围内不再保留已知的高价值优化项；之后的工作应以新需求、新课程内容或新部署范围立项。
