#!/usr/bin/env python3
"""Prompt Coach — UserPromptSubmit gate (v0.2).

Stage 1 (deterministic lint) + loop rescue (mid-session coaching) +
optional stage-2 verifier (a model call that can veto a stage-1 fire).

Design contract (see DESIGN.md §2):
- Fail open: any internal error exits 0 with no output.
- Never blocks a prompt. The only effect is injecting additionalContext.
- Silent on the overwhelming majority of prompts; per-session caps.
- Zero model calls unless stage2 is explicitly enabled in config.

State lives under ~/.claude/prompt-coach/ (override with $PROMPT_COACH_HOME,
used by tests). Disabled by default until the user runs /coach on.
"""
import json
import os
import re
import subprocess
import sys

DEFAULT_CONFIG = {
    "enabled": False,
    "threshold": "error",            # "error" fires only error-tier rules; "warn" adds warn-tier
    "max_triggers_per_session": 3,
    "bypass_prefix": "raw:",
    "loop_rescue": True,             # detect 2 consecutive low-information corrections
    "max_loop_rescues_per_session": 1,
    "stage2": False,                 # model verifier for stage-1 lint fires (adds latency + cost)
    "stage2_command": ["claude", "--model", "haiku", "-p"],
}


def coach_home():
    return os.environ.get("PROMPT_COACH_HOME") or os.path.join(
        os.path.expanduser("~"), ".claude", "prompt-coach")


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(os.path.join(coach_home(), "config.json"), encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            cfg.update(loaded)
    except Exception:
        pass
    return cfg


# ---------------------------------------------------------------- lint rules

# A prompt that names something concrete (path, symbol, code, URL, quote,
# line number) is grounded enough that the referent rules must not fire.
CONCRETE_RE = re.compile(
    r"""(
        /[\w.\-]+                                            # path segment
      | `[^`]+`                                              # backtick code
      | \b[\w\-]+\.(py|ts|tsx|js|jsx|mjs|md|json|yaml|yml|toml|swift|kt|kts|java|go|rs|rb|c|h|hpp|cpp|cs|sh|zsh|sql|css|scss|html|xml|txt|lock)\b
      | \b[a-z0-9]+_[a-z0-9_]+\b                             # snake_case
      | \b[a-z]+[A-Z][A-Za-z]+\b                             # camelCase
      | \b[A-Z][a-z]+[A-Z][A-Za-z]+\b                        # PascalCase
      | \bline\s+\d+\b
      | https?://
      | "[^"]{3,}"
      | '[^']{3,}'
    )""",
    re.X,
)

PRONOUN_IMPERATIVE_RE = re.compile(
    r"^\s*(please\s+)?(can\s+you\s+|could\s+you\s+|now\s+)?"
    r"(fix|change|update|improve|refactor|debug|clean|make|optimize|rewrite|redo|adjust|tweak|correct|finish)\b"
    r".*\b(it|this|that|them|these|those)\b",
    re.I,
)

BROKEN_RE = re.compile(
    r"\b(doesn'?t|does\s+not|isn'?t|is\s+not|won'?t|will\s+not|not)\s+work(ing)?\b"
    r"|\bstill\s+(broken|failing|wrong)\b"
    r"|\bit'?s\s+broken\b",
    re.I,
)

VAGUE_WHOLE = {
    "fix it", "fix this", "fix that", "fix", "make it better", "improve it",
    "improve this", "clean it up", "clean this up", "make it work",
    "try again", "do it again", "it's wrong", "its wrong", "that's wrong",
    "thats wrong", "do it better", "make it nicer",
}

CAPS_RE = re.compile(r"\b(CRITICAL|MUST|NEVER|ALWAYS|IMPORTANT|IMMEDIATELY|MANDATORY)\b")

LAZY_RE = re.compile(
    r"\b(do(\s+not|n'?t)\s+be\s+lazy|never\s+be\s+lazy"
    r"|do\s+not\s+(omit|skip)\s+anything"
    r"|write\s+the\s+(full|complete|entire)\s+(code|file|implementation)"
    r"|don'?t\s+truncate)\b",
    re.I,
)


def analyze(prompt):
    """Return a list of (rule_id, tier, message) for stage-1 findings."""
    findings = []
    text = prompt.strip()
    if not text:
        return findings
    words = text.split()
    normalized = " ".join(text.lower().split()).rstrip(".!?")
    concrete = bool(CONCRETE_RE.search(text))

    if normalized in VAGUE_WHOLE:
        findings.append((
            "CLR01", "error",
            "the entire prompt is a vague imperative with no concrete referent"))
    elif len(words) <= 12 and not concrete and PRONOUN_IMPERATIVE_RE.search(text):
        findings.append((
            "CLR01", "error",
            "short imperative aimed at 'it/this/that' with no file, symbol, or error identifying the target"))

    if len(words) <= 25 and not concrete and BROKEN_RE.search(text):
        findings.append((
            "CTX01", "error",
            "reports something 'not working' without the error output, symptom, or location"))

    if len(CAPS_RE.findall(text)) >= 2:
        findings.append((
            "MOD02", "warn",
            "ALL-CAPS pressure language — causes over-triggering on Claude 4.5+; state rules plainly"))

    if LAZY_RE.search(text):
        findings.append((
            "MOD05", "warn",
            "anti-laziness boilerplate — unnecessary on modern models and can cause overproduction"))

    return findings


# ------------------------------------------------------------- loop rescue

def _parser_mod():
    scripts = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import parse_transcript
    return parse_transcript


def rescue_eligible(text):
    """Current prompt: a short, low-information correction (per type-agentic.md)."""
    pt = _parser_mod()
    return (pt.is_correction(text)
            and len(text.split()) <= 15
            and not CONCRETE_RE.search(text))


def previous_real_prompt(transcript_path, current_text):
    pt = _parser_mod()
    prompts = []
    for entry in pt.iter_entries(transcript_path):
        if pt.is_real_user_prompt(entry):
            prompts.append(entry["message"]["content"].strip())
    # UserPromptSubmit usually fires before the prompt lands in the transcript,
    # but guard against the current prompt already being the last entry.
    if prompts and prompts[-1] == current_text.strip():
        prompts.pop()
    return prompts[-1] if prompts else None


RESCUE_CONTEXT = (
    "[Prompt Coach loop rescue] This is the second consecutive corrective prompt, and it adds "
    "little new information. Do not make another blind attempt. First state, in 1-2 sentences, "
    "your diagnosis of why the previous attempts missed (wrong target? wrong constraint? missing "
    "information you don't have?). If you can now see exactly what to change, proceed — diagnosis "
    "first, then the fix. If not, the documented best practice after two failed corrections is a "
    "fresh start: recommend the user run /clear, and draft the restart prompt for them — "
    "Goal / Where (files, the actual error) / Constraints / Verify — built from everything this "
    "session has established. Be brief and non-judgmental; don't lecture about prompt quality. "
    "(Disable this behavior: /coach config loop_rescue false.)"
)


# ------------------------------------------------------------- stage 2

def stage2_confirms(cfg, prompt, fired):
    """Run the configured verifier; return False only on an unambiguous VETO.

    Fails open to the stage-1 verdict on any error or timeout."""
    cmd = cfg.get("stage2_command")
    if not isinstance(cmd, list) or not cmd:
        return True
    rules = ", ".join(rule_id for rule_id, _tier, _msg in fired)
    judge = (
        "Reply with exactly one word: CONFIRM or VETO. A deterministic prompt-lint gate flagged "
        "the user prompt below as [%s]. VETO if, in a typical coding-agent session, the prompt is "
        "probably clear enough from surrounding context that a clarifying question would be an "
        "annoyance. CONFIRM if asking one clarifying question before executing is warranted.\n\n"
        "User prompt:\n%s" % (rules, prompt[:2000])
    )
    try:
        proc = subprocess.run(cmd + [judge], capture_output=True, text=True, timeout=20)
        out = (proc.stdout or "").strip().upper()
        if "VETO" in out and "CONFIRM" not in out:
            return False
    except Exception:
        pass
    return True


# ------------------------------------------------------------- plumbing

def build_context(fired, bypass_prefix):
    rules = "; ".join("%s: %s" % (rule_id, msg) for rule_id, _tier, msg in fired)
    return (
        "[Prompt Coach gate] This prompt tripped lint rule(s) — %s. Handle it this way: "
        "(1) Check whether the immediate context (conversation so far, repo state, recent errors) "
        "already disambiguates the request; if it does, proceed and state your interpretation in one line. "
        "(2) If genuinely ambiguous, investigate briefly first (read the likely files), then ask exactly ONE "
        "clarifying question via AskUserQuestion with options grounded in what you found, always including a "
        "'Proceed as written' option. "
        "(3) Do not lecture the user about prompt quality and do not mention rule IDs. "
        "(User controls: '/coach off' disables this; prefixing a prompt with '%s' bypasses it once.)"
        % (rules, bypass_prefix)
    )


def emit(context):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }))


