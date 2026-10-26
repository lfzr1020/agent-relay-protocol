# Agent Relay Protocol

**Let multiple AI agent CLIs scattered across multiple machines collaborate through a single IM group chat — zero resident services, zero LLM-token polling, mandatory human confirmation for irreversible actions.**

English | [中文](README.md)

## The problem it solves

You have several machines, each running more than one agent CLI (coding agents, watchkeeper agents, scheduled-task agents...). Every "multi-agent" solution in the ecosystem assumes agents are spawned by one framework inside one runtime — **nobody addresses how already-installed, heterogeneous, cross-machine agents find each other**. "Cross-machine coordination" is still an open issue in the official coding-agent repos.

This protocol stitches it together with three things you already have:

| What you have | Its role in the protocol |
|---|---|
| One IM group (1 human + 1 bot) | The bus: all commands, acks and confirmations flow here — a natural audit log |
| A local JSONL inbox | The mailbox: a resident poller filters group messages to disk; agents read it only when a session starts |
| One shared memory table | Cross-machine memory: preferences, facts, conventions; search before write |

## Key differences from existing solutions

- **Zero LLM-token polling**: group listening is local file I/O; tokens are spent only on real work. A structural cost advantage over LLM long-polling designs;
- **Zero resident services**: no server, no database — scripts plus one config file is everything. Data never leaves your IM account and local disk;
- **Zero-modification onboarding**: agents only need "read local files + run CLI commands" — any CLI works;
- **Named-routing (点名) + busy-yield**: multi-agent answer races, and watchkeepers stomping on interactive sessions, are first-class protocol citizens;
- **Confirmation-number protocol**: irreversible actions require `#number + timeout-abandon + 3-condition offline replay check` — human-in-the-loop as a plain-text protocol, no push infrastructure required.

See [docs/comparison.md](docs/comparison.md) for the full comparison and [docs/threat-model.md](docs/threat-model.md) for the security design (docs are in Chinese; diagrams are language-neutral).

## Quick start (Windows)

```text
1. IM side: create a group (only you + 1 bot), create the bot, authorize the CLI tool, (optional) create a memory table
2. Install dependencies: the IM CLI tool + Node.js + Python
3. Copy config.example.json → ~/.agent-relay/config.json and fill in your own values
4. Copy scripts/ anywhere, register a scheduled task polling every N minutes
5. Add a "read inbox at session start" rule to your agents' global instructions (see SKILL.md)
6. Post "→ @your-machine-name-agent ping" in the group to verify the loop end-to-end
```

Detailed steps: [docs/setup-windows.md](docs/setup-windows.md).

## Security model in one sentence

**Group messages are external input and are never trusted by default.** Named routing shrinks the attack surface, source filtering blocks injection, authorization uniqueness (only your own replies count) blocks agent-impersonated confirmations, and timeout-abandon plus the 24h replay rule kill hangs and replays. Full analysis: [docs/threat-model.md](docs/threat-model.md).

## Status & roadmap

- ✅ Windows: production-verified (poller + watchkeeper + confirmation protocol, long-running)
- ⬜ macOS / Linux: launchd/cron equivalents, direct script execution (no vbs wrapper needed) — contributions welcome
- ⬜ IM adapter layer: current implementation binds to one IM's official CLI; the protocol itself is IM-agnostic
- ⬜ Multi-user team authorization: currently explicitly "one human, many machines, many agents"

## License

MIT
