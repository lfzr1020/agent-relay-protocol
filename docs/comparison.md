# 同类项目对比与定位（Comparison · 2026-10 调研）

回答一个问题：这个协议在已有生态里站在哪，为什么还值得存在。

## 格局四层

### 1) 平台产品化：IM 官方亲自做 agent 群聊
- [Slack Code agent channels](https://slack.com/blog/news/slack-code-channels-for-agents)：
  Slack 官方把「人 + agent 混合群聊」做成产品，口号 human set direction, agents close the loop。
  **方向与本协议完全一致——需求真实性由大厂背书**；但绑定 Slack 平台与其 agent 生态。
- 官方编码智能体仓库中「跨机协调」至今是 open 功能请求（如
  [anthropics/claude-code#28300](https://github.com/anthropics/claude-code/issues/28300)）。
  **原生方案缺位 = 本协议的窗口期。**

### 2) 框架内多 agent：解决不了「已装好的异构 CLI」
[CrewAI](https://github.com/crewAIInc/crewAI)、AutoGen、
[aws-samples/sample-claude-code-agent-team](https://github.com/aws-samples/sample-claude-code-agent-team)
等：agent 都由同一框架在**同一运行时**拉起，共享框架的通信原语。
它们无法纳管「用户多年前就装好的、彼此独立的、分布在不同机器上的 agent CLI」——
而这恰是绝大多数个人用户的真实存量。

### 3) 托管/跨机平台：能力重叠最大，形态最重
- [Omnara](https://github.com/omnara-ai/omnara)：开源托管 agent 平台（YC 背景），
  统一 API 在任意机器跑 agent，手机实时监控 + 推送 Approve/Deny。
  人工确认、多机、监控三点都覆盖——**但需要自托管服务端**，审批与监控依赖平台在线。
- [claude-code-by-agents](https://github.com/baryhuang/claude-code-by-agents)：
  macOS + iOS 原生 app 协调本地/远程编码 agent 实例。形态是 app，不是可移植协议。

### 4) 记忆层：定位互补而非竞争
[mem0](https://github.com/mem0ai/mem0)、[Letta](https://github.com/letta-ai/letta)：
面向语义检索的向量记忆服务。本协议的共享记忆表是**结构化事实**（类型/范围/来源机器），
人工可直接打开阅读编辑，先搜后写、更新优于新增。两者可以并存（记忆层换 mem0 不影响协议）。

## 本协议的差异化（调研时点上未见同类做出）

| 能力 | 本协议 | 平台类（Omnara 等） | 框架类（CrewAI 等） |
|---|---|---|---|
| 纳管存量异构 agent CLI | ✅ 唯一前提：能读文件+调命令行 | 部分（需接其 API） | ❌ 须由框架拉起 |
| 常驻服务端 | ❌ 无 | ✅ 需自托管 | ❌ 无 |
| 群监听成本 | **零 LLM token**（本地文件 IO） | 平台侧 | 框架侧 |
| 多 agent 抢答治理 | ✅ 点名应答制（协议级） | 平台路由 | 框架内编排 |
| 值守与交互会话冲突 | ✅ 忙碌让位（本地检测） | — | — |
| 不可逆操作人工确认 | ✅ 纯文本 `#编号` 协议 + 超时放弃 + 离线补读三条件 | ✅ 推送审批（体验更好） | 框架 gate |
| 审计 | 群聊即审计日志 | 平台日志 | — |
| 数据主权 | 个人 IM 账户 + 本地磁盘 | 自托管平台 | 本地 |
| IM 锁定 | 单 IM（当前实现），协议本身 IM 无关 | 平台独立 | 无关 |

一句话定位：**平台类给你一台服务，框架类给你一个笼子，本协议给你一套交通规则——
已有的车（agent CLI）、已有的路（IM 群），直接上路。**

## 诚实的不如人处

1. **无 UI**：没有仪表盘/手机 App 体验，监控靠群聊记录与本地日志；
2. **确认延迟**：审批到达速度受轮询间隔限制（推送类方案秒级到达）；
3. **IM 单一实现**：当前绑定一个官方 CLI，其他 IM 需要适配层贡献；
4. **单用户模型**：多人团队授权未设计，不要拿去做团队共享总线；
5. **无服务端 = 无全局视图**：没有「所有机器状态汇总」的地方，状态散在各机收件箱。
