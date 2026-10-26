#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Relay group inbox filter: list unprocessed messages addressed to this machine's agent.

Usage:
  py check_inbox.py                            # busy check + list pending candidates
  py check_inbox.py --busy-window 15           # custom busy window (minutes)
  py check_inbox.py --mark-done <id> [<id>...] # mark as replied; prevents duplicate answers

Busy check: only run as the FIRST step of a watch cycle (this cycle's own turn is not
yet recorded, and the previous watch cycle was hours ago), so a recent record means an
interactive session is active on this machine -> print BUSY and stay silent.

Reads machine/agent identity from the fixed local config ~/.agent-relay/config.json.
"""
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

RELAY_DIR = Path.home() / ".agent-relay"
# Trusted local config at a fixed path (see docs/threat-model.md); no env/argument
# redirect on purpose, so the config location cannot be steered from outside.
CONFIG = RELAY_DIR / "config.json"
INBOX = RELAY_DIR / "inbox.jsonl"
STATE = RELAY_DIR / "guard_state.json"
MAX_KEEP = 500
DEFAULT_BUSY_WINDOW_MIN = 15


def load_config():
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return {}


def is_busy(cfg, window_min):
    """Pluggable busy probe. Any exception counts as busy (fail-safe: watch yields)."""
    bc = cfg.get("busy_check") or {"type": "none"}
    btype = bc.get("type", "none")
    if btype == "none":
        return False
    if btype == "zcode_turn_usage":
        # verified implementation: turns are recorded after completion, so a recent
        # max(started_at) within the window means an interactive session is live;
        # the watch cycle itself is immune (its own turn lands after this check).
        db = Path(os.path.expanduser(bc.get("db_path", "~/.zcode/cli/db/db.sqlite")))
        try:
            con = sqlite3.connect(db.as_uri() + "?mode=ro", uri=True, timeout=5)
            try:
                row = con.execute("SELECT MAX(started_at) FROM turn_usage").fetchone()
            finally:
                con.close()
            if not row or row[0] is None:
                return False
            return (time.time() * 1000 - row[0]) < window_min * 60 * 1000
        except Exception:
            return True
    return False


def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"processed_ids": []}


def save_state(st):
    st["processed_ids"] = st.get("processed_ids", [])[-MAX_KEEP:]
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cfg = load_config()
    machine = cfg.get("machine", "")
    agent_name = cfg.get("agent_name", "")
    if not machine or not agent_name:
        print(f"ERROR: config missing machine/agent_name: {CONFIG} (see config.example.json)")
        sys.exit(1)
    self_prefix = f"\u3010{machine}-{agent_name}\u3011"
    mention = f"@{machine}-{agent_name}"

    argv = sys.argv[1:]
    st = load_state()
    done = set(st.get("processed_ids", []))

    if argv and argv[0] == "--mark-done":
        done.update(a for a in argv[1:])
        st["processed_ids"] = sorted(done)
        save_state(st)
        print(f"marked done: {len(argv) - 1}")
        return

    window = DEFAULT_BUSY_WINDOW_MIN
    if "--busy-window" in argv:
        i = argv.index("--busy-window")
        if i + 1 < len(argv):
            try:
                window = float(argv[i + 1])
            except ValueError:
                pass

    if is_busy(cfg, window):
        print(f"BUSY: a session turn was active within the last {window:g} min; watch yields")
        return

    rows = []
    if INBOX.exists():
        for line in INBOX.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            mid = str(r.get("id", ""))
            text = str(r.get("text", ""))
            if not mid or mid in done:
                continue
            if mention not in text:
                continue
            if text.lstrip().startswith(self_prefix):
                continue  # this machine's own outbound message, not a pending item
            rows.append(r)

    if not rows:
        print("NO_PENDING")
        return
    for r in rows:
        print(f"--- id={r.get('id')} time={r.get('time')} from={r.get('from')}")
        print(str(r.get("text", "")))
    print(f"({len(rows)} pending; after replying successfully run: "
          f"py {Path(__file__)} --mark-done <id...>)")


if __name__ == "__main__":
    main()
