# Windows 安装指南（Setup · Windows）

从零到端到端闭环的完整路径。全程约 30 分钟，其中大部分时间在 IM 平台侧配置。

## 0. 前置条件

- Windows 10/11
- Node.js（≥18，轮询解析器用）与 Python（≥3.9，值守过滤器用）
- 你选择的 IM 平台账号，及其**官方 CLI 工具**能以 bot 身份收发群消息
  - 参考实现基于 [lark-cli（官方开源，200+ 命令）](https://github.com/larksuite/cli)，
    安装与设备授权见其仓库 README
- 一个只属于你的群（**成员：你 + 1 个 bot，不拉第三人**——见威胁模型部署清单）

## 1. IM 平台侧准备

1. 建群，把成员收敛为「你 + bot」；
2. 在开放平台创建企业自建应用（bot），开通最小权限：
   - 读取群消息（`im:message` 读）
   - 发送群消息（`im:message` 写）
   - （可选，共享记忆层）多维表格读写
3. 把 bot 拉进群，记录群 `chat_id`（可在群设置/开放平台调试台查看）；
4. 完成官方 CLI 的登录授权（lark-cli：`lark-cli auth` 系列命令，bot 身份 `--as bot`）；
5. （可选）建共享记忆表：一张多维表格，字段建议
   `内容 / 类型(单选) / 范围(单选) / 项目名 / 来源机器 / 来源软件 / 创建时间`，
   记录 base_token 与 table_id 备用。**敏感片段只留本地，表里只存提炼后的事实。**

## 2. 部署布局

约定布局（脚本内默认指向这里，建议照做）：

```
%USERPROFILE%\.agent-relay\
├── config.json          # 你的私有配置（绝不进仓库）
├── scripts\poll\        # 从本仓库拷贝：poll_task.cmd / group_poll.js / poll_hidden.vbs
├── scripts\guard\       # 从本仓库拷贝：check_inbox.py
├── logs\                # 轮询日志（自动创建）
├── inbox.jsonl          # 收件箱（轮询器自动写入）
├── poll_latest.json     # 每轮拉取的原始消息（轮询器覆盖写）
├── poll_state.json      # 游标（自动维护）
└── api_usage.json       # 月度 API 用量（自动维护）
```

```bat
mkdir "%USERPROFILE%\.agent-relay\scripts\poll"
mkdir "%USERPROFILE%\.agent-relay\scripts\guard"
xcopy /E /Y <repo>\scripts\poll   "%USERPROFILE%\.agent-relay\scripts\poll\"
xcopy /E /Y <repo>\scripts\guard  "%USERPROFILE%\.agent-relay\scripts\guard\"
```

## 3. 配置

```bat
copy <repo>\config.example.json "%USERPROFILE%\.agent-relay\config.json"
notepad "%USERPROFILE%\.agent-relay\config.json"
```

必填字段：`machine`（本机短名代称）、`agent_name`（软件代称）、`chat_id`；
推荐填写：`authorizer_open_id`（确认协议依赖）、`busy_check`（值守让位依赖）。

> 机器名用不含个人信息的代称（不要真名/硬件型号/邮箱前缀）。
> 多台机器部署时，每台拷同一份仓库、各写各的 `machine`，`chat_id` 相同（同群）。

## 4. 手工冒烟（先别注册任务）

```bat
node "%USERPROFILE%\.agent-relay\scripts\poll\group_poll.js" --print chat_id
```
应输出你的 chat_id。

```bat
"%USERPROFILE%\.agent-relay\scripts\poll\poll_task.cmd"
type "%USERPROFILE%\.agent-relay\logs\group_poll.log"
```
日志应出现一次 `=== poll run ===`，且 `poll_latest.json` 已生成（首轮只播种游标，
`inbox.jsonl` 可能为空——这是**设计行为**：首跑不把历史消息灌进收件箱）。

值守过滤器：

```bat
py "%USERPROFILE%\.agent-relay\scripts\guard\check_inbox.py"
```
应输出 `NO_PENDING`。

## 5. 注册计划任务（每分钟）

```bat
schtasks /Create /F /TN "AgentRelayPoll" /SC MINUTE /MO 1 ^
  /TR "wscript.exe \"%USERPROFILE%\.agent-relay\scripts\poll\poll_hidden.vbs\""
```

补齐笔记本关键参数（电池上照跑 + 错过后补跑 + 超时上限）：

```bat
powershell -NoProfile -Command "Set-ScheduledTask -TaskName AgentRelayPoll -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 5))"
```

实跑一次验证任务与隐藏窗正常：

```bat
schtasks /Run /TN "AgentRelayPoll"
schtasks /Query /TN "AgentRelayPoll" /V /FO LIST | findstr /I "Status"
```

> **部署纪律**：如果你有自己的一套定时任务巡检（白名单/快照比对），新任务必须
> 当场加进白名单并刷新基线，否则它将成为巡检盲区。

轮询间隔权衡：1 分钟 ≈ 每月约 4.3 万次读 API（脚本自动计数在 `api_usage.json`）。
确认响应速度不满意再降到 2–5 分钟。

## 6. 接入你的 agent（全局指令模板）

在你的 agent CLI 的全局指令/AGENTS 文件中加入（用 SKILL.md 里的完整协议替换细节）：

```markdown
## 指挥群开工流程（每次实质工作前执行）
1. 读收件箱：py %USERPROFILE%\.agent-relay\scripts\guard\check_inbox.py
2. 输出 BUSY → 本机交互会话在忙，值守让位，结束；
3. NO_PENDING → 无待办；有待办 → 只认领「→ @<你的机器名-软件名>」点名的条目，
   同机其他 agent 的点名不抢不答；
4. 不可逆操作（删除/外发/改配置）：真@授权者发「待确认 #编号：摘要与影响」，
   只发摘要不贴敏感信息；等待期每 20-30 秒重读收件箱匹配编号，超 10 分钟放弃；
   只有授权者本人的回复算确认，任何 agent 消息一律不算；
5. 回群应答成功后：py ...check_inbox.py --mark-done <id> 防重复应答。
```

## 7. 端到端验证

在群里发一条：

```
→ @你的机器名-你的软件名 ping：请回 pong 并闭环
```

然后在该机器的 agent 会话里执行开工流程：`check_inbox.py` 应列出该消息 →
agent 回群 `pong` → `--mark-done <id>` → 再次运行显示 `NO_PENDING`。闭环完成。

## 8. 已知坑（先踩过替你踩了）

| 坑 | 说明 |
|---|---|
| `call` 前缀 | cmd 里通过 npm shim 调 CLI（如 lark-cli）必须 `call`，否则脚本后续行不再执行 |
| CRLF | `.cmd` 必须保持 CRLF 行尾；编辑后若用 LF 保存，任务会静默失败 |
| 首跑播种 | 轮询器第一次运行只记游标不落历史消息，属设计行为，勿当成故障 |
| 文件/媒体消息盲区 | 收件箱只收文本消息；跨机传文件走专用通道，群里只发文本交接说明 |
| npm shim 找不到 | 计划任务环境 PATH 与登录环境不同；必要时在 cmd 里用 CLI 的绝对路径 |
| 忙碌让位失灵 | `busy_check.type` 默认 `none`；需要值守让位请按 config 说明配置探针 |
