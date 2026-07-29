# Type overlay — One-shot task prompt

**Detect this type:** a self-contained request to a chat model (claude.ai, API single-turn): no repo access assumed, no tools, the answer comes back in one response.

## What "good" means
Everything needed is inline: task, context, constraints, output format. The prompt is judged as if the model knows nothing beyond it.

## Rule adjustments
- CTX01 (missing referent) is **strict** — there is no repo for the model to check; any referenced material must be in the prompt.
- CTX03 (pasted what could be pointed to) is **waived** — pasting is correct here.
- AGT01/AGT02 are **waived** (no agent).
- FMT01 upgrades to **error** when the output feeds a machine or a template.
- STR02 matters at length: documents first, question last.

## Recommended skeleton
Use only the sections the task needs — an empty section is bloat (MOD06):

```
[1 sentence: role/perspective, only if it matters]
Task: what you want, with an explicit action verb.
Context: the material — pasted, delimited (XML tags if mixed with instructions).
Constraints: the 2–5 things that must hold (versions, audience, boundaries, priority on conflict).
Format: the positive shape of the output.
[Examples: 1–3 in <example> tags, only if the pattern resists description]
```
