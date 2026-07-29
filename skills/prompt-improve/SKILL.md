---
name: prompt-improve
description: Analyze and improve a prompt — lint findings with rule IDs and evidence, context suggestions, and two rewrite candidates (conservative and restructured). Use when the user asks to improve, critique, review, lint, or optimize a prompt, check a prompt against a model version, or invokes /improve.
---

# Prompt Improve

Critique and rewrite a prompt without drifting its intent. You are a coach, not a ghostwriter: every change is shown, explained, and chosen by the user.

## Step 0 — Parse arguments

Supported: literal prompt text · `--last` (the user's previous prompt in this session) · `--file <path>` · `--mode swe|research|writing` · `--target <model>` (migration lint only) · `--deep` (no finding cap; also compare candidates more carefully) · `--test` (A/B-compare original vs chosen rewrite on a sample input; oneshot/template types only).

- No arguments → ask the user to paste the prompt, or offer `--last`.
- `--last` → run the transcript parser (plugin root is two directories above this SKILL.md file):
  `python3 <plugin_root>/scripts/parse_transcript.py --cwd "<session cwd>" --current --last-prompt`
- `--file` → read the file; if it contains `{{variables}}` or reads like a system prompt, it is type `template`.

## Step 1 — Load the rubric

Always read, from this skill's `rubric/` directory: `core.md` and `model-claude-4x.md`.
Classify, then read the matching overlays:
- **Type** — `oneshot` | `agentic` | `template` (agentic = it targets this or another tool-using agent session; template = reusable/{{vars}}/system prompt; else oneshot). Read `type-<type>.md`.
- **Domain** — `swe` | `research` | `writing` if clearly detectable or given via `--mode`; read `mode-<domain>.md`. If no domain fits, use core rules only — do not force a domain.

For rewrites, also read `examples/gold-prompts.md` and match the exemplar's shape for the detected type.

`--target <model>` short-circuits: run ONLY the MOD family against the prompt, report which rules the target model changes, and stop (no rewrite unless asked).

## Step 1.5 — Personal and team context

- **Team house rules:** if `<cwd>/.claude/prompt-coach.md` exists, read it. Its rules are additional rubric entries scoped to this project (cite as HR01, HR02… in file order); on conflict with core rules, house rules win.
- **Profile:** if `~/.claude/prompt-coach/profile.md` exists, read it. Check the user's recorded recurring patterns first, and when a finding matches one, say so in one clause ("this is your most frequent pattern"). Never use the profile to pad findings a clean prompt doesn't have.

## Step 2 — Analyze

Apply the rubric per its application protocol (evidence or silence; max 5 findings unless `--deep`; overlays win). For agentic prompts in a live session, check whether the surrounding conversation already disambiguates before flagging CLR/CTX rules — a terse prompt with rich context is not a bad prompt.

**If there are zero findings: say "No findings — this prompt is solid", optionally note one thing it does well, and stop.** Do not produce rewrite candidates for a clean prompt.

## Step 3 — Report

1. **Findings** — the rubric's format, ordered by severity.
2. **Context to add** — from CTX/CON findings, a short list of what the user should supply that you cannot invent (error text, versions, audience…). If the missing context is *available to you* (a file in the repo, the conversation), fetch it yourself and fold it into the candidates instead of asking.

## Step 4 — Two candidates

- **Conservative** — minimal edit: fix error- and warn-level findings only, preserve the user's wording and structure everywhere else.
- **Restructured** — the type overlay's skeleton applied, gold-exemplar shape, info-level findings also fixed. Skip this candidate when the prompt is short and simple enough that restructuring adds nothing (say so — over-engineering a 1-line prompt violates MOD06), or when missing context makes a full rewrite speculative.

For each candidate, list changes as: *change → rule → why*. Where required context is missing, use an explicit `[FILL IN: the exact error text]` placeholder — never fabricate specifics the user didn't give.

**Intent check (mandatory):** state in one line what the original asks for; verify each candidate asks for exactly that. If a candidate sharpened something ambiguous, name the interpretation you chose so the user can veto it.

## Step 5 — Choose

Use AskUserQuestion: **Use conservative** / **Use restructured** / **Keep original** / **Refine further** (with a note of what to change). If the prompt was meant for this session, execute the chosen version immediately as if the user had sent it. If `Refine further`, iterate on the chosen base.

## Step 5b — `--test` (A/B evidence)

Only for `oneshot` and `template` types — never execute two full agentic runs. After the user picks a candidate:

1. Get a sample input: the prompt's own material, one the user provides, or synthesize a realistic one for templates (fill the `{{variables}}`; show the filled values).
2. Produce output A (original prompt) and output B (chosen candidate) via two parallel Agent tool calls, so neither run sees the other.
3. Judge both orders: compare A-vs-B, then B-vs-A with positions swapped, against (a) the findings you flagged — did the rewrite actually fix them? — and (b) overall task quality. If the verdict flips with order, call it a tie.
4. Report honestly. "Improved on X, no difference on Y" and "no meaningful difference" are legitimate verdicts — show both outputs (or excerpts) so the user can disagree.

## Step 6 — Log (silent)

Append one line to `~/.claude/prompt-coach/feedback.jsonl` (create the directory/file if needed; get the timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ`):
`{"ts": "...", "rules": [fired IDs], "type": "...", "mode": "...", "choice": "conservative|restructured|original|refine"}`
Do not narrate this step. If it fails, skip silently — never let logging break the flow.

## Hard rules

- Never numeric scores. Never auto-apply a rewrite. Never invent findings for a clean prompt. Never fabricate missing specifics. Keep the whole report tight — findings and candidates, not an essay on prompt engineering.
