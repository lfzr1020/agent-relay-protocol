#!/usr/bin/env node
// Relay group poll · inbox parser (paired with poll_task.cmd; zero LLM tokens, zero process spawning)
// Input : <relay-dir>/poll_latest.json (written to disk by the IM CLI call inside poll_task.cmd)
// Action: diff against local cursor -> append newly addressed/user messages to inbox JSONL -> count monthly API usage
// Rule  : local files only. Never auto-reply. Never execute anything. Responses happen in agent sessions.
// Usage : node group_poll.js              normal poll-cycle run
//         node group_poll.js --print <f>  print a config field and exit (used by poll_task.cmd; no side effects)

const fs = require('fs');
const path = require('path');
const os = require('os');

const RELAY_DIR = path.join(os.homedir(), '.agent-relay');
const LATEST = path.join(RELAY_DIR, 'poll_latest.json');
const STATE = path.join(RELAY_DIR, 'poll_state.json');
const INBOX = path.join(RELAY_DIR, 'inbox.jsonl');
const USAGE = path.join(RELAY_DIR, 'api_usage.json');

function readJson(f, d) { try { return JSON.parse(fs.readFileSync(f, 'utf8')); } catch (e) { return d; } }

// Config is a trusted local file at a fixed path (only the local user can write it;
// see docs/threat-model.md). Fixed constant on purpose: no env/argument can redirect it.
const CONFIG_PATH_RESOLVED = path.join(RELAY_DIR, 'config.json');

const cfg = readJson(CONFIG_PATH_RESOLVED, null);

// --print mode: side-effect-free config field dump (no usage counting, no state touching)
if (process.argv[2] === '--print') {
  const field = process.argv[3];
  if (!cfg) { console.error('[relay] config not found: ' + CONFIG_PATH_RESOLVED); process.exit(1); }
  const v = cfg[field];
  if (v === undefined || v === '') { console.error('[relay] config field empty: ' + field); process.exit(1); }
  console.log(v);
  process.exit(0);
}

if (!cfg || !cfg.machine) {
  console.error('[relay] config missing or no "machine" field: ' + CONFIG_PATH_RESOLVED + ' (see config.example.json)');
  process.exit(0); // unattended scheduled task: log and exit cleanly instead of crashing
}
const MY_MACHINE = cfg.machine;

// Monthly API usage counter (real consumption, for tuning the poll interval)
const ym = new Date().toISOString().slice(0, 7);
const usage = readJson(USAGE, {});
usage[ym] = (usage[ym] || 0) + 1;
try { fs.writeFileSync(USAGE, JSON.stringify(usage)); } catch (e) {}

const j = readJson(LATEST, null);
if (!j || !j.ok) process.exit(0);
const msgs = (j.data && j.data.messages) || [];

const st = readJson(STATE, { seen: {} });
const firstRun = Object.keys(st.seen).length === 0;
const fresh = [];

for (const m of msgs) {
  if (!m || !m.message_id || st.seen[m.message_id]) continue;
  st.seen[m.message_id] = 1;
  if (firstRun) continue; // first run only seeds the cursor; never flood the inbox with history
  if (m.msg_type === 'system' || !m.sender || !m.sender.sender_type) continue;
  let text = '';
  try { text = JSON.parse(m.content).text || ''; } catch (e) { text = String(m.content || ''); } // CLI json output content may be a plain string
  const fromUser = m.sender.sender_type === 'user';
  const isMine = !fromUser && text.startsWith('【' + MY_MACHINE); // this machine's own outbound messages: skip
  const toMe = text.includes('→ @' + MY_MACHINE);                 // addressed to this machine (incl. machine-wide broadcast)
  if (isMine) continue;
  if (toMe || fromUser) { // inbound: addressed bot messages + everything from the user (confirmations/commands)
    fresh.push({ time: m.create_time, id: m.message_id, from: fromUser ? 'user' : 'bot', text: text.slice(0, 2000) });
  }
}

// cursor keeps only the most recent 500 ids
const ids = Object.keys(st.seen);
if (ids.length > 500) for (const id of ids.slice(0, ids.length - 500)) delete st.seen[id];
try { fs.writeFileSync(STATE, JSON.stringify(st)); } catch (e) {}

if (fresh.length) {
  try { fs.appendFileSync(INBOX, fresh.map(x => JSON.stringify(x)).join('\n') + '\n'); } catch (e) {}
}
