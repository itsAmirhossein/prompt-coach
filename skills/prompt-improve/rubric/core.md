# Prompt Coach — Core Lint Catalog (rubric v0.1)

The rulebook for analyzing prompts. Findings are categorical — never numeric scores.

## Application protocol

1. **Evidence or silence.** Every finding must quote the exact text that triggers it (or name the exact absence — "no output format stated anywhere"). If you cannot point at evidence, the finding does not exist.
2. **A clean prompt gets zero findings.** Say "No findings — this prompt is solid" and stop. Do not invent findings to appear useful; false positives are how this tool dies.
3. **Cap the report.** At most 5 findings, ordered error → warn → info. If more exist, report the top 5 and state how many were omitted (`--deep` lifts the cap).
4. **Severity meanings:**
   - `error` — will likely cause a wrong or wasted response: ambiguity the model must guess about, contradictions, missing referents.
   - `warn` — degrades quality or reliability in a predictable way.
   - `info` — inefficiency or style; fixing is optional.
5. **Finding format:**
   `[CLR01 error] Ambiguous referent — evidence: "fix it" — impact: the model must guess which of several things to fix; a wrong guess wastes the turn or the session.`
6. **Always load `model-claude-4x.md` alongside this file** — it holds the MOD (model-era) rules and their version pins.
7. **Overlays win.** The prompt-type overlay (`type-*.md`) and domain overlay (`mode-*.md`) may raise/lower severities or waive rules for that context. Where an overlay contradicts this file, the overlay is right.
8. **Judge the prompt for its context.** A terse prompt in a rich session where context disambiguates it is fine; the same prompt cold is an error. When analyzing retrospectively, check whether the surrounding conversation supplied what the prompt omitted before flagging.

---

## CLR — Clarity

### CLR01 · Ambiguous referent · error
- **Detect:** "it", "this", "that thing", "the function" with no antecedent in the prompt or unambiguous antecedent in immediate context.
- **Impact:** the model guesses the target; a wrong guess wastes the turn and often the next several.
- **Fix:** name the file, symbol, artifact, or paste the identifier: "fix the off-by-one in `Pager.next()` (src/pager.ts)".

### CLR02 · Vague success criteria · warn
- **Detect:** "better", "cleaner", "more professional", "some tests", "etc.", "and so on" — quality or quantity words with no observable meaning.
- **Impact:** the model optimizes for its own reading of "better", which may not be yours; output is unfalsifiable.
- **Fix:** state the observable outcome: "reduce the function to a single pass", "3 tests covering the empty, single, and overflow cases".

### CLR03 · No done-condition · warn (error in agentic type)
- **Detect:** a multi-step task with no statement of what "finished" looks like or how to check it.
- **Impact:** the model stops too early or gold-plates; you can't tell if it succeeded.
- **Fix:** one sentence: "done when `npm test` passes and the new endpoint returns 201 on the happy path".

### CLR04 · Ambiguous scope · warn
- **Detect:** a request that could legitimately mean a 10-line change or a 1000-line change ("add caching", "support dark mode") with no boundary.
- **Impact:** scope roulette — usually discovered only after the wrong-size answer arrives.
- **Fix:** bound it: which layer, which surfaces, what's explicitly out of scope.

## CTX — Context

### CTX01 · Missing referent material · error
- **Detect:** the prompt references something the model cannot see — "the error", "the design doc", "as we discussed" — without pasting it, pointing to a path, or the context containing it.
- **Impact:** the model reconstructs the missing material by guessing; the answer is grounded in fiction.
- **Fix:** paste the error text verbatim; give the file path; summarize the prior decision in one line.

### CTX02 · Assumed private knowledge · warn
- **Detect:** internal project names, team conventions, acronyms, or prior-conversation facts stated as if universally known.
- **Impact:** the model either guesses the meaning or silently ignores the term.
- **Fix:** one-line gloss on first use: "ARB (our internal review board)".

### CTX03 · Pasted what could be pointed to · info (agentic type only)
- **Detect:** large verbatim code/doc blocks pasted into an agentic prompt when the agent can read the file itself.
- **Impact:** token waste, staleness risk, and the pasted copy diverges from the file the agent will actually edit.
- **Fix:** give the path (and line range if helpful); paste only what's off-disk (error output, a spec from elsewhere).

### CTX04 · Irrelevant context bloat · info
- **Detect:** background material with no bearing on the ask (history of the project, three paragraphs of pleasantries, dead constraints).
- **Impact:** dilutes the signal; long low-relevance preambles measurably degrade instruction-following.
- **Fix:** cut, or move essentials into a one-line constraint.

