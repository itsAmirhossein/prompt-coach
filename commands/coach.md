---
description: Toggle and configure Prompt Coach always-on mode
argument-hint: "on | off | status | config <key> <value>"
allowed-tools: Read, Write, Bash(mkdir:*), Bash(cat:*), Bash(date:*)
---

Manage the Prompt Coach always-on gate. Config file: `~/.claude/prompt-coach/config.json`. Defaults if absent:

```json
{"enabled": false, "threshold": "error", "max_triggers_per_session": 3, "bypass_prefix": "raw:",
 "loop_rescue": true, "max_loop_rescues_per_session": 1,
 "stage2": false, "stage2_command": ["claude", "--model", "haiku", "-p"]}
```

Arguments given: $ARGUMENTS

- **on** — read the config (or start from defaults), set `"enabled": true`, write it back (create `~/.claude/prompt-coach/` if needed). Confirm in one sentence and mention: it fires on at most `max_triggers_per_session` genuinely broken prompts per session, `raw:` prefix bypasses it once, `/coach off` disables it.
- **off** — set `"enabled": false`, write it back. Confirm in one sentence.
- **status** — show the current config values and whether the config file exists, in 3–4 lines. Note that the gate never blocks prompts; it only makes Claude ask one grounded clarifying question when a prompt is genuinely ambiguous, plus a loop-rescue nudge after two consecutive low-information corrections.
- **config <key> <value>** — update one of: `threshold` (`error` | `warn`), `max_triggers_per_session` (integer ≥ 0), `bypass_prefix` (short string), `loop_rescue` (`true` | `false`), `max_loop_rescues_per_session` (integer ≥ 0), `stage2` (`true` | `false` — a Haiku call verifies each stage-1 fire before it surfaces; better precision, adds seconds of latency and token cost on flagged prompts only). Validate; on an invalid key or value, list the valid ones instead of writing. Preserve all other fields (including `stage2_command`, which advanced users may edit by hand).
- **no arguments** — same as `status`.

Keep every response short — this is a settings toggle, not a conversation. Never edit files other than `~/.claude/prompt-coach/config.json`.
