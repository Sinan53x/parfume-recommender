# Repository Agent Rules

These rules constrain any coding agent operating in this repository.

## 1) Change Strategy

- Do not perform full-file rewrites.
- Use incremental diffs only (small, targeted edits).
- Preserve existing behavior unless the requested task requires change.
- Prefer minimal touch radius: edit only the files directly needed.

## 2) Scope Control

- Limit work strictly to the user-requested task.
- Do not add opportunistic refactors, dependency changes, or feature work.
- If a useful improvement is out of scope, propose it separately instead of implementing it.

## 3) Testing Requirement

- Any new logic must include tests in the same change.
- Any behavior change must update existing tests or add new ones.
- If tests cannot be run in the current environment, state that explicitly in the final report.

## 4) Architecture Compliance

- `architecture.md` is the source of truth for system structure and boundaries.
- Do not introduce changes that violate `architecture.md`.
- If `architecture.md` is missing, unclear, or conflicts with a request, pause and ask for clarification before making structural changes.

## 5) Diff Quality

- Keep commits/review diffs readable and reviewable.
- Avoid unrelated formatting churn.
- Document assumptions when requirements are ambiguous.
