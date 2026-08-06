---
name: prompt-check
description: Universal review dispatcher — accept anything (a single prompt, many prompts, or a file of prompts/conversations in Markdown, TXT, JSONL, or exported-chat form), determine its structure, route each item to the applicable Prompt Coach capability (improve / retro / templatize / audit) unchanged, then summarize recurring issues across the whole input. Use when the user passes multiple prompts, a file of prompts or conversations, or invokes /check.
---

# Prompt Check

A dispatcher, not a new analyzer. Check determines the structure of whatever it is handed, splits it into items, routes each item to the existing capability that fits, and runs *that capability's own procedure, unchanged*. It adds exactly one new thing: a cross-item summary. It never re-implements linting, rewriting, retro, templating, or auditing — it calls them. Any capability added to Prompt Coach later is reachable the same way, with no change here.

## Step 0 — Parse arguments

Supported: literal text (one prompt or many) · `--file <path>` (or a bare path that exists) · `--mode swe|research|writing` and `--deep` and `--target <model>` (passed through to each routed item) · `--as prompts|conversations|context` (skip structure detection and force the unit type).

No input → ask the user to paste the prompts/conversations or give a `--file`.

## Step 1 — Determine the structure (do this first)

Decide the **source**, then the **unit type**. Never guess silently on an ambiguous split — confirm it with one AskUserQuestion before analyzing anything.

**Source** — a readable file path (or `--file`) → read it; otherwise the argument text *is* the input.

**Unit type** — classify the content into one of:

| Signal | Unit type |
|---|---|
| `.jsonl` where lines carry `type` / `uuid` / `message` / `timestamp` | conversation — a Claude Code transcript |
| JSON export with `mapping` / `messages` / `author.role` (ChatGPT/Claude web export) | conversation(s) — exported chat |
| Turn markers: `User:` / `Assistant:` / `Human:` / `AI:`, or `>`-quoted alternating turns | conversation(s) |
| Rule bullets, "always…/never…", or a `CLAUDE*.md` / `.claude/*.md` filename | context-file |
| Blocks split by blank lines, `---`, or `Prompt N:` / numbered headers | multiple prompts |
| One blob, no separators | single prompt |

`--as <type>` overrides detection. When the split between "one long prompt" and "several prompts" is genuinely unclear, show the candidate segmentation and ask *treat as N items or 1?* first. If a file holds a **mix** (several conversations, or prompts plus a context file), segment by kind and route each segment to its matching capability.

## Step 2 — Route each item (reuse, never re-implement)

For every item, invoke the matching capability and follow its `SKILL.md` **exactly** — the output for one item must be identical to running that capability on it standalone:

| Unit | Capability | How |
|---|---|---|
| prompt | `prompt-improve` | Skill `prompt-coach:prompt-improve` with the item text + any `--mode` / `--deep` / `--target` |
| conversation in a file (`.jsonl` or text/markdown export) | `prompt-retro` | Skill `prompt-coach:prompt-retro` with `--file <path>` (its Step 1 handles both formats) |
| conversation pasted as text (no file) | `prompt-retro` | Follow prompt-retro's `--file` procedure on the pasted text (agent-side turn parsing), then its Steps 2–4 unchanged |
| context-file | `prompt-audit` | Skill `prompt-coach:prompt-audit` with the file path |

A single item → just run that capability and stop; the dispatcher adds nothing to one item.

**The only behavioral adaptation for many items:** defer each capability's terminal *choose-a-candidate-and-run* / *apply-this-fix* interaction. The items are artifacts under review, not prompts to execute now — identical to how `/improve --file` reviews a saved prompt without executing it, and how `/retro` reviews many prompts and offers artifacts once at the end. Produce the full analysis for each item (findings, context-to-add, both candidates and the intent check for prompts; the grounded per-prompt review and counterfactual for conversations; the proposed diffs for context files) and collect the offered actions. Present the consolidated choices once, in Step 5. Nothing else about any capability changes.

## Step 3 — Per-item report

- **≤ ~8 items** → full per-item analysis inline, each clearly delimited by item.
- **> ~8 items** → lead with a compact table (`item · detected type · routed capability · fired rule IDs · one-line verdict`), then full detail for the items with the most or most-severe findings, and offer to expand the rest. State any cap you apply — never drop items silently.
- A clean item gets one line ("Item 3: clean"), the same false-positive discipline the linter uses everywhere.

## Step 4 — Overall summary (the one new thing)

Only when there are ≥2 items. Synthesize over the *per-item findings* — not the raw content, so nothing is re-analyzed:

- **Recurring issues** — the rule IDs that fired across multiple items, with counts ("CLR03 no done-condition — 6 of 9 prompts; CTX01 unshown referent — 4 of 9"). This is the headline of a multi-item run.
- **Top 2 patterns** — the two highest-leverage habits, grounded in the per-item evidence, not an inventory (retro's discipline: coaching that lists everything teaches nothing).
- **Opportunities** — concrete and evidence-backed: a template if one prompt *shape* repeats ≥2× · CLAUDE.md lines for a constraint the items keep restating · a profile update.
- No numeric scores, ever. A count is evidence; it is not a grade.

## Step 5 — Offer durable artifacts

One AskUserQuestion (multiSelect) over what the evidence supports, each drafted through the owning capability so nothing is re-implemented:

- **Templatize** a repeated shape → `prompt-coach:prompt-templatize` (its save flow and self-lint).
- **CLAUDE.md lines** → run `prompt-audit` checks 2–3 on the target file first, exactly as `/retro` does before appending.
- **Profile update** → the `/retro` Step 5 format.
- **Apply one item's rewrite / fix** → for the items the user names, resume that capability's deferred terminal step (pick a candidate, or apply the diff).

Write or execute only what the user selects. Nothing is written without confirmation.

## Hard rules

- Check never lints, rewrites, retros, templatizes, or audits by itself — it routes to the capability that does. Per-item behavior is identical to standalone; the only difference across many items is deferred, consolidated interaction.
- Determine structure before analyzing; confirm an ambiguous split rather than guessing.
- No numeric scores. No silent truncation of items. Nothing written or executed without confirmation.