## CON — Constraints & contradictions

### CON01 · Internal contradiction · error
- **Detect:** two instructions that cannot both be satisfied: "be comprehensive… keep it under 100 words", "don't change the API… rename the endpoint".
- **Impact:** the model silently picks one side; which side varies run to run — the classic reliability killer.
- **Fix:** resolve the conflict yourself, or make the priority explicit: "if length and completeness conflict, prefer brevity".

### CON02 · Missing constraint that will matter · warn
- **Detect:** an ask where an unstated constraint predictably changes the answer: language/framework version, environment, backward-compatibility, "don't touch X", audience, region, budget.
- **Impact:** a correct answer to the wrong problem; discovered late.
- **Fix:** state the constraints you already know: "Python 3.9, no new dependencies, must stay backward-compatible with the v1 clients".

### CON03 · Over-constraint · info
- **Detect:** the prompt prescribes the implementation when it means to describe the problem ("add a mutex in acquire()" when the actual need is "make acquire() thread-safe").
- **Impact:** forecloses better solutions; the model follows orders off a cliff.
- **Fix:** state the problem and the acceptance criteria; constrain the solution only where you genuinely require it.

## FMT — Output format

### FMT01 · No format when format matters · warn
- **Detect:** output destined for a specific use (a table to paste, JSON to parse, a commit message, a doc section) with no format stated.
- **Impact:** re-work; for machine-consumed output, breakage.
- **Fix:** one line: "output as a two-column markdown table", "JSON matching {name, path, reason}".

### FMT02 · Format by counter-example only · info
- **Detect:** format specified only as prohibitions ("no bullet points, no headers, don't be long").
- **Impact:** negative-only instructions are the weakest format control; the model must infer the positive shape.
- **Fix:** say what to do: "2–3 plain paragraphs, ~150 words".

## STR — Structure

### STR01 · Buried instruction · warn
- **Detect:** the actual ask sits mid-paragraph inside a wall of text; no separation between context, task, and constraints.
- **Impact:** instruction gets diluted or partially missed, especially with multiple asks.
- **Fix:** short labeled sections or a blank line between context and task; the ask stated first or last, not buried.

### STR02 · Data before instructions · info (warn at 20k+ tokens of data)
- **Detect:** long documents/code pasted first, instructions at the bottom missing, or instructions only at the top of very long material.
- **Impact:** for long contexts, models handle "documents first, query last" best; misordering costs accuracy.
- **Fix:** long material in delimited blocks first, the question/instructions after it.

### STR03 · Fused unrelated asks · warn
- **Detect:** multiple independent tasks in one prompt ("fix the login bug, also update the README, and what do you think about switching to pnpm?").
- **Impact:** uneven effort across asks; the weakest ask gets a throwaway answer; hard to review.
- **Fix:** split into separate prompts, or explicitly rank: "primary task: … ; if time permits: …".

## AGT — Agentic (apply only when type = agentic; see type-agentic.md)

### AGT01 · No verification path · warn
- **Detect:** an agentic task with no way for the agent to check its own work (no test command, no expected behavior, no example input/output).
- **Impact:** the agent declares success on unverified work; errors surface later, on you.
- **Fix:** give the check: "verify with `pytest tests/test_pool.py`", "the page at /settings should render without console errors".

### AGT02 · Unbounded blast radius · warn
- **Detect:** open-ended change requests with no statement of what must not change ("clean up the codebase", "modernize the styles").
- **Impact:** collateral edits in places you didn't want touched.
- **Fix:** name the boundary: "only under src/auth/", "no public API changes", "don't touch the generated files".

## EFF — Efficiency

### EFF01 · Low-information redundancy · info
- **Detect:** the same instruction restated in several phrasings; boilerplate that adds no constraint ("please make sure to do a good job").
- **Impact:** token cost and — worse — dilution: each restatement slightly reweights attention away from the instructions that matter.
- **Fix:** say it once, precisely. (Keep this *readable* — never compress into unmaintainable shorthand.)

### EFF02 · Cache-hostile ordering · info (templates only; see type-template.md)
- **Detect:** a reusable template with volatile content (dates, user input, per-run data) before stable content.
- **Impact:** breaks prompt-cache prefix matching; every run pays full input cost.
- **Fix:** stable preamble first (role, rules, examples), volatile material last.
