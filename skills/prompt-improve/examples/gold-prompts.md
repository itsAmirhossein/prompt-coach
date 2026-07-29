# Gold exemplars

Reference prompts for rewrites — one per type. Match their *shape and altitude*, not their words. Note what each does NOT do: no persona theater, no pressure caps, no step-by-step reasoning scripts, no restated instructions.

## Agentic session opener (SWE)

> Goal: `POST /api/orders` intermittently returns 500 under concurrent requests; make it reliable.
>
> Where: error from prod logs (pasted below); repro with `npm run test:load`. Suspect `src/orders/inventory.ts` — the stock check and decrement aren't atomic — but treat that as a hypothesis, not the diagnosis.
>
> ```
> TypeError: Cannot read properties of null (reading 'reserve')
>     at InventoryService.hold (src/orders/inventory.ts:84)
> ```
>
> Constraints: Postgres 14, no new dependencies; don't change the public API shape.
>
> Verify: `npm run test:load` passes 50 concurrent orders with no 500s; add a regression test for the race.

*Why it's good: observed symptom pasted verbatim, hypothesis labeled as hypothesis (CON03 avoided), scope bounded, done-condition executable (AGT01).*

## One-shot task prompt (writing)

> Write the announcement email for our SSO feature.
>
> Audience: IT admins at existing customers — technical, busy, skeptical of "enterprise-ready" claims.
> Goal: they click through to the setup guide.
> Voice — match this sample from our last release email: "You asked, we shipped. Connection pooling is live for all Team plans — no config changes needed. Here's what it does and what it costs you: nothing."
> Musts: mention SAML + OIDC support, link placeholder [SETUP_GUIDE]; no pricing commitments.
> Format: subject line + ~120-word body + one CTA button label.

*Why it's good: audience with attitude, one reader-action, voice by example not adjectives, must-nots stated, positive format spec.*

## Reusable template (support triage)

> You are a support triage assistant for Acme's help desk.
>
> Rules:
> - Classify each ticket into exactly one of: `billing`, `bug`, `how-to`, `account`, `other`. Prefer `bug` over `how-to` when the user reports unexpected behavior, because misrouted bugs cost SLA time.
> - Quote the sentence that determined your classification.
> - If the ticket mentions data loss or security, set `"escalate": true` regardless of category.
>
> Format: JSON only — `{"category": string, "evidence": string, "escalate": boolean}`.
>
> <example>
> Ticket: "I was charged twice this month and support hasn't answered."
> Output: {"category": "billing", "evidence": "I was charged twice this month", "escalate": false}
> </example>
>
> Ticket: <ticket>{{TICKET_TEXT}}</ticket>

*Why it's good: stable preamble before the volatile variable (EFF02), each rule checkable with a reason attached, example obeys the rules, delimited input, schema-first format.*
