# Prompt Coach

Visible prompt coaching for Claude Code. It explains what's weak in a prompt, shows the fix, reviews your sessions, and turns what it finds into templates and rules you keep — instead of silently rewriting your prompts or scoring you with made-up numbers.

**Principles:** everything local · categorical lint findings, never numeric scores · no silent rewrites — every change shown, explained, and chosen by you · critiques grounded in what actually happened, not abstract rules.

## Commands

| Command | What it does |
|---|---|
| `/improve [prompt \| --last \| --file <f>]` | Lint findings with rule IDs and evidence, context you should add, and two rewrite candidates: **conservative** (minimal, intent-preserving) and **restructured** (full best-practice shape). You pick; original always an option. |
| `/improve --target <model>` | Migration lint only: which parts of this prompt break or degrade on a given model generation (e.g. prefill → hard 400 on Claude 4.6+). |
| `/improve --test` | A/B evidence: run the original and the chosen rewrite on a sample input in parallel, judge both orders (order-flip = tie), report honestly — including "no meaningful difference". One-shot/template prompts only. |
| `/retro [--current \| --list \| --session <id>]` | Outcome-grounded retrospective: per-prompt review anchored to what each prompt actually cost (corrections, errors, wasted tokens), the top-2 recurring patterns, a progress check against your profile, **the counterfactual opening prompt** that would have avoided the mess, and confirmable artifacts (CLAUDE.md lines, templates, profile updates). |
| `/templatize [prompt \| --last \| --file <f>]` | Turn a concrete prompt into a reusable `{{variable}}` template (self-linted against the template rubric) and save it to your library. `--list` shows the library; `--use <name>` fills and runs one; `--from-examples` induces a prompt from 2–3 input→output pairs. |
| `/audit [paths… \| --global]` | Lint CLAUDE.md and context files: contradictions (within and across files), stale file/command references (checked mechanically), duplication, pressure language, uncheckable rules, wrong-altitude instructions, derivable content, misplaced automation. Minimal fixes, applied only on confirmation. |
| `/coach on\|off\|status\|config` | Toggle and tune the always-on gate. |

## The always-on gate (off by default)

`/coach on` enables a `UserPromptSubmit` hook that is **silent on the overwhelming majority of prompts**. It runs free deterministic checks (no model calls, ~10ms) and fires solely on high-confidence problems — "fix it" with no referent, "it doesn't work" with no error text. When it fires, Claude first checks whether the repo/conversation already disambiguates your prompt; only if genuinely ambiguous does it ask **one** clarifying question, grounded in what it found, with "proceed as written" always an option.

**Loop rescue** (v0.2): after two consecutive low-information corrections ("no, still wrong" → "still broken"), instead of letting Claude take a third blind attempt, the gate has it diagnose first — and if the corrections added no information, recommend `/clear` with a drafted restart prompt built from what the session established. At most once per session; `loop_rescue false` disables it.

**Stage 2** (optional, off by default): `stage2 true` adds a Haiku verifier that can veto a stage-1 fire when the prompt is probably clear from context — better precision, at the cost of seconds of latency and a small token spend on flagged prompts only. Fails open to the stage-1 verdict.

Guardrails: at most 3 lint interventions per session (configurable), `raw:` prefix bypasses once, `/coach off` kills everything. The hook never blocks or rewrites a prompt and fails open on any internal error.

Note a platform constraint honestly: hooks cannot replace your prompt text. The "choose original vs improved" flow is therefore implemented as a grounded clarifying question, not a swap.

## Install

In Claude Code:

```
/plugin marketplace add itsAmirhossein/prompt-coach
/plugin install prompt-coach@prompt-coach
```

(From a local checkout instead: `/plugin marketplace add /path/to/prompt-coach`.) Restart Claude Code after install. Requires `python3` on PATH (macOS/Linux default).

## Team house rules

Commit `.claude/prompt-coach.md` to a repo to add project-scoped lint rules — one rule per bullet, each checkable, with a reason. `/improve` and `/retro` apply them like rubric rules (cited as HR01, HR02…), and they win over core rules on conflict. Example:

```markdown
- Prompts asking for DB changes must name the migration tool (we use dbmate, not raw SQL) — mixed tooling has burned us twice.
- Bug reports must include the request ID from Sentry.
```

## Data & privacy

Everything stays on your machine. `/retro` reads your local session transcripts (`~/.claude/projects/…`), which may contain code and secrets — nothing is sent anywhere beyond your normal Claude session. Plugin state lives in `~/.claude/prompt-coach/`:

- `config.json` — gate settings: `enabled`, `threshold` (`error`|`warn`), `max_triggers_per_session`, `bypass_prefix`, `loop_rescue`, `max_loop_rescues_per_session`, `stage2`, `stage2_command`
- `profile.md` — recurring patterns from retros (feeds `/improve` prioritization and the retro progress check)
- `templates/` — your template library (`/templatize`)
- `feedback.jsonl` — which rewrite candidates you picked (local learning signal)
- `state/` — per-session trigger counters

Review artifacts before committing any to a shared repo.

## Layout

- `skills/prompt-improve/rubric/` — **the product**: the lint catalog (`core.md`), version-pinned model-era rules (`model-claude-4x.md`), prompt-type overlays (oneshot/agentic/template), domain overlays (swe/research/writing). Rules are data; PRs against the rubric are the main way to improve the tool.
- `skills/prompt-retro/` — retrospective procedure + report template.
- `skills/prompt-templatize/` — template extraction, instruction induction, library management.
- `skills/prompt-audit/` — CLAUDE.md/context-file linter.
- `scripts/parse_transcript.py` — read-only transcript parser (prompts + outcome signals + token usage).
- `hooks/gate.py` — stage-1 gate + loop rescue + optional stage-2 verifier.
- `tests/` — deterministic gate tests (`python3 tests/test_gate.py`, 34 cases), the 40-case model-judged golden set, and the planted-defect audit fixture. **No rubric change ships without a golden run** — see `tests/README.md`.

Design rationale, competitive research, and roadmap: see `DESIGN.md`. Shipped through the Advanced tier (v0.2); still deferred: eval-backed template optimization, local trend analytics, claude.ai-portable build.
