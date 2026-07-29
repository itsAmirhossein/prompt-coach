# Type overlay — Reusable template / system prompt

**Detect this type:** a prompt meant to run many times with varying inputs — `{{variable}}` templates, system prompts, agent instructions, CI prompts.

## What "good" means
Stable under varied inputs, cache-friendly, and written at the **right altitude**: neither brittle if-else micro-rules that break on the first unanticipated input, nor vague platitudes ("be helpful and accurate") that constrain nothing. Rules should state the principle plus one concrete anchor.

## Rule adjustments
- MOD01 (prefill) is **strict** — templates are exactly where fossilized prefills hide, and they hard-fail on Claude 4.6+.
- EFF02 (cache-hostile ordering) is **active**: stable preamble (role, rules, examples) first; volatile content ({{variables}}, dates, per-run data) last. Getting this wrong forfeits prompt caching on every run.
- CON01 (contradiction) upgrades severity — a contradiction in a template is a *distribution* of inconsistent behavior across every run, not one bad answer.
- FMT01 upgrades to **error** when downstream code parses the output; specify the schema, and prefer structured outputs over prose instructions for JSON.
- CLR02 applies to rules, not outcomes: every instruction should be checkable against an output ("cite the source for each claim" — checkable; "be trustworthy" — not).
- Variables: every `{{variable}}` should be referenced by the instructions at least once; flag orphans. Wrap free-text user variables in delimiters/XML tags so injected content can't read as instructions.

## Additional checks
- **Example consistency:** few-shot examples must obey the stated rules — an example that violates a rule silently overrides it (examples beat instructions).
- **Right altitude test:** for each rule ask "would a new competent hire need this told once (keep), per-case (too low — generalize), or never (too high — cut)?"

## Recommended skeleton
```
[Stable — identical bytes every run, in this order:]
Role: one sentence.
Rules: the invariants, each checkable, each with a reason where non-obvious.
Format: output schema/shape.
Examples: 1–5 diverse, rule-obeying, in <example> tags.
[Volatile — last:]
Input variables, delimited: <user_input>{{input}}</user_input>
```
