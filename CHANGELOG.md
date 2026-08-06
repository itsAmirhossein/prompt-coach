# Changelog

All notable changes to Prompt Coach are documented here. This project adheres to [Semantic Versioning](https://semver.org) and the [Keep a Changelog](https://keepachangelog.com) format.

## [0.4.0] — 2026-08-06

### Changed

- **`/batch` renamed to `/check`** (skill `prompt-batch` → `prompt-check`). "Batch" described the incidental property (plurality) rather than the essential one (routing): the command accepts *anything* — one prompt, many, or a file — and routes each piece to the right capability. No deprecation alias is kept; the old name had also proven collision-prone with user-local commands named `batch`.

### Added

- **`/retro --file <path>`** — review a conversation file directly: a Claude Code `.jsonl` transcript (via the existing parser) or a text/markdown export (turns parsed agent-side; token totals honestly reported as unavailable). `/check`'s conversation routing now delegates to it.

## [0.3.0] — 2026-08-03

### Added

- **Batch and file input (`/batch`, skill `prompt-batch`).** Accept a single prompt, many pasted prompts, or a file of prompts/conversations (Markdown, TXT, JSONL, exported chats). `/batch` determines the input structure, splits it into items, and routes each item to the existing capability that fits — a prompt to `/improve`, a conversation to `/retro`, a CLAUDE.md-shaped context file to `/audit` — then adds a cross-item summary of recurring rule IDs and shared opportunities. It is a dispatcher, not a new analyzer: per-item behavior is identical to running the underlying command standalone, no capability is re-implemented, and any capability added later is reachable by adding a routing-table row.
- Grading fixture `tests/fixtures/batch-prompts.md` and a `/batch` grading section (`tests/README.md` §4).

### Notes

- No parser change was needed: `parse_transcript.py` already resolves `--session <path>` to an arbitrary file, so Claude Code transcript files route into `/retro` unchanged; non-Claude exports are segmented agent-side.

## [0.2.0] — 2026-07-28

Initial public release.

### Added

- **`/improve`** — lint findings with rule IDs and evidence, context suggestions, and two rewrite candidates (conservative + restructured); `--target <model>` migration linting; `--test` A/B comparison.
- **`/retro`** — outcome-grounded session retrospective with a counterfactual opening prompt, top-2 recurring patterns, session-cost accounting, and durable artifacts (CLAUDE.md lines, templates, profile updates).
- **`/templatize`** — turn a prompt into a reusable `{{variable}}` template, induce one from input/output examples (`--from-examples`), and manage a personal template library.
- **`/audit`** — lint CLAUDE.md and context files for contradictions, stale references, pressure language, bloat, and uncheckable rules.
- **`/coach`** — optional threshold-gated always-on gate (off by default) with correction-loop rescue and an opt-in Haiku stage-2 verifier.
- Model-version-aware lint rubric (core catalog + Claude 4.x model-era rules + prompt-type and domain overlays), a 40-case golden test set, and 34 deterministic gate tests.
- Team house rules via `.claude/prompt-coach.md`.

[0.4.0]: https://github.com/itsAmirhossein/prompt-coach/releases/tag/v0.4.0
[0.3.0]: https://github.com/itsAmirhossein/prompt-coach/releases/tag/v0.3.0
[0.2.0]: https://github.com/itsAmirhossein/prompt-coach/releases/tag/v0.2.0
