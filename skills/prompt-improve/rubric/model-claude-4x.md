# Model-era rules — Claude 4.x / Fable generation (MOD family)

Version-pinned rules. These change when models change; check the changelog before trusting a finding, and cite the version pin in every MOD finding (that citation *is* the migration-linting feature: `/improve --target <model>` runs only this file against the prompt).

Baseline assumption: the prompt targets Claude 4.5+ / Fable-era models. If the user names an older target model, waive MOD rules that don't apply to it and say so.

## MOD01 · Prefill · error (API prompts/templates only)
- **Detect:** a template that seeds the assistant turn with partial output (prefill), e.g. `"assistant": "{"` or "start your response with…" used as a forced prefix at the API level.
- **Pin:** hard **400 error on Claude 4.6+**. Older advice (including Anthropic's own Console improver output) still emits these.
- **Fix:** structured outputs for JSON; "respond directly without preamble" for chat; a tool with an enum for classification.

## MOD02 · Pressure language · warn
- **Detect:** ALL-CAPS emphasis and threat-style emphasis: "CRITICAL:", "YOU MUST", "NEVER EVER", "IMPORTANT!!!".
- **Pin:** on Claude 4.5+ this causes **over-triggering** — the model over-applies the emphasized rule in cases it shouldn't. Anthropic guidance: "dial back aggressive language".
- **Fix:** state the rule plainly once, and give the *reason*: "Use X here because Y" outperforms "ALWAYS USE X".

## MOD03 · Prescriptive chain-of-thought script · info
- **Detect:** "think step by step", numbered private-reasoning scripts ("First, list assumptions. Second, …") for reasoning-capable models.
- **Pin:** superseded by adaptive/extended thinking (4.6+). General nudges ("consider the edge cases before answering") are fine; step scripts constrain reasoning and add tokens. Quirk: for Opus 4.5 without thinking enabled, the bare word "think" is oversensitive — prefer "consider/evaluate".
- **Fix:** delete the script; keep at most a one-line "consider X and Y before deciding".

## MOD04 · Persona bloat · info
- **Detect:** multi-sentence role theater: "You are a world-class 10x engineer with 20 years of experience who never makes mistakes…".
- **Pin:** modern models get full value from one perspective-setting sentence; elaborate personas add tokens and occasionally style drift. De-emphasized in current Anthropic guidance.
- **Fix:** one sentence, only if perspective genuinely matters: "Answer as a security reviewer."

## MOD05 · Anti-laziness boilerplate · info
- **Detect:** "do not be lazy", "write the COMPLETE code", "do not omit anything", "no placeholders".
- **Pin:** on 4.6+ these cause overproduction (dumping whole files, over-long answers) more often than they prevent laziness.
- **Fix:** delete; if truncation was a real past problem, state the concrete requirement ("include the full modified function, not a diff").

## MOD06 · Technique stacking · info
- **Detect:** 2023-era scaffolding stacked without purpose: persona + "think step by step" + tip offers + emotional appeals + triple-redundant instructions in one prompt.
- **Pin:** current guidance is scope minimalism — "minimum complexity for the current task". Bloat measurably dilutes the instructions that matter.
- **Fix:** strip to: task, context, constraints, format, (examples if the pattern is hard to describe).

## Still-good techniques (do NOT flag these)
- Clear, explicit, specific instructions — still rule #1.
- Giving the *reason* for a constraint ("because the output feeds a parser") — models generalize from the why.
- 1–5 diverse examples in `<example>` tags when the pattern resists description — still the most reliable technique.
- XML/section tags for prompts mixing instructions with data — still recommended; unnecessary for simple prompts (don't flag their absence in a 2-line prompt).
- Positive format instruction; matching prompt style to desired output style.
- For agentic prompts: verification criteria, explicit action verbs, and parallel-tool-call encouragement.

## Changelog
- **v0.1 (2026-07-28):** initial rules, pinned to public Anthropic guidance through mid-2026 (prompting best practices, Claude 4.x migration notes, context-engineering post). Review when the next model generation ships.
