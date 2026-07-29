# Project instructions

<!-- Test fixture for the /audit golden run. Planted defects are annotated in
     tests/README.md §3 — do not "fix" this file; the audit skill is graded
     against it. -->

## Setup

Always use npm for everything in this repo. Run `npm install` before anything else.

This project uses pnpm workspaces — install dependencies with `pnpm install`.

## Project structure

- src/ — application code
- src/components/ — React components
- src/utils/ — helpers
- tests/ — test files
- package.json — dependencies: react, react-dom, express, lodash, axios

## Rules

- IMPORTANT: You MUST NEVER commit directly to main. ALWAYS use a branch. THIS IS CRITICAL.
- Write clean, high-quality, maintainable code at all times.
- Be careful with the database.
- After every single file edit, run `scripts/format_all.sh` before doing anything else.
- Use 2-space indentation in .ts files, except in src/legacy/ where it is 4 spaces, except for the files that were migrated after March which use 2, except vendor-patched ones.
- Deploy with `scripts/deploy_old.sh --env prod`.
- Never commit directly to main; always work on a feature branch.

## Notes

Do not be lazy when implementing features. Write the complete code.
