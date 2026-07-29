# Session retrospective — <session id, date>

**Session:** <N> prompts · <N> tool calls · <N> tool errors · <N> corrections · <N> rephrases
**Cost of friction:** ~<N> output tokens spent inside correction loops (rough lower bound).

## The counterfactual opening prompt

*The session eventually established: <the real goal, the constraints discovered midway, the verify command that emerged>. This opening prompt would have gotten there directly:*

> <counterfactual prompt in the agentic skeleton: Goal / Where / Constraints / Verify>

*What it would likely have saved: <grounded estimate — which correction runs (#a–#b) it would have prevented and why>.*

## Prompt-by-prompt

*Clean: prompts <list> — no findings.*

### Prompt #<n> — "<first ~60 chars…>"
- **Issues:** [<RULE> <severity>] <one line> — evidence: "<quote from the prompt>"
- **Impact:** <what it observably caused in this session, with prompt #refs>
- **Suggested improvement:** <the principle, one line>
- **Optimized prompt:**
  > <rewrite — minimal edit of the user's own words, [FILL IN: …] for anything you'd have to invent>

## Patterns (top 2)

1. **<pattern>** (<rule IDs>; prompts #<refs>) — <one sentence: the habit and what it cost this session>
2. **<pattern>** (<rule IDs>; prompts #<refs>) — <one sentence>

## Proposed artifacts

<only what the evidence supports — offered via AskUserQuestion, never auto-written>
