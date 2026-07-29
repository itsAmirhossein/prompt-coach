# Domain overlay — Software engineering

**Detect this domain:** coding tasks, debugging, architecture decisions, code review, system design.

## Optimization criteria
Reproducibility (can the model see what you see?), bounded scope, verifiability, environment fidelity.

## Common prompt problems in this domain
- Describing a bug from memory instead of pasting the actual error/stack trace (CTX01 — the #1 SWE prompt failure).
- Naming the suspected cause instead of the observed symptom (CON03): "fix the race in the pool" when the observation is "intermittent 500s under load" — if your diagnosis is wrong, the model debugs a fiction.
- Missing environment facts that change the answer (CON02): language/framework *versions*, runtime, OS, package manager.
- "Add tests" with no coverage intent (CLR02): which behaviors, which edge cases?
- Architecture questions with no constraints (CLR04): scale, team size, existing stack, migration tolerance — without these, you get a generic blog post.

## Domain-specific checks
- **Symptom vs diagnosis:** the prompt should always contain the *observation* (error text, failing test, wrong output vs expected). Diagnosis is optional and should be labeled as a hypothesis.
- **Expected vs actual:** debugging prompts state both. "It returns 3" is half a bug report; "returns 3, expected 5 because…" is whole.
- **Review asks name the axis:** "review this" → review for *what*? Correctness, security, performance, API design? Unscoped review requests get shallow passes over everything.

## Recommended structure (debugging, the canonical case)
```
Observed: [exact error/output, pasted verbatim]
Expected: [what should happen and why you believe that]
Repro: [command or steps; the failing test if there is one]
Environment: [versions that matter]
Hypothesis (optional, labeled): [your guess]
Constraint: [what the fix must not break]
```
