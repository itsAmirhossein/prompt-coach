# Prompt Coach — Design Document

*Design date: 2026-07-28. Target platform: Claude Code plugin (skills + hooks + slash commands), with the core skill portable to claude.ai.*

---

## 0. Verdict up front

The idea is validated but over-scoped. Research across ~40 tools/papers and the Claude Code ecosystem shows:

1. **The niche exists and is not solved.** ~10 community prompt-improver hooks/skills exist for Claude Code. The category leader (severity1/claude-code-prompt-improver, 1.8k★) deliberately *hides* its improvements — it silently clarifies vague prompts and teaches nothing. Nobody with traction combines **visible critique + rewrite + rationale** with **per-conversation retrospectives**. awesome-claude-code (51k★) lists zero prompt-improver or retrospective entries.
2. **Standalone prompt-rewriter products die** (PromptPerfect shutting down 2026-09, Humanloop dead, Helicone in maintenance, prompttools wound down). Embedded ones live (Braintrust Loop, LangSmith Canvas, Langfuse's Claude Code skill). A workflow-embedded Claude Code plugin is the right form factor; a platform is the wrong one.
3. **Half the spec should be cut or reshaped**: the always-on "review every prompt and ask" mode as specified would kill adoption (latency + interruption fatigue — documented 60–100s cost in a prior community attempt); the seven domain modes are over-engineered relative to what matters (prompt *type* matters more than domain); numeric prompt scoring without ground truth is false precision; and the collaboration/analytics wishlist is a dying SaaS category, not a plugin feature.
4. **A genuinely differentiating asset is available**: a rubric that is *current* for Claude 4.6+/Fable-era models. Most circulating prompt advice is 2023-era. Prefill is now a hard 400 error, ALL-CAPS pressure causes overtriggering, prescriptive chain-of-thought scripts are superseded by adaptive thinking — even Anthropic's own Console improver still emits deprecated prefills. A model-version-aware rubric beats every existing tool on correctness.

**Build**: a Claude Code plugin, "Prompt Coach", with three surfaces — `/improve` (on-demand critique + rewrite), `/retro` (session retrospective that produces durable artifacts), and a threshold-gated optional hook (intervenes only on genuinely broken prompts). Rubric and domain modes are data files, not code.

---

## 1. Improved product vision

### Original framing (implicit): "a tool that makes prompts better before execution."
### Improved framing: **"a coach that converts wasted sessions into durable assets."**

Three reframes, each backed by evidence:

**Reframe 1 — The unit of value is not the rewritten prompt; it is the durable artifact.**
A rewritten prompt is consumed once. What compounds: a reusable template, a line added to CLAUDE.md, a personal rule ("you never state a done-condition"), a changed habit. Every successful adjacent tool converges on this — Braintrust's doctrine is "failure → permanent eval case"; Anthropic's built-in `/insights` outputs ready-to-paste CLAUDE.md suggestions; Langfuse's skill writes the improved prompt back to a registry. The retrospective is therefore not a report generator; it is an **artifact factory**. Per-prompt rewriting is the top of the funnel, not the product.

**Reframe 2 — Prompt *type* is a more important axis than domain.**
The spec's seven domain modes miss the distinction that actually changes optimization strategy:

| Prompt type | What "good" means | Optimization strategy |
|---|---|---|
| **One-shot task prompt** (most claude.ai usage) | Self-contained: context, constraints, format all inline | Classic prompt engineering: structure, examples, format spec |
| **Agentic session opener** (Claude Code) | Points at context rather than containing it; states goal, constraints, and a verifiable done-condition | Grounding: does the repo/CLAUDE.md carry the context? Is success checkable? |
| **Mid-session steering** (corrections) | Precise diagnosis of what went wrong, not vibes ("no, cleaner") | Teach diagnosis; detect frustration loops; recommend `/clear` after repeated failure |
| **Reusable template / system prompt** | Stable under varied inputs; cache-friendly; right altitude | The only type where eval-backed optimization (DSPy/GEPA-style) ever pays off |

An agentic opener that pastes 200 lines of code the agent could read itself is a *bad* prompt; the same prompt sent to claude.ai chat is a *good* one. No existing tool makes this distinction. Domain (SWE, PM, marketing…) becomes a secondary overlay — auto-detected, user-overridable, defined as data.

**Reframe 3 — In agentic contexts, pre-execution rewriting has lower marginal value than the spec assumes, and retrospectives have higher.**
Modern agents can ask clarifying questions themselves; a vague prompt often self-corrects at the cost of a few turns. What the model *cannot* do is change the user's habits across sessions. The pre-execution path should therefore be reserved for prompts that will genuinely waste a session (ambiguous referent, contradiction, missing error text), while the coaching depth goes into the retrospective — which is also where the competitive gap is widest.

**Positioning statement:** *Local, vendor-neutral, visible prompt coaching for Claude Code. It explains what's weak, shows the fix, reviews your sessions, and turns what it finds into templates and rules you keep — instead of silently rewriting or scoring you with made-up numbers.*

Explicit non-goals: a prompt-management SaaS, team analytics dashboards, eval infrastructure, silent auto-rewriting.

---

## 2. Recommended architecture

### Form factor: Claude Code plugin (verified against the live plugin system)

```
prompt-coach/
├── .claude-plugin/plugin.json          # plugin manifest (name, version, components)
├── commands/
│   ├── improve.md                      # /improve [prompt|--last|--file f] [--mode m] [--deep]
│   ├── retro.md                        # /retro [--session id|--current|--last-n N]
│   ├── coach.md                        # /coach on|off|status|config  (always-on toggle)
│   ├── templatize.md                   # /templatize  (v1.1)
│   └── audit.md                        # /audit — CLAUDE.md & context-file lint  (v1.1)
├── skills/
│   ├── prompt-improve/
│   │   ├── SKILL.md                    # critique + rewrite procedure
│   │   ├── rubric/
│   │   │   ├── core.md                 # universal rules (the lint catalog, §below)
│   │   │   ├── model-claude-4x.md      # model-era rules, version-pinned
│   │   │   ├── type-oneshot.md         # prompt-type overlays
│   │   │   ├── type-agentic.md
│   │   │   ├── type-template.md
│   │   │   └── mode-swe.md, mode-research.md, mode-writing.md   # domain overlays
│   │   └── examples/                   # gold prompt exemplars per genre (metaprompt-style)
│   ├── prompt-retro/
│   │   ├── SKILL.md                    # transcript parsing + report + artifact generation
│   │   └── report-template.md
│   └── prompt-templatize/SKILL.md      # concrete prompt → {{variable}} template  (v1.1)
├── hooks/
│   ├── hooks.json                      # registers UserPromptSubmit hook
│   └── gate.sh                         # cheap two-stage gate (see below)
└── scripts/
    └── parse_transcript.py             # JSONL → clean, ordered user-prompt list + outcome signals
```

State (all local):
- `~/.claude/prompt-coach/config.json` — always-on toggle, mode override, thresholds, bypass prefix. The `/coach` command writes it; the hook reads it. This is how a slash command toggles hook behavior at runtime (the hook always fires but exits 0 instantly when disabled).
- `~/.claude/prompt-coach/profile.md` — learned user patterns, written by `/retro`, read by `/improve` and injected as context by the hook when triggered.
- `.claude/prompt-coach.md` (per project, git-committed) — team house rules: extra rubric rules, preferred prompt shapes. This is the entire "team standards" feature — a file in the repo, not a platform.

### The lint catalog (design center of the whole tool)

Findings are **categorical, severity-tagged, and identified** — like a linter — not numeric scores. This makes output consistent, testable against a golden set, cheap to gate on, and honest (LLM-judge research shows numeric prompt scores without ground truth are unstable vibes; atomic binary criteria with rationale-before-verdict is the literature-backed pattern).

| ID | Rule | Severity | Check type |
|---|---|---|---|
| CLR01 | Ambiguous referent ("fix it", "that thing") with no antecedent | error | deterministic-ish + model |
| CLR02 | Vague quantifiers/success criteria ("some tests", "make it better", "etc.") | warn | deterministic + model |
| CLR03 | No stated done-condition on a multi-step task | warn | model |
| CLR04 | Ambiguous scope (could mean 10-line or 1000-line change) | warn | model |
| CTX01 | References something the model can't see (an error, "the design doc") without pointing to it | error | model |
| CTX02 | Assumes private knowledge (internal names, prior conversations) | warn | model |
| CTX03 | Pastes content the agent could read itself (agentic mode only) | info | deterministic |
| CTX04 | Stale/irrelevant context bloat | info | model |
| CON01 | Internal contradiction between instructions | error | model |
| CON02 | Missing constraints likely to matter (versions, environment, boundaries, "don't touch X") | warn | model |
| CON03 | Over-constraint: prescribes the solution when the problem statement was wanted | info | model |
| FMT01 | No output format specified where one clearly matters | warn | model |
| STR01 | Wall of text with the actual instruction buried mid-paragraph | warn | deterministic + model |
| STR02 | Long data before instructions (long-context ordering) | info | deterministic |
| STR03 | Multiple unrelated asks fused into one prompt | warn | model |
| MOD01 | Prefill pattern (hard 400 error on Claude 4.6+) | error | deterministic |
| MOD02 | ALL-CAPS / "CRITICAL: YOU MUST" pressure language (causes overtriggering on 4.5+) | warn | deterministic |
| MOD03 | Prescriptive step-by-step CoT script (superseded by adaptive thinking) | info | model |
| MOD04 | Elaborate persona boilerplate (one sentence suffices on modern models) | info | model |
| MOD05 | Anti-laziness boilerplate ("do not be lazy", "always fully…") | info | deterministic |
| MOD06 | Technique stacking / prompt bloat (redundant scaffolding) | info | model |
| AGT01 | No verification criterion the agent could run (agentic mode) | warn | model |
| AGT02 | No scope bound on an open-ended agentic task | warn | model |
| EFF01 | Low-information redundancy (readable-compression candidate) | info | model |
| EFF02 | Cache-hostile structure in a reusable template (volatile content early) | info | model |

The MOD family is version-pinned data (`model-claude-4x.md`) with a changelog — advice staleness becomes a maintenance task on one file, and "model-migration linting" falls out for free.

### Always-on mode: the honest design

**Platform fact (verified):** a `UserPromptSubmit` hook **cannot replace the prompt text**. It can only (a) exit 0 and optionally inject additional context via stdout, or (b) exit 2 to block the prompt. The spec's flow — "rewrite, then ask which version to use" — is not directly implementable, and blocking every prompt for review would be intolerable. Design accordingly:

**Two-stage gate, silent by default:**
1. **Stage 1 (deterministic, <10ms):** `gate.sh` checks config toggle, bypass prefix (`raw:` or leading `!`), and cheap heuristics (length, MOD01/02/05 regexes, ambiguous-referent patterns, no-verb detection). From v1.1 it also runs the correction-loop detector for mid-session coaching (§3, item 11) — two consecutive corrective prompts trigger a `/clear`-and-restart recommendation instead of a lint. Overwhelming majority of prompts exit 0 silently here.
2. **Stage 2 (only if stage 1 trips, optional):** one Haiku call (~200 tokens) classifies severity. Below threshold → silent pass.
3. **On trigger:** exit 0 with injected context — a short instruction telling Claude: *"Before executing, this prompt has [CLR01: 'it' has no referent]. Ask one targeted clarifying question via AskUserQuestion (ground it in the repo — check the likely files first), or proceed if the codebase disambiguates it. Options must include 'proceed as written'."* The user experiences: occasionally, Claude asks one sharp, well-grounded question before running. That *is* the "choose original or improved" flow, implemented within platform constraints — and it borrows the two proven patterns from the field: fire-wide-cancel-cheap gating, and research-before-asking.

**Adoption guardrails:** auto-disable suggestion after 3 consecutive dismissals; per-session trigger cap (default 3); `error`-severity-only default threshold. Global enablement = installing the plugin at user level with `"coach": "on"` in config — hooks registered by a user-level plugin apply to every session, which satisfies the "enable globally" requirement with zero extra machinery.

**Rejected alternatives:** exit-2 blocking loops (prompt is erased; hostile UX); output styles (wrong tool — changes response style, not prompt handling); an agent-wrapper/middleware proxy (breaks the native UX, doubles cost, and severity1's data shows hook+skill suffices); CLAUDE.md instructions alone ("always critique my prompt first" — unreliable, pollutes every turn's context, and can't be toggled cleanly).

### Retrospective: transcript access (verified locally)

Sessions live at `~/.claude/projects/<munged-cwd>/<session-uuid>.jsonl`. Each line is a typed JSON entry; real user prompts are `type=="user"`, `isMeta` falsy, `isSidechain==false`, string content not starting with `<command-` or `<local-command-`. Entries carry `timestamp`, `promptId`, `parentUuid` (conversation tree), `cwd`, `gitBranch`. Crucially, the transcript also contains what happened *after* each prompt — assistant actions, tool errors, user corrections. `parse_transcript.py` extracts, per user prompt: the prompt, the following assistant activity summary, outcome signals (number of subsequent corrections, error loops, whether the user rephrased), and per-turn token usage from the assistant entries — the raw material for session-cost accounting. The critique is thereby **grounded in actual outcomes** — this is GEPA-style trace reflection with the session as the trajectory and the user's corrections as the feedback function, and it is what makes the retrospective more than generic advice.

### Model usage
- Hook gate: heuristics + optional Haiku (cost control; a hook that costs Fable-tier tokens per prompt is a non-starter).
- `/improve`, `/retro`: run in the main conversation with the session's model — for judge hygiene on before/after comparisons (`--deep`), evaluate both orders and call a flip a tie (position bias is severe and documented).

---

## 3. Feature list

### MVP (v1.0 — 2–4 weeks of focused work)
1. **`/improve`** — critique (lint findings with IDs, severity, rationale) + **two rewrite candidates**: *conservative* (minimal edit, intent-preserving) and *restructured* (full best-practice shape) — the GEPA insight that maintaining diverse candidates beats one greedy rewrite, and the user picking one is your feedback signal. Auto-detects prompt type + domain; `--mode` overrides. Shows a diff and a per-change rationale. Explicitly lists "what was wrong" (spec requirement) and "context you should add" (CTX findings).
2. **`/retro`** — parses the current or a chosen session; per-prompt findings in the spec's format (Issues / Impact / Suggested improvement / Optimized prompt); session-level analysis of recurring patterns; **proposed artifacts**: CLAUDE.md additions, a template if a prompt shape repeats, profile.md updates. Nothing is written without user confirmation. Two behaviors are committed core, not optional polish:
   - **Outcome-grounded critique** — every finding is anchored to what actually happened next in the transcript ("this prompt led to 3 correction rounds; the ambiguity that caused them was X"), never to abstract rules alone. This is the tool's single biggest quality differentiator; a retro that isn't outcome-grounded ships nothing.
   - **The counterfactual prompt** — the report identifies the turn where the session went sideways and synthesizes the opening prompt that would have avoided it. This is the report's centerpiece, placed above the per-prompt grades, because it is more motivating than any grade.
3. **Rubric v1** — full lint catalog above; overlays for 3 domains (SWE, research, writing/marketing) + 3 prompt types; `model-claude-4x.md`.
4. **Model-migration linting** — the MOD rule family surfaced as an explicit, named capability rather than a byproduct: every MOD finding cites the model generation that changed the rule ("prefill → hard 400 error since Claude 4.6"; "CAPS pressure → overtriggering since 4.5"; "prescriptive CoT scripts → superseded by adaptive thinking"). `/improve --target <model>` re-lints an existing prompt or template against a specific model version — the "will this 2023-era prompt still work?" check that no other tool offers, and the cheapest headline feature in the whole design since the rules already exist as data.
5. **`/coach on|off`** — the threshold-gated hook, stage 1 heuristics only (no Haiku dependency at MVP), error-severity threshold, bypass prefix, trigger cap.
6. **Golden test set** — ~50 prompts with hand-labeled expected findings; a regression harness (ironically, promptfoo-style) run before any rubric change. This is the answer to "who improves the improver."

### Advanced (v1.1–v1.5)

*Status: items 7–15 shipped in plugin v0.2.0 (2026-07-28). Notes: instruction induction (15) shipped inside `/templatize --from-examples`; the stage-2 gate (12) ships config-gated and off by default (`/coach config stage2 true`), implemented via a `claude -p` Haiku call with fail-open semantics; session cost accounting (10) was already wired in the MVP parser/retro.*
7. **`/templatize`** — concrete prompt → reusable `{{variable}}` template (the one good idea from Anthropic's retired experimental API; almost unserved in the ecosystem). Templates saved to a personal library with simple versioning (files + diffs — no registry).
8. **Profile learning** — `/retro` maintains `profile.md` (recurring habits, confirmed preferences); `/improve` and the hook consume it, so coaching sharpens over time. Deliberately scoped to *the user's prompting habits*, not CLAUDE.md auto-editing — that adjacent niche (claude-reflect et al.) is crowded and partially subsumed by the built-in `/insights`.
9. **CLAUDE.md audit** (`/audit`) — runs the rubric against CLAUDE.md and other context files (CLAUDE.local.md, rule files): bloat, internal contradictions, CAPS pressure, stale instructions referencing removed code, wrong altitude (brittle if-else rules or vague platitudes). Anthropic's own guidance: a bloated CLAUDE.md causes Claude to ignore your actual instructions. Reuses existing rule families (MOD, CON, STR, EFF) — cheap to build, high goodwill, and the natural companion to `/retro`'s "add this line to CLAUDE.md" artifacts, which should never be appended to an unaudited file. Run it automatically before offering CLAUDE.md additions.
10. **Session cost accounting** — `/retro` closes with a real number: token usage of correction loops and dead-end detours, read from the per-turn `usage` data already present in transcript assistant entries ("prompts #4–#7 were recovery from the ambiguity in #3: ~38k tokens, ~an hour of session budget"). Motivates behavior change with numbers that are real — the honest replacement for a fabricated quality score, and it makes the counterfactual prompt's value concrete.
11. **Mid-session coaching** — the hook's stage-1 heuristics gain a correction-loop detector: two consecutive corrective prompts (short, negation-led, adding no new information) trigger injected context recommending the documented best practice — `/clear` plus a fresh, grounded restart prompt, which Claude drafts from the session so far. This extends always-on mode from catching bad *prompts* to catching doomed *trajectories*, and it operationalizes Anthropic's own "/clear after 2 failed corrections" guidance, which nobody follows unprompted.
12. **Haiku stage-2 gate** — better precision for always-on mode.
13. **A/B compare** (`/improve --test`) — run original vs rewrite on a sample input, side-by-side, both-order judged. Instant evidence of value (the one thing PromptPerfect got right).
14. **Team house rules** — `.claude/prompt-coach.md` merged into the rubric; committed to the repo.
15. **Instruction induction** — "give me 2–3 input/output examples and I'll draft the prompt" (APE's core move, metric-free variant).

### Future / explicitly deferred
16. **Eval-backed template optimization** — for library templates only, once a template has accumulated failure cases (Braintrust's failure→eval-case pattern); GEPA/DSPy integration territory. Never for interactive prompts.
17. **Local trend analytics** — corrections-per-task and clarification-rounds trending over weeks, rendered locally. Not dashboards, not hosted.
18. **claude.ai portability** — the improve skill (minus hook and transcript access) as a plain skill for non-Code users.
19. **Cut entirely:** collaboration platform, shared prompt marketplace, hosted anything, numeric quality scores, automatic role/persona suggestion as a feature (modern models need one sentence of role; the rubric *flags* heavy personas instead — the spec had this backwards), standalone hallucination-risk detector (it is CTX01/CTX02/CON02 by another name).

### Triage of the spec's additional-features list

| Feature | Value | Complexity | Verdict |
|---|---|---|---|
| Prompt versioning | Med (templates only) | Low (files+git) | v1.1, templates only |
| Prompt history | High | Free (transcripts are the history) | MVP via `/retro` |
| Version comparison | Med | Med (judge hygiene needed) | v1.5 (`--test`) |
| Quality measurement/scoring | Med | High to do honestly | Categorical findings: MVP. Numeric scores: never |
| Hallucination-risk detection | Med | Low | Folded into rubric (CTX/CON) |
| Missing-constraint detection | High | Low | MVP (CON02) |
| Automatic context extraction | High | Med | MVP (CTX findings + research-before-asking in hook) |
| Reusable templates | High | Low | v1.1 |
| Team standards | Med | Low (a file) | v1.1 |
| Prompt libraries | Med | Low personal / High shared | Personal v1.1; shared: cut |
| Collaboration | Low for this form factor | Very high | Cut |
| Analytics | Low-med | Med | Future, local-only |
| Learning from corrections | High | Med | v1.1 (profile.md) |
| Domain patterns | Med | Low (data files) | MVP-lite (3 overlays) |
| Auto role/persona suggestion | Low (era-obsolete) | Low | Inverted: rubric flags heavy personas |
| Output-format recommendations | High | Low | MVP (FMT01 + rewrite includes format section) |

---

## 4. User experience flows

**Flow A — on-demand improve:** `/improve` (defaults to the user's last prompt) → findings list (`[CLR01 error] "it" has no referent — Claude will guess between the parser and the config loader`) → context suggestions ("attach the actual error text; state which module") → two candidates with diff + rationale → AskUserQuestion: use conservative / use restructured / keep original / refine further. Chosen prompt executes. Selection is logged as feedback.

**Flow B — retrospective:** `/retro` after a frustrating session → per-prompt review in the spec's format, but grounded in outcomes ("this prompt led to 3 correction rounds; the ambiguity that caused them was X") → session summary: quality assessment, top 2 recurring patterns (not ten — coaching that lists everything teaches nothing), the counterfactual opening prompt, and (v1.1) the cost line: "recovery from prompt #3's ambiguity consumed ~38k tokens" → offered artifacts: "Add these 2 lines to CLAUDE.md? Save this as a template? Update your profile?" Each individually confirmable.

**Flow C — always-on:** invisible on ~90% of prompts. On a genuinely broken one, Claude asks one grounded clarifying question with "proceed as written" always an option. `raw:` prefix bypasses. Three dismissals → "want me to turn coaching down?"

**Flow D — recurring-pattern capture:** `/retro` notices the same prompt shape three times → offers `/templatize` → next time, the user fills a template instead of improvising.

**Flow E — mid-session rescue (v1.1):** the user sends a second consecutive correction ("no, still wrong") → the hook's loop detector fires → instead of a third blind attempt, Claude responds with a diagnosis: "We're looping — the last two corrections added no new information. Recommend `/clear` and restarting with this prompt: [drafted restart prompt grounded in what the session has established]." The user gets a clean start with the accumulated context distilled, not lost.

**Flow F — context hygiene (v1.1):** `/retro` proposes a CLAUDE.md addition → `/audit` runs on CLAUDE.md first → "before adding, note: lines 12–15 contradict each other and line 30 references a deleted script; fix these first?" → additions land in a file that Claude will actually obey.

The teaching loop that makes this a coach rather than a linter: each intervention names the rule (CLR03), and the profile tracks per-rule frequency — when a rule stops firing for a user, say so ("you've stopped under-specifying done-conditions — nice"). Measurable improvement, no fake numbers.

---

## 5. Implementation approach

1. **Week 1:** rubric files + golden set first (they are the product; everything else is plumbing). Then `prompt-improve` skill + `/improve` command. Manual testing against the golden set.
2. **Week 2:** `parse_transcript.py` (pure Python, no deps) + `prompt-retro` skill. Test on your own real transcripts (there are 7 projects' worth locally).
3. **Week 3:** hook (`gate.sh` stage 1 only) + `/coach` toggle + config file. Dogfood for a week; tune trigger rate ruthlessly — the target is under ~1 intervention per 10 prompts.
4. **Week 4:** packaging (`.claude-plugin/plugin.json`), README, publish to a git marketplace; submit to awesome-claude-code and the official marketplace. Distribution is the hard part — every mechanism here is proven; nobody has broken out, which means the niche is winnable on quality + positioning but not automatic.

Engineering principles: rubric as data with a changelog (model-era rules will change); every model-facing behavior covered by the golden set; hook must never cost tokens on the silent path; nothing writes without confirmation; everything stays local.

---

## 6. Comparison with existing solutions

| Solution | What it does | Gap Prompt Coach fills |
|---|---|---|
| severity1/claude-code-prompt-improver (1.8k★) | Silent auto-clarification via hook + AskUserQuestion | Teaches nothing, shows nothing, no retro. We are the *visible, explanatory* counterpart — do not compete on silent clarification |
| Built-in `/insights` | Monthly usage retrospective → CLAUDE.md suggestions | Batch, config-focused; not per-conversation, not about the user's prompting skill |
| Prompt-sensei (116★), vibe-log (337★) | Closest analogs (coach+retro / score+reports) | Neither broke out; vibe-log is analytics-flavored, sensei shallow. Beat on rubric quality + outcome-grounded retro |
| Anthropic Console Prompt Improver | Template rewriter (CoT, XML, examples, prefill) | Template/{{variable}}-centric, credit-gated, still emits deprecated prefills; no conversation awareness |
| Langfuse Claude Code skill | Annotate traces → analyze → rewrite registry prompt | Requires Langfuse infra; production-app prompts, not the user's own prompting |
| linshenkx/prompt-optimizer (32.7k★) | Web/MCP rewriter, system/user modes | BYO-key chat app, not workflow-embedded, no session context |
| DSPy / GEPA / TextGrad | Metric-driven prompt search | Require eval sets + hundreds of calls; wrong tool for interactive prompts. Borrow the *moves* (trace reflection, candidate diversity, verbalized gradients) |
| promptfoo / DeepEval | Output evaluation against test cases | Test prompts via outputs; don't critique prompt text. Use the pattern internally for the golden set |
| claude-reflect cluster (1.3k★ + clones) | Corrections → CLAUDE.md updates | Crowded and partially subsumed by `/insights`; we target the user's habits, not the config file |

---

## 7. Ideas the spec did not consider

*Items marked ✦ were promoted into the committed roadmap (§3) in the 2026-07-28 revision — section retained to document what the original spec was missing.*

1. **Templatize** (concrete prompt → variable template) — nearly unserved since Anthropic retired its experimental endpoint. *(In roadmap from the start: §3 item 7.)*
2. ✦ **Model-migration linting** — "this prompt was written for 2023-era models; on Claude 4.6+ the prefill will 400 and the CAPS will overtrigger." Timely, unique, falls out of the MOD rules. → **MVP, §3 item 4.**
3. ✦ **Outcome-grounded retro** — critiques anchored to what actually happened next in the transcript, not abstract rules. The single biggest quality differentiator available. → **MVP core behavior of `/retro`, §3 item 2.**
4. ✦ **The counterfactual prompt** — "here is the opening prompt that would have avoided this session's failure." More motivating than per-prompt grades. → **MVP core behavior of `/retro`, §3 item 2.**
5. **Research-before-asking** — clarifying questions grounded in the actual repo state before being asked. *(Built into the hook design, §2.)*
6. **Two-candidate rewrites** (conservative/restructured) — hedges intent drift and generates preference signal. *(Built into `/improve`, §3 item 1.)*
7. ✦ **CLAUDE.md audit** — bloat/contradiction lint for CLAUDE.md itself (Anthropic: bloated CLAUDE.md causes instruction-ignoring). Adjacent, cheap, high goodwill. → **v1.1 as `/audit`, §3 item 9.**
8. **Cache-aware template structure** (EFF02) — stable prefix first; no tool offers readable token-efficiency advice (LLMLingua-style compression produces unmaintainable prompts and breaks prompt caching — the spec's "token optimization" goal is best served by *readable redundancy removal + cache-aware ordering*, not compression). *(In rubric as EFF02.)*
9. ✦ **Session-cost accounting** — "correction loops in this session ≈ N wasted tokens" — motivates with numbers that are real. → **v1.1 inside `/retro`, §3 item 10.**
10. **Right-altitude advice for system prompts/templates** — flag both brittle if-else over-specification and vague platitudes. *(In `type-template.md` overlay; also checked by `/audit`.)*
11. ✦ **Mid-session steering coaching** — detecting the 2-failed-corrections point and recommending `/clear` + a fresh grounded prompt (matches Anthropic's own best-practice guidance). → **v1.1 via the hook's loop detector, §3 item 11.**

---

## 8. Risks and challenges

1. **Platform risk (highest):** Anthropic extends `/insights` toward per-conversation coaching or ships native prompt critique. Mitigation: move fast, occupy the per-conversation + teaching slot, keep the rubric a maintained asset (which survives even if the delivery surface changes). Accept: this risk is structural.
2. **Always-on annoyance:** the documented failure mode of this category (60–100s latency in auto-mode attempts; interruption fatigue). Mitigation: silent-by-default gating, trigger caps, bypass, auto-deescalation, dogfooding target of <10% intervention rate. If in doubt, intervene less.
3. **Intent drift in rewrites:** an "improved" prompt that asks for something subtly different is worse than the original. Mitigation: conservative candidate always offered, diff + per-change rationale, never auto-apply, golden-set cases specifically for intent preservation.
4. **Advice staleness:** prompt-engineering truth changes per model generation; a stale rubric makes the tool actively harmful (cf. Anthropic's own improver emitting deprecated prefills). Mitigation: version-pinned rubric file with changelog; treat rubric updates as releases.
5. **Judge validity:** LLM judgment of "better prompt" without ground truth hits ~80% human agreement at best, with position/verbosity/self-family biases. Mitigation: categorical findings over scores; both-order pairwise with flip→tie for comparisons; conciseness as its own dimension so verbosity can't launder into quality.
6. **Privacy:** transcripts contain code, secrets, and business context. Everything local, nothing phones home, and team-shareable artifacts (templates, house rules) get a "review before committing" warning.
7. **Self-referential quality:** who lints the linter? The golden set + regression harness is the answer; without it, rubric edits are vibes.
8. **Crowded adjacent niches:** silent clarification (severity1) and CLAUDE.md auto-reflection (claude-reflect + 8 clones) are claimed. Do not drift into either.
9. **Distribution:** mechanisms are proven; nobody has broken out. Quality alone won't distribute — awesome-claude-code listing, marketplace submission, and a write-up demonstrating an outcome-grounded retro on a real session are the launch assets.
10. **Cost discipline:** any per-prompt token cost in the hook path compounds across every user prompt forever. Stage 1 must remain free; stage 2 opt-in.
