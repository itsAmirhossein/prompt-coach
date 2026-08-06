---
name: prompt-retro
description: Outcome-grounded retrospective of a Claude Code session — reviews every user prompt against the lint rubric, anchors each critique to what actually happened next in the transcript, synthesizes the counterfactual opening prompt, and offers durable artifacts (CLAUDE.md lines, templates, profile updates). Use when the user asks to review a session, analyze their prompts, run a retrospective, or invokes /retro.
---

# Prompt Retro

Review a session's prompts and convert what you find into durable artifacts. The critique is only credible because it is **grounded in outcomes**: every "this prompt was weak" claim must point at what it actually cost in the transcript. A rubric violation that caused no observable trouble is at most an `info` note.

## Step 1 — Resolve the session

Arguments: `--current` (default) · `--session <id>` · `--list` · `--file <path>`.

The parser lives at `<plugin_root>/scripts/parse_transcript.py` (plugin root = two directories above this SKILL.md file). All calls need `--cwd "<the session's working directory>"`.

- `--list` → run with `--list`, show sessions (date, prompt count, first prompt), ask which to review.
- `--file <path>` → a conversation file outside the session store. If it is a Claude Code `.jsonl` transcript, run the parser with `--session <path>` (it accepts absolute paths). Any other format (TXT/Markdown export, rendered terminal log, exported chat) → parse agent-side: read the file, split turns on speaker markers (`User:` / `Assistant:` / `Human:` / `AI:` / `❯` / `●`, or alternating quoted turns), and treat each user turn as a prompt. Judge corrections/rephrases from the visible turns. Token and tool-error totals are not recoverable from a text export — say so in the cost line instead of inventing numbers. Then apply Steps 2–4 unchanged.
- Otherwise → run with `--current` or `--session <id>`, plus `--max-text 2000`.

If the session has fewer than 3 real prompts, say a retro won't be informative and offer `/improve` on the single prompt instead.

## Step 2 — Load the rubric

From the sibling skill `../prompt-improve/rubric/`: read `core.md`, `model-claude-4x.md`, and `type-agentic.md` (sessions are agentic by definition). Read the domain overlay (`mode-*.md`) if the session's content clearly fits one. Also read, if they exist: `<cwd>/.claude/prompt-coach.md` (team house rules — apply like rubric rules) and `~/.claude/prompt-coach/profile.md` (the user's recorded patterns — needed for the progress check in Step 4).

## Step 3 — Analyze each prompt, grounded

For each prompt in the parser output, use its outcome data — `is_correction`, `is_rephrase`, `tool_errors`, and whether the *following* prompts were corrections — as the evidence base:

- A prompt followed by a correction run: find the rubric rule whose violation explains the correction. That link (rule → observed consequence) is the whole value of the retro.
- A correction prompt itself: judge it as mid-session steering (see type-agentic.md) — did it diagnose, or just reject?
- A rephrase: the original prompt failed to land; identify why.
- A prompt with no downstream trouble: leave it alone even if imperfect. List it as clean. **Do not manufacture findings for prompts that worked.**

## Step 4 — Report

Fill `report-template.md` (in this skill's directory). Requirements:

- **Per-prompt sections only for prompts with findings**; clean prompts get one summary line ("Prompts 2, 5, 6: clean").
- Every **Impact** line cites transcript evidence: "led to 2 corrections (#5–#6)", "agent guessed X, you meant Y (see #4)", "3 tool errors while the agent searched for the unnamed file".
- **Patterns: exactly the top 2** recurring issues, by cost, not an inventory. Coaching that lists everything teaches nothing.
- **The counterfactual opening prompt is the centerpiece.** Using everything the session eventually established (the real goal, constraints discovered midway, the verify command that emerged), write the opening prompt that would have made this session short — in the type-agentic skeleton. Then state, honestly, what it would likely have saved (grounded in the correction runs it would have prevented).
- **Cost line** from `totals`: corrections, rephrases, tool errors, and `correction_output_tokens` as "~N output tokens spent inside correction loops (rough lower bound)". Real numbers only; no invented precision, no scores.
- **Progress check** (the teaching loop): compare this session against the profile. If a previously recorded pattern did *not* recur, say so in one line ("Previously noted: vague success criteria — didn't happen this time"). If it recurred, note the streak. One or two lines, max.

## Step 5 — Offer artifacts

Propose only what the evidence supports, via one AskUserQuestion (multiSelect):

1. **CLAUDE.md additions** — only for facts the user had to state mid-session that recur by nature (build commands, conventions, constraints). Before proposing, run the contradiction and duplication checks from `../prompt-audit/SKILL.md` (Step 3, items 2–3) against the target file: never duplicate what's there, and if the file's existing rules contradict each other, propose `/audit` instead of appending.
2. **Template** — only if the same prompt *shape* appeared ≥2 times; draft it per `../prompt-templatize/SKILL.md` (skeleton, self-lint, file format) into `~/.claude/prompt-coach/templates/<name>.md`, and mention `/templatize --use <name>` for next time.
3. **Profile update** — update `~/.claude/prompt-coach/profile.md` (create with a `# Prompt Coach profile` header if missing). Entry format: `- [YYYY-MM-DD] <pattern> (<rule IDs>, session <id>)`. If the pattern already has an entry, update that line (add the session, note the recurrence) instead of appending a duplicate. This file feeds future `/improve` runs and the progress check.

Write only what the user selects. Nothing is written without confirmation.

## Hard rules

- No numeric scores anywhere. No findings without transcript evidence. Top-2 patterns, not ten. The tone is a colleague's debrief, not a report card — the user's *prompts* are being reviewed, never the user.
