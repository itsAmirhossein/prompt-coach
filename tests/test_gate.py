#!/usr/bin/env python3
"""Deterministic tests for hooks/gate.py — run: python3 tests/test_gate.py

No dependencies. Tests analyze() directly, then the full hook end-to-end
via subprocess with PROMPT_COACH_HOME pointed at a temp dir. Covers v0.2:
loop rescue and the stage-2 verifier.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(ROOT, "hooks", "gate.py")
sys.path.insert(0, os.path.join(ROOT, "hooks"))
import gate  # noqa: E402

failures = []


def check(name, condition, detail=""):
    if condition:
        print("PASS  %s" % name)
    else:
        print("FAIL  %s  %s" % (name, detail))
        failures.append(name)


# ---------- analyze(): should fire ----------
FIRE = [
    ("fix it", {"CLR01"}),
    ("Fix this", {"CLR01"}),
    ("make it better", {"CLR01"}),
    ("make it work", {"CLR01"}),
    ("please fix it so it works", {"CLR01"}),
    ("the login page doesn't work", {"CTX01"}),
    ("it's broken", {"CTX01"}),
    ("checkout is still failing after your change", {"CTX01"}),
    ("IMPORTANT: you MUST validate inputs. NEVER skip this.", {"MOD02"}),
    ("Write the complete file, do not be lazy", {"MOD05"}),
]
for prompt, expected in FIRE:
    got = {rule for rule, _tier, _msg in gate.analyze(prompt)}
    check("fire: %r -> %s" % (prompt, sorted(expected)),
          expected <= got, "got %s" % sorted(got))

# ---------- analyze(): must NOT fire (false-positive control) ----------
QUIET = [
    "fix the race condition in src/db/pool.py line 112",
    "fix the `parse_args` helper, it returns None for empty input",
    "The tests in test_pool.py don't work under xdist — error: TimeoutError at line 40",
    "Improve this function: `def f(x): return x + 1`",
    "Rename getUserData to fetchUserProfile across src/ and update all call sites",
    "Why doesn't the GIL prevent this data race in CPython?",
    "IMPORTANT: the migration must be reversible",   # single caps token — below MOD02 bar
    "Add a --verbose flag to scripts/deploy.sh and document it in README.md",
]
for prompt in QUIET:
    got = gate.analyze(prompt)
    check("quiet: %r" % prompt[:60], got == [], "got %s" % got)


# ---------- helpers ----------
def run_gate(home, payload):
    env = dict(os.environ, PROMPT_COACH_HOME=home)
    proc = subprocess.run(
        [sys.executable, GATE], input=json.dumps(payload),
        capture_output=True, text=True, env=env, timeout=30)
    return proc


def write_config(home, **overrides):
    cfg = {"enabled": True, "threshold": "error",
           "max_triggers_per_session": 3, "bypass_prefix": "raw:"}
    cfg.update(overrides)
    with open(os.path.join(home, "config.json"), "w") as f:
        json.dump(cfg, f)


def make_transcript(path, prompts):
    """Minimal but schema-faithful transcript: alternating user/assistant."""
    with open(path, "w") as f:
        for i, text in enumerate(prompts):
            f.write(json.dumps({
                "type": "user", "uuid": "u%d" % i,
                "timestamp": "2026-07-28T00:00:%02dZ" % i,
                "message": {"role": "user", "content": text},
            }) + "\n")
            f.write(json.dumps({
                "type": "assistant",
                "message": {"role": "assistant", "usage": {"output_tokens": 10},
                            "content": [{"type": "text", "text": "ok"}]},
            }) + "\n")


# ---------- e2e: lint path ----------
with tempfile.TemporaryDirectory() as home:
    write_config(home)
    payload = {"session_id": "t-e2e", "hook_event_name": "UserPromptSubmit",
               "prompt": "fix it"}

    p = run_gate(home, payload)
    out = json.loads(p.stdout)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    check("e2e: fires on 'fix it'",
          p.returncode == 0
          and out["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
          and "CLR01" in ctx and "AskUserQuestion" in ctx,
          "stdout=%r" % p.stdout[:200])

    p = run_gate(home, dict(payload, prompt="raw: fix it"))
    check("e2e: bypass prefix silences", p.stdout.strip() == "", repr(p.stdout))

    p = run_gate(home, dict(payload, prompt="/retro --current"))
    check("e2e: slash command silences", p.stdout.strip() == "", repr(p.stdout))

    p = run_gate(home, dict(payload,
                            prompt="IMPORTANT: you MUST ALWAYS validate inputs"))
    check("e2e: warn-tier silent at error threshold",
          p.stdout.strip() == "", repr(p.stdout))

    # cap: fired once above already; two more fire, the fourth is capped
    fired = [run_gate(home, dict(payload, prompt="fix this")).stdout.strip()
             for _ in range(3)]
    check("e2e: session cap of 3",
          fired[0] != "" and fired[1] != "" and fired[2] == "",
          repr(fired))

with tempfile.TemporaryDirectory() as home:
    write_config(home, enabled=False)
    p = run_gate(home, {"session_id": "t-off",
                        "hook_event_name": "UserPromptSubmit", "prompt": "fix it"})
    check("e2e: disabled config is silent", p.stdout.strip() == "", repr(p.stdout))

with tempfile.TemporaryDirectory() as home:
    # no config file at all -> defaults -> disabled
    p = run_gate(home, {"session_id": "t-noconf",
                        "hook_event_name": "UserPromptSubmit", "prompt": "fix it"})
    check("e2e: no config file is silent (disabled by default)",
          p.stdout.strip() == "", repr(p.stdout))

with tempfile.TemporaryDirectory() as home:
    write_config(home, threshold="warn")
    p = run_gate(home, {"session_id": "t-warn",
                        "hook_event_name": "UserPromptSubmit",
                        "prompt": "IMPORTANT: you MUST ALWAYS validate inputs"})
    check("e2e: warn threshold fires MOD02",
          "MOD02" in p.stdout, repr(p.stdout[:200]))

# malformed stdin must fail open (exit 0, no output)
proc = subprocess.run([sys.executable, GATE], input="not json{{{",
                      capture_output=True, text=True,
                      env=dict(os.environ, PROMPT_COACH_HOME="/nonexistent-pc"),
                      timeout=30)
check("e2e: malformed stdin fails open",
      proc.returncode == 0 and proc.stdout.strip() == "",
      "rc=%s out=%r" % (proc.returncode, proc.stdout))


# ---------- e2e: loop rescue ----------
with tempfile.TemporaryDirectory() as home:
    write_config(home)
    tpath = os.path.join(home, "transcript.jsonl")
    make_transcript(tpath, [
        "add pagination to the users endpoint in api/users.ts",
        "no, still wrong. try again",
    ])
    payload = {"session_id": "t-rescue", "hook_event_name": "UserPromptSubmit",
               "prompt": "still broken", "transcript_path": tpath}

    p = run_gate(home, payload)
    check("rescue: fires on 2nd consecutive low-info correction",
          "loop rescue" in p.stdout and "/clear" in p.stdout,
          repr(p.stdout[:200]))

    p = run_gate(home, payload)
    check("rescue: capped at 1 per session (and no lint fallback)",
          p.stdout.strip() == "", repr(p.stdout))

with tempfile.TemporaryDirectory() as home:
    write_config(home)
    tpath = os.path.join(home, "transcript.jsonl")
    make_transcript(tpath, [
        "add pagination to the users endpoint in api/users.ts",
    ])
    p = run_gate(home, {"session_id": "t-norescue", "prompt": "still broken",
                        "hook_event_name": "UserPromptSubmit",
                        "transcript_path": tpath})
    check("rescue: prev non-correction falls through to lint (CTX01)",
          "CTX01" in p.stdout and "loop rescue" not in p.stdout,
          repr(p.stdout[:200]))

with tempfile.TemporaryDirectory() as home:
    write_config(home, loop_rescue=False)
    tpath = os.path.join(home, "transcript.jsonl")
    make_transcript(tpath, ["do the thing in api/users.ts", "no, still wrong. try again"])
    p = run_gate(home, {"session_id": "t-rescueoff", "prompt": "still broken",
                        "hook_event_name": "UserPromptSubmit",
                        "transcript_path": tpath})
    check("rescue: disabled -> lint path instead",
          "CTX01" in p.stdout and "loop rescue" not in p.stdout,
          repr(p.stdout[:200]))

with tempfile.TemporaryDirectory() as home:
    write_config(home)
    tpath = os.path.join(home, "transcript.jsonl")
    make_transcript(tpath, ["add pagination", "no, still wrong. try again"])
    # informative correction: concrete referent -> not rescue-eligible, and
    # concrete + no BROKEN match -> lint quiet too
    p = run_gate(home, {"session_id": "t-inforescue", "hook_event_name": "UserPromptSubmit",
                        "prompt": "no — the modal still flashes; check the effect ordering in Modal.tsx",
                        "transcript_path": tpath})
    check("rescue: informative correction stays silent",
          p.stdout.strip() == "", repr(p.stdout))


# ---------- e2e: stage 2 ----------
with tempfile.TemporaryDirectory() as home:
    write_config(home, stage2=True, stage2_command=["/bin/sh", "-c", "echo VETO"])
    p = run_gate(home, {"session_id": "t-s2v", "hook_event_name": "UserPromptSubmit",
                        "prompt": "fix it"})
    check("stage2: VETO silences a stage-1 fire", p.stdout.strip() == "", repr(p.stdout))

with tempfile.TemporaryDirectory() as home:
    write_config(home, stage2=True, stage2_command=["/bin/sh", "-c", "echo CONFIRM"])
    p = run_gate(home, {"session_id": "t-s2c", "hook_event_name": "UserPromptSubmit",
                        "prompt": "fix it"})
    check("stage2: CONFIRM lets the fire through", "CLR01" in p.stdout,
          repr(p.stdout[:200]))

with tempfile.TemporaryDirectory() as home:
    write_config(home, stage2=True, stage2_command=["/nonexistent-bin-xyz"])
    p = run_gate(home, {"session_id": "t-s2b", "hook_event_name": "UserPromptSubmit",
                        "prompt": "fix it"})
    check("stage2: broken command fails open to stage-1 verdict",
          "CLR01" in p.stdout, repr(p.stdout[:200]))

print()
if failures:
    print("%d FAILED: %s" % (len(failures), ", ".join(failures)))
    sys.exit(1)
print("all tests passed")
