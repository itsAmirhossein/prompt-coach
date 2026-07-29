#!/usr/bin/env python3
"""Prompt Coach — Claude Code session transcript parser.

Reads ~/.claude/projects/<munged-cwd>/<session>.jsonl and emits structured
data for the retrospective skill: each real user prompt paired with what
followed it (assistant activity, tool errors, token usage) and outcome
signals (corrections, rephrases, correction runs).

Stdlib only. Read-only: never writes anything.

Usage:
  parse_transcript.py [--cwd DIR] --list
  parse_transcript.py [--cwd DIR] --current
  parse_transcript.py [--cwd DIR] --session <id-or-path>
  parse_transcript.py [--cwd DIR] --current --last-prompt
  Options: --max-text N (truncate prompt texts in JSON output)
"""
import argparse
import json
import os
import re
import sys
import time


def munge(path):
    # Claude Code project dirs: every non-alphanumeric char becomes '-'.
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(path))


def project_dir(cwd):
    return os.path.join(os.path.expanduser("~"), ".claude", "projects", munge(cwd))


def iter_entries(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def is_real_user_prompt(entry):
    if entry.get("type") != "user":
        return False
    if entry.get("isMeta") or entry.get("isSidechain"):
        return False
    content = (entry.get("message") or {}).get("content")
    if not isinstance(content, str):
        return False  # tool_result payloads arrive as list-content user entries
    c = content.strip()
    if not c:
        return False
    for prefix in ("<command-", "<local-command-", "<system-reminder>",
                   "[Request interrupted"):
        if c.startswith(prefix):
            return False
    return True


CORRECTION_RE = re.compile(
    r"^(no[,.!\s]|no$|nope\b|wrong\b|stop\b|undo\b|revert\b"
    r"|that'?s\s+(not|wrong)|still\s|actually[,\s]"
    r"|why\s+(did|are|would)\s+you|i\s+(said|asked|meant|told)\b|don'?t\b)",
    re.I,
)
CORRECTION_CONTAINS = (
    "not what i asked", "not what i meant", "didn't ask", "didnt ask",
    "still broken", "still doesn't", "still doesnt", "still not",
    "try again", "you ignored", "as i said", "i already said",
)


def is_correction(text):
    t = " ".join(text.strip().lower().split())
    return bool(CORRECTION_RE.match(t)) or any(s in t for s in CORRECTION_CONTAINS)


def token_set(text):
    return set(re.findall(r"[a-z0-9]{2,}", text.lower()))


def analyze(path):
    prompts = []
    current = None

    def close(cur):
        if cur is not None:
            prompts.append(cur)

    for entry in iter_entries(path):
        if is_real_user_prompt(entry):
            close(current)
            current = {
                "index": len(prompts) + 1,
                "timestamp": entry.get("timestamp"),
                "uuid": entry.get("uuid"),
                "text": entry["message"]["content"].strip(),
                "assistant_turns": 0,
                "tool_calls": 0,
                "tool_errors": 0,
                "output_tokens": 0,
                "assistant_preview": "",
            }
            continue
        if current is None or entry.get("isSidechain"):
            continue
        etype = entry.get("type")
        if etype == "assistant":
            msg = entry.get("message") or {}
            usage = msg.get("usage") or {}
            current["assistant_turns"] += 1
            current["output_tokens"] += usage.get("output_tokens") or 0
            for block in (msg.get("content") or []):
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    current["tool_calls"] += 1
                elif block.get("type") == "text" and not current["assistant_preview"]:
                    current["assistant_preview"] = (block.get("text") or "").strip()[:200]
        elif etype == "user":
            content = (entry.get("message") or {}).get("content")
            if isinstance(content, list):
                for block in content:
                    if (isinstance(block, dict)
                            and block.get("type") == "tool_result"
                            and block.get("is_error")):
                        current["tool_errors"] += 1
    close(current)

    for i, p in enumerate(prompts):
        p["is_correction"] = is_correction(p["text"])
        p["is_rephrase"] = False
        if i > 0 and not p["is_correction"]:
            a, b = token_set(prompts[i - 1]["text"]), token_set(p["text"])
            if a and b and len(a & b) / len(a | b) >= 0.5:
                p["is_rephrase"] = True

    # Consecutive-correction runs; tokens spent inside a run approximate the
    # cost of recovering from whatever preceded it.
    runs, run = [], None
    for p in prompts:
        if p["is_correction"]:
            if run is None:
                run = {"start_index": p["index"], "end_index": p["index"],
                       "prompts": 0, "output_tokens": 0}
            run["prompts"] += 1
            run["end_index"] = p["index"]
            run["output_tokens"] += p["output_tokens"]
        elif run is not None:
            runs.append(run)
            run = None
    if run is not None:
        runs.append(run)

    totals = {
        "prompts": len(prompts),
        "assistant_turns": sum(p["assistant_turns"] for p in prompts),
        "tool_calls": sum(p["tool_calls"] for p in prompts),
        "tool_errors": sum(p["tool_errors"] for p in prompts),
        "output_tokens": sum(p["output_tokens"] for p in prompts),
        "corrections": sum(1 for p in prompts if p["is_correction"]),
        "rephrases": sum(1 for p in prompts if p["is_rephrase"]),
        "correction_runs": runs,
        "correction_output_tokens": sum(r["output_tokens"] for r in runs),
    }
    return {
        "path": path,
        "session": os.path.splitext(os.path.basename(path))[0],
        "totals": totals,
        "prompts": prompts,
    }


def session_files(pdir):
    try:
        files = [os.path.join(pdir, f) for f in os.listdir(pdir) if f.endswith(".jsonl")]
    except FileNotFoundError:
        return []
    files.sort(key=os.path.getmtime, reverse=True)
    return files


def list_sessions(pdir, limit=15):
    out = []
    for fp in session_files(pdir)[:limit]:
        first, count = None, 0
        for entry in iter_entries(fp):
            if is_real_user_prompt(entry):
                count += 1
                if first is None:
                    first = entry["message"]["content"].strip()[:100]
        out.append({
            "session": os.path.splitext(os.path.basename(fp))[0],
            "modified": time.strftime("%Y-%m-%d %H:%M",
                                      time.localtime(os.path.getmtime(fp))),
            "prompts": count,
            "first_prompt": first,
        })
    return out


def resolve_session(pdir, ref):
    if os.path.isfile(ref):
        return ref
    candidate = os.path.join(pdir, ref if ref.endswith(".jsonl") else ref + ".jsonl")
    if os.path.isfile(candidate):
        return candidate
    # prefix match on session id
    for fp in session_files(pdir):
        if os.path.basename(fp).startswith(ref):
            return fp
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cwd", default=os.getcwd(),
                    help="project working directory (default: current dir)")
    ap.add_argument("--list", action="store_true", help="list recent sessions")
    ap.add_argument("--current", action="store_true",
                    help="use the most recently modified session")
    ap.add_argument("--session", help="session id (or prefix, or a .jsonl path)")
    ap.add_argument("--last-prompt", action="store_true",
                    help="print only the last real user prompt as text")
    ap.add_argument("--max-text", type=int, default=0,
                    help="truncate prompt texts to N chars in JSON output")
    args = ap.parse_args()

    pdir = project_dir(args.cwd)

    if args.list:
        print(json.dumps({"project_dir": pdir, "sessions": list_sessions(pdir)},
                         indent=2))
        return 0

    if args.session:
        path = resolve_session(pdir, args.session)
    else:
        files = session_files(pdir)
        path = files[0] if files else None
    if not path:
        print(json.dumps({"error": "no session found", "project_dir": pdir}),
              file=sys.stderr)
        return 1

    result = analyze(path)

    if args.last_prompt:
        if not result["prompts"]:
            print(json.dumps({"error": "no user prompts in session"}), file=sys.stderr)
            return 1
        print(result["prompts"][-1]["text"])
        return 0

    if args.max_text > 0:
        for p in result["prompts"]:
            if len(p["text"]) > args.max_text:
                p["text"] = p["text"][:args.max_text] + " …[truncated]"

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
