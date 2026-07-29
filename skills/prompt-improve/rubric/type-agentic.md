# Type overlay — Agentic session prompt (Claude Code)

**Detect this type:** a prompt to an agent with tool access and a repo — session openers and mid-session instructions in Claude Code or similar.

## What "good" means
The prompt **points at** context instead of containing it, states the goal and boundaries, and gives the agent a way to verify its own work. The repo, CLAUDE.md, and conversation carry the details; the prompt carries intent, constraints, and the done-condition.

## Rule adjustments
- CLR03 (no done-condition) upgrades to **error** for multi-step tasks — this is the highest-leverage fix in agentic prompting.
- AGT01 (no verification path) and AGT02 (unbounded blast radius) are **active** and central.
- CTX01 softens where the agent can find the referent: "fix the failing auth test" is fine *if* running the tests reveals it. Flag only when the agent cannot plausibly locate the referent.
- CTX03 (pasting what the agent could read) is **active** — paste error output and off-disk specs; point to files.
- FMT01 usually **waived** (the "output" is edits/commits), except for asks that end in a report or document.

## Mid-session steering (corrections)
A correction prompt is good when it *diagnoses*, not just rejects. "No, still wrong" forces the agent to re-guess; "the modal still flashes because the cleanup runs after the re-render — look at the effect ordering" redirects it. Flag pure-rejection corrections as CLR02 with this framing. After two failed corrections on the same issue, the documented best practice is a fresh start (`/clear`) with a grounded restart prompt — recommend it.

## Recommended skeleton (session opener)
```
Goal: what should be true when you're done (one or two sentences).
Where: entry points you already know — files, commands, the failing test, the error text pasted verbatim.
Constraints: what must not change; versions; conventions not in CLAUDE.md; scope boundary.
Verify: the command or observable behavior that proves it works.
[Optionally: "plan first before editing" for large or risky tasks]
```
