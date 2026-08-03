# Prompt Coach — test suite

Two layers, per DESIGN.md §3 item 6: deterministic tests you run in seconds, and a model-judged golden harness you run before any rubric release.

## 1. Deterministic tests (gate + parser)

```
python3 tests/test_gate.py
```

Covers the stage-1 heuristics (fire cases, false-positive quiet cases) and the hook end-to-end: config toggle, bypass prefix, slash-command skip, threshold tiers, per-session cap, fail-open on malformed input — plus the v0.2 paths: loop rescue (fires on the 2nd consecutive low-information correction, capped, disabled-config fallback, informative corrections stay silent) and the stage-2 verifier (VETO silences, CONFIRM passes, broken command fails open). Must pass before any change to `hooks/gate.py`.

Parser smoke test (read-only, uses your own real transcripts):

```
python3 scripts/parse_transcript.py --cwd <some project dir> --list
python3 scripts/parse_transcript.py --cwd <some project dir> --current --max-text 200
```

Check that prompt counts look right, command/meta entries are filtered, and corrections are plausibly flagged.

## 2. Golden harness (model-judged rubric regression)

`tests/golden/golden_prompts.jsonl` — one labeled case per line:

- `expect`: rule IDs the analysis MUST report (recall check).
- `forbid`: rule IDs it MUST NOT report (false-positive check). Clean prompts (`expect: []`) are the FP control set — a third of the suite, on purpose.
- `type` / `mode`: overlays to apply.

### Running it

For each case, run the analysis step of the `prompt-improve` skill (Steps 1–2 only — no rewrites needed) against `prompt` with the given type/mode, and record the reported rule IDs. Then score:

- **Recall** — fraction of `expect` IDs reported. Target ≥ 0.80.
- **False positives** — an error/warn-severity finding on a clean prompt, or any `forbid` ID reported. Target ≤ 10% of cases. (Info-severity notes on clean prompts count as half a hit — they erode trust too.)
- Report per-rule misses so rubric edits are targeted.

Cheapest way to run the whole suite headlessly from the repo root:

```
claude -p "Read tests/README.md section 2 and tests/golden/golden_prompts.jsonl. For each case, apply the analysis protocol from skills/prompt-improve/SKILL.md steps 1-2 (rubric in skills/prompt-improve/rubric/). Output one line per case: id, reported rule IDs, PASS/FAIL against expect+forbid. Finish with recall, FP rate, and per-rule miss counts."
```

Run it 2–3 times — rule detection has variance; a rule that flips across runs is a rubric-wording bug, not noise to ignore.

### The rule

**No rubric change ships without a golden run before and after.** If a change improves recall but raises FP rate, the FP rate wins — false positives are how this tool dies (core.md protocol rule 2). When a real-world miss or FP is found in use, add it here first, then fix the rubric against it (failure → permanent test case).

## 3. Audit fixture (model-judged)

`tests/fixtures/CLAUDE.bad.md` is a planted-defect CLAUDE.md for grading the `/audit` skill. Run the audit against it (`/audit tests/fixtures/CLAUDE.bad.md`) and check it finds all of:

1. **Contradiction:** "Always use npm" vs "install dependencies with `pnpm install`" (Setup section).
2. **Duplication:** the no-direct-commits-to-main rule appears twice (Rules, first and last bullets).
3. **Stale reference:** `scripts/deploy_old.sh` and `scripts/format_all.sh` don't exist (mechanical check).
4. **Pressure caps (MOD02):** the "IMPORTANT: You MUST NEVER…" bullet.
5. **Uncheckable rules (CLR02):** "Write clean, high-quality, maintainable code", "Be careful with the database".
6. **Misplaced automation:** "After every single file edit, run `scripts/format_all.sh`" → belongs in a hook.
7. **Wrong altitude (too low):** the four-way indentation exception rule.
8. **Derivable content:** the Project structure section (directory listing + dependency list restating package.json).
9. **Anti-laziness boilerplate (MOD05):** the Notes section.

Pass bar: ≥8 of 9 found, zero proposed edits to content that isn't defective, and nothing applied without confirmation. Do not "fix" the fixture — it is the exam.

## 4. Batch fixture (model-judged)

`tests/fixtures/batch-prompts.md` is three planted-defect prompts separated by `---`, for grading `/batch`. Run `/batch --file tests/fixtures/batch-prompts.md` and check four things — `/batch` is a dispatcher, so it is graded on structure + routing + faithful reuse, not on any new analysis of its own:

1. **Structure** — detects three separate prompts (not one blob, not a conversation), without needing `--as`.
2. **Routing** — sends each prompt to `prompt-improve` (a conversation would go to `/retro`, a CLAUDE.md-shaped file to `/audit`).
3. **Per-item findings match standalone** — the findings for each item are what `/improve` alone would report on that text. Reference expectations:
   - Prompt 1 (`fix it and make the tests better`): CLR01 (ambiguous referent "it"), CLR02 (vague "better"), CLR03 (no done-condition).
   - Prompt 2 (auth + docs + db "make everything clean and production ready"): STR03 (multiple unrelated asks fused), CLR02 (uncheckable "clean", "production ready"), CLR03.
   - Prompt 3 (`IMPORTANT: YOU MUST … Do not be lazy …`): MOD02 (CAPS pressure), MOD05 (anti-laziness boilerplate), CLR02/CLR04 (unbounded "ALL of the code across the whole repo").
4. **Overall summary** — names the recurring rules with counts (CLR02 in all three, CLR03 in prompts 1–2) as the headline, keeps to the top ~2 patterns, offers durable artifacts only on confirmation, and prints **no numeric score**.

Pass bar: correct segmentation and routing, per-item findings consistent with the golden expectations above, a summary that surfaces the recurring rules, and nothing written or executed without confirmation.
