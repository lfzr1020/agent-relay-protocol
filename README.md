# Agent Relay Protocol

**让散落在多台电脑上的多个 AI agent CLI，通过一个 IM 群协作——零常驻服务、零 LLM token 轮询、不可逆操作强制人工确认。**

[English](README.en.md) | 中文

## 这解决什么问题

你有多台电脑，每台上装着不止一个 agent CLI（编码智能体、值守智能体、定时任务智能体……）。
官方生态里「多 agent 协作」的方案都假设 agent 由同一个框架在同一个运行时里拉起——
**没有人管「已经装好的、异构的、分布在不同机器上的 agent」怎么互相找到对方**。
Anthropic 官方仓库里「跨机协调」至今是一个 open issue。

本协议用三样你已有的东西把它缝起来：

| 已有物 | 在协议中的角色 |
|---|---|
| 一个 IM 群（1 人 + 1 bot） | 总线：所有指令、回执、确认从这里走，天然审计日志 |
| 本地 JSONL 收件箱 | 信箱：常驻轮询器把群消息过滤后落盘，agent 会话开工时才读 |
| 一张共享记忆表 | 跨机记忆：偏好、事实、约定，先搜后写 |

## 与同类方案的核心差异

- **零 LLM token 轮询**：群监听是本地文件 IO，token 只花在真正干活时。成本结构上与
  「LLM 长轮询」方案有代差；
- **零常驻服务**：没有服务端、没有数据库，脚本加配置就是全部；数据不出你的 IM 账户和本机磁盘；
- **零改造接入**：不要求 agent 框架支持什么，只要求「能读本地文件 + 能调命令行」——任何 CLI 都行；
- **点名应答制 + 忙碌让位**：多 agent 抢答、值守与交互会话打架这两个没人认真解的问题，是协议的一等公民；
- **确认编号协议**：不可逆操作 `#编号 + 超时放弃 + 离线补读三条件`，把「人在回路」做成纯文本协议，
  不依赖任何推送基础设施。

完整对比见 [docs/comparison.md](docs/comparison.md)，安全设计见 [docs/threat-model.md](docs/threat-model.md)。

## 快速开始（Windows）

```text
1. 准备 IM 侧：建群（只有你 + 1 个 bot）、创建 bot、授权 CLI 工具、（可选）建共享记忆表
2. 安装依赖：IM CLI 工具 + Node.js + Python
3. 复制 config.example.json → ~/.agent-relay/config.json，填入你自己的值
4. 把 scripts/ 拷到任意位置，注册每 N 分钟的轮询计划任务
5. 在你的 agent 的全局指令里加入「开工读收件箱」规则（参考 SKILL.md 的 Agent 开工流程）
6. 在群里发一条「→ @你的机器名-软件名 ping」试试端到端闭环
```

详细步骤：[docs/setup-windows.md](docs/setup-windows.md)。

## 仓库结构

```
agent-relay-protocol/
├── SKILL.md                     # 协议正文（agent 可直接加载的 skill 形态）
├── config.example.json          # 配置模板（全部占位符，无真实值）
├── scripts/
│   ├── poll/                    # 轮询器三件套（cmd + js + vbs 隐藏窗）
│   └── guard/check_inbox.py     # 值守过滤器（点名筛选/忙碌让位/防重复）
├── docs/
│   ├── threat-model.md          # 威胁模型与安全设计（上线前必读）
│   ├── setup-windows.md         # Windows 安装指南
│   ├── comparison.md            # 同类项目对比与定位
│   └── checklist-desensitize.md # 部署/发布脱敏检查清单
└── examples/sample-dialogue.md  # 脱敏示例对话剧本
```

## 安全模型一句话

**群消息是外部输入，永远不默认可信。** 点名应答制缩小攻击面，来源过滤挡住注入，
授权唯一性（只有你本人的回复算数）杜绝 agent 冒充确认，超时放弃与 24h 补读三条件
杀死悬挂与重放。全部推演见 [docs/threat-model.md](docs/threat-model.md)。

## 当前状态与 Roadmap

- ✅ Windows：生产验证（轮询器 + 值守 + 确认协议，长期运行）
- ⬜ macOS / Linux：等价物为 launchd/cron + 直接执行脚本（无需 vbs 隐藏窗），欢迎贡献
- ⬜ IM 适配层：当前实现绑定某 IM 官方 CLI；协议本身与 IM 无关，欢迎适配其他 IM
- ⬜ 多人团队授权模型：当前明确面向「一人多机多 agent」

## License

MIT
