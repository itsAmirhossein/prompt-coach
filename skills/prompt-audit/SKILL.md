---
name: prompt-audit
description: Lint CLAUDE.md and other context files (CLAUDE.local.md, .claude/*.md rule files, optionally the global ~/.claude/CLAUDE.md) for contradictions, stale references, pressure language, bloat, uncheckable rules, and wrong-altitude instructions; propose minimal fixes as diffs. Use when the user asks to audit, clean up, or review CLAUDE.md or context files, or invokes /audit.
---

# Prompt Audit

Context files are templates that run on *every* prompt — a defect in CLAUDE.md is a defect in every future session. Anthropic's own guidance: a bloated CLAUDE.md causes Claude to ignore your actual instructions. This audit finds the defects and proposes minimal fixes; it never rewrites wholesale.

## Step 1 — Collect the files

- Default set (skip missing ones silently): `<cwd>/CLAUDE.md`, `<cwd>/CLAUDE.local.md`, `<cwd>/.claude/*.md` (rule/standards files, including `.claude/prompt-coach.md`).
- `--global` adds `~/.claude/CLAUDE.md`.
- Explicit paths as arguments override the default set.
- Nothing exists → say so and stop; offer to draft a minimal CLAUDE.md only if the user asks.

## Step 2 — Load the rubric

From `../prompt-improve/rubric/`: `core.md` (CON, STR, EFF, CLR02), `model-claude-4x.md` (MOD), `type-template.md` (the right-altitude test — context files ARE reusable templates).

## Step 3 — The checks

1. **Stale references (mechanical — run it, don't eyeball it):** extract every file path, script, and command the files mention; verify each exists (`ls`, `test -f`, `command -v` for the base command of documented invocations). A rule pointing at a deleted script is worse than no rule — it teaches Claude the file is authoritative when it's fiction.
2. **Contradictions (CON01)** — within a file and *across* files (CLAUDE.md vs CLAUDE.local.md vs .claude/*.md vs global): conflicting package managers, formatting rules, branch conventions. State which instruction currently wins is undefined — that's the bug.
3. **Duplication** — the same rule stated in multiple places; drift between the copies is a future contradiction.
4. **Pressure & boilerplate (MOD02, MOD05)** — CAPS-lock rules, "NEVER EVER", anti-laziness lines.
5. **Uncheckable rules (CLR02)** — "write clean code", "be careful with the database": cannot be checked against any output. Either make it concrete or cut it.
6. **Wrong altitude** (type-template.md test) — brittle micro-rules that break on the first unanticipated case, and platitudes that constrain nothing. For each rule: would a competent new hire need this told once (keep), per-case (too low — generalize), or never (too high — cut)?
7. **Derivable content** — sections restating what the code, README, or file tree already shows (directory listings, dependency lists). Claude reads the repo; CLAUDE.md should hold what it *can't* derive.
8. **Misplaced automation** — "always run X after every edit" style instructions. Instructions are unreliable for always-behaviors; the harness executes hooks deterministically. Flag with: "this belongs in a hook (settings.json), not CLAUDE.md" — recommend, don't implement.
9. **Bloat (info)** — report total line count per file. No hard limit, but past ~150 lines look hard for items 3/6/7; note the two or three sections doing the least work.

## Step 4 — Report

Per file: findings as `file:line — [RULE severity] issue — proposed fix (before → after)`. Order by severity. A clean file gets "clean" and nothing else — same false-positive discipline as the prompt linter. Cross-file contradictions get their own section listing both locations.

## Step 5 — Apply

One AskUserQuestion (multiSelect) over the proposed fixes. Apply only what's selected, as minimal edits — never reformat or reorder untouched content. Deletions the user didn't select stay put. Close with one line on what changed.

## Interplay

When `/retro` proposes CLAUDE.md additions, it runs this audit's checks 2–3 on the target file first — never append to a file whose existing rules contradict each other.
