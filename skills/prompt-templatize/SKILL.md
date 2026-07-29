---
name: prompt-templatize
description: Turn a concrete prompt into a reusable {{variable}} template, induce a prompt from input/output examples, and manage the personal template library (list, use, save). Use when the user wants to templatize or save a reusable prompt, draft a prompt from examples, reuse a saved template, or invokes /templatize.
---

# Prompt Templatize

Convert prompts that get written repeatedly into templates that get filled. The library lives at `~/.claude/prompt-coach/templates/` — plain markdown files, no registry.

## Step 0 — Parse arguments

Supported: literal prompt text · `--last` (previous prompt via `<plugin_root>/scripts/parse_transcript.py --current --last-prompt`; plugin root = two directories above this SKILL.md) · `--file <path>` · `--from-examples` · `--list` · `--use <name>`. No arguments → ask what to templatize, or show `--list` if the library is non-empty.

## `--list`

Read each `*.md` in the library; show a table: name, description, variables, created. If empty, say so and explain the save flow in one line.

## `--use <name>`

1. Read the template (prefix match on name is fine; ambiguity → ask).
2. Collect values for each `{{VARIABLE}}` — one compact message listing all variables with their descriptions/examples from the frontmatter; let the user answer in free text. Use AskUserQuestion only when a variable has enumerable options.
3. Compose, show the filled prompt, then AskUserQuestion: **Run it now** / **Just give me the text** / **Edit first**.

## Templatize flow (text | --last | --file)

1. Read the rubric: `../prompt-improve/rubric/type-template.md`, plus `core.md` and `model-claude-4x.md`.
2. Separate the **stable intent** (task, rules, format — what would survive to next time) from the **volatile specifics** (names, dates, pasted content, this-time-only details). Each volatile specific becomes an `{{UPPER_SNAKE}}` variable.
3. Build the template using the type-template skeleton: stable preamble first, variables last, free-text variables wrapped in delimiters. Where the source prompt was missing something the template will always need (audience, format), add the section with a variable rather than inventing content.
4. **Self-lint** the produced template against the rubric (EFF02 ordering, checkable rules, conforming examples, no MOD violations). Fix violations before showing it — a templatizer that ships templates its own linter would flag is broken.
5. Show: the template, then a variables table (name → description → example value pulled from the source prompt).
6. Save: ask for a name (suggest a kebab-case one). If `<name>.md` exists, show a diff against it and AskUserQuestion: **Overwrite** / **Save as <name>-2** / **Cancel**. File format:

```markdown
---
name: <kebab-name>
description: <one line>
created: <date -u +%Y-%m-%d>
variables:
  - name: AUDIENCE
    description: who reads this
    example: IT admins at existing customers
---
<template body with {{VARIABLES}}>
```

## `--from-examples` (instruction induction)

For "I can show you what I want but can't describe it":

1. Collect 2–3 input → output pairs (ask if not provided). One pair is allowed but say the induced instruction will be weakly constrained.
2. Induce the transformation: what rule maps each input to its output? State the induced instruction explicitly — including edge behaviors visible in the examples (casing, ordering, what gets dropped).
3. Draft the template: induced instruction as rules + the user's pairs as `<example>` blocks + `{{INPUT}}` last.
4. **Verify against the evidence:** for each provided pair, check the drafted template would plausibly produce that output from that input; report any pair it wouldn't handle and what ambiguity remains ("both examples had unique keys — behavior on duplicates is unspecified; pick one:").
5. Same save flow as above.

## Hard rules

- Never save without confirmation. Never invent content for variables — that's what makes them variables. The template must pass the template rubric before it is shown.
