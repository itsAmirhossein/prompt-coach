# Domain overlay — Research & analysis

**Detect this domain:** deep research, investigation, summarization, competitive analysis, literature review.

## Optimization criteria
Scoped question, decision-linkage (what will the answer be used for?), source discipline, explicit depth/breadth trade-off, honesty about uncertainty.

## Common prompt problems in this domain
- The unanswerable-as-asked question (CLR04): "research the AI market" — no region, segment, time window, or use. Scope is the whole game in research prompts.
- No decision context (CON02): the same question needs a different answer for "deciding whether to enter this market" vs "writing a newsletter blurb". State what the answer feeds.
- No source/recency requirements (CON02): should it prefer primary sources? How should it treat claims it can't verify? Is 2024 data acceptable or is this a fast-moving topic?
- No uncertainty protocol (FMT01-adjacent): without "mark unverified claims", fluent synthesis and verified fact read identically — this is where hallucination risk concentrates. **Any research prompt without an uncertainty-marking instruction gets this finding.**
- Summarization without an audience or compression target (CLR02): "summarize this paper" → for whom, at what length, preserving what (methods? results? limitations?).

## Recommended structure
```
Question: one sentence, scoped (segment, region, time window).
Purpose: the decision or artifact this feeds.
Depth: [quick orientation | thorough with sources | exhaustive]
Source rules: recency floor, source preferences, how to treat conflicting claims.
Uncertainty: mark anything unverified; distinguish evidence from inference.
Format: [memo / table of options / annotated bibliography], target length.
```
