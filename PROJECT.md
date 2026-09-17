# Hermes Factory Test v4 — Project Definition

## Goal
Small calculator REST API used to validate multi-agent orchestration

## Success criteria
- [ ] Define measurable outcomes.
- [ ] Define MVP scope.
- [ ] Define testing/verification requirements.
- [ ] Define release/deployment expectations.

## Verification contract
- `./scripts/verify.sh` is the canonical local/CI verification entrypoint.
- The template starts with `HERMES_VERIFY_PLACEHOLDER`; the first implementation task must replace it with real project-specific verification.
- Pull requests are not reviewable until GitHub Actions `project-verification` passes on the exact PR HEAD SHA.

## Constraints
- Public GitHub repository.
- No secrets/private data committed.
- Behavior changes require verification evidence tied to an exact commit SHA.
- Shared working-directory changes do not count as delivered until committed, pushed, and present in the PR.
