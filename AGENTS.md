# Project agent instructions

This is a public repo managed by Hermes Agent Engineering.

1. Read `PROJECT.md` before changing scope.
2. Treat this `AGENTS.md` as protected policy. Read it; do not modify it during normal task execution.
3. Never commit secrets, tokens, cookies, `.env` values, or private data.
4. Keep changes scoped to the active task.
5. Persistent project work uses `dir:<project-root>` or an explicit git worktree. Never use ephemeral scratch for deliverable work.
6. Do not implement directly on `main`; use a feature branch and GitHub PR.
7. The GitHub software PR HEAD SHA is the delivery candidate; never treat uncommitted shared-directory state as delivery evidence.
8. Every worker must inspect `git status --porcelain`; unexpected dirty state is a blocker, not something to silently absorb/reset.
9. Coder/Tester completion requires a clean workspace and `local HEAD == origin branch HEAD == PR HEAD`.
10. `./scripts/verify.sh` is the canonical verification entrypoint. The first implementation must replace `HERMES_VERIFY_PLACEHOLDER` with real project verification.
11. CI approval requires the `project-verification` check to pass for the exact candidate SHA; unrelated green checks are insufficient.
12. Tester changes are part of the candidate and must be committed/pushed before completion. Tester posts `HERMES-TEST` with exact `tested_sha`.
13. Reviewer is read-only. Reviewer approval requires clean state, `tested_sha == reviewed_sha == PR HEAD`, reproducible verification, and a `HERMES-REVIEW` PR attestation.
14. Reviewer outcomes are exactly `APPROVE`, `REQUEST_CHANGES`, or `BLOCK`; task acceptance criteria must never preselect approval.
15. Software merge occurs before evaluation. Finalizer must re-check current PR HEAD equals the tested/reviewed SHA immediately before merge.
16. Evaluator runs on synchronized `main` at the immutable merged SHA and never modifies the reviewed software PR.
17. Evaluation records are append-only in `metrics/model-evaluations.jsonl`, use actual evidence, and never guess unknown values.
18. Evaluator delivers metrics through a separate metrics-only PR; metrics finalization must confirm no software files changed.

## Project-specific architecture
Put project-specific architecture in assigned delivery-branch documentation changes or task comments, not by rewriting this protected policy file.

## Verification
`./scripts/verify.sh` is the single canonical project verification command used locally and by GitHub Actions.
`./scripts/check_candidate.sh` verifies clean workspace and local/remote/PR SHA identity for the software candidate.