def state_paths(session_id):
    state_dir = os.path.join(coach_home(), "state")
    os.makedirs(state_dir, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9\-]", "_", str(session_id or "unknown"))
    return os.path.join(state_dir, safe + ".json")


def load_state(path):
    try:
        with open(path, encoding="utf-8") as f:
            state = json.load(f)
        return state if isinstance(state, dict) else {}
    except Exception:
        return {}


def save_state(path, state):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f)


def main():
    data = json.load(sys.stdin)
    prompt = data.get("prompt") or ""
    cfg = load_config()
    if not cfg.get("enabled"):
        return

    stripped = prompt.lstrip()
    bypass = str(cfg.get("bypass_prefix") or "raw:")
    if (not stripped
            or stripped.startswith("/")
            or stripped.startswith("!")
            or stripped.startswith("#")
            or stripped.lower().startswith(bypass.lower())
            or stripped.startswith("[Request interrupted")):
        return

    state_path = state_paths(data.get("session_id"))
    state = load_state(state_path)

    # Loop rescue takes precedence over lint for correction prompts.
    if cfg.get("loop_rescue", True):
        try:
            if rescue_eligible(stripped):
                transcript_path = data.get("transcript_path")
                if transcript_path and os.path.isfile(transcript_path):
                    prev = previous_real_prompt(transcript_path, stripped)
                    if prev is not None and _parser_mod().is_correction(prev):
                        if (int(state.get("rescue", 0))
                                < int(cfg.get("max_loop_rescues_per_session", 1))):
                            state["rescue"] = int(state.get("rescue", 0)) + 1
                            save_state(state_path, state)
                            emit(RESCUE_CONTEXT)
                        return  # fired or capped — either way, no lint on top
        except Exception:
            pass

    threshold = cfg.get("threshold", "error")
    tiers = ("error",) if threshold != "warn" else ("error", "warn")
    fired = [f for f in analyze(prompt) if f[1] in tiers]
    if not fired:
        return
    if int(state.get("lint", 0)) >= int(cfg.get("max_triggers_per_session", 3)):
        return
    if cfg.get("stage2") and not stage2_confirms(cfg, stripped, fired):
        return

    state["lint"] = int(state.get("lint", 0)) + 1
    save_state(state_path, state)
    emit(build_context(fired, bypass))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
