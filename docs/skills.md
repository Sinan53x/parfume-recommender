# Agent Skills and Constraints

This file defines mandatory project rules for AI agents working in this repository.
If a request conflicts with these rules, ask for explicit override before proceeding.

## 1) Python Coding Standards

- Use Python 3.11+ syntax and type hints for all new/changed functions.
- Prefer `dataclasses` or Pydantic schemas for structured data crossing module boundaries.
- Keep domain logic pure and side-effect free where possible.
- Separate concerns by layer:
  - `domain`: business models, enums, scoring contracts.
  - `application`: orchestration and use-cases.
  - `infrastructure`: IO, scraping, persistence, external services.
  - `api`: request/response mapping and validation only.
- Do not put scraping, SQL, or HTTP calls inside domain models.
- Keep functions small and deterministic; avoid hidden global state.
- Use descriptive names; avoid single-letter variables except loop indices.
- New config values must be centralized in settings/config modules.

## 2) Scraping Rules

- Always respect `robots.txt`.
- Use conservative rate limiting: default 1 request/second unless explicitly changed.
- Implement retries with exponential backoff for transient failures.
- Parse listing pages and detail pages separately; do not mix parser responsibilities.
- Preserve stable product identity via `perfume_id` derived from URL handle.
- Normalize notes/tags/families using shared normalizers before persistence.
- Prefer resilient selectors with fallbacks; never rely on one fragile selector path.
- Track scrape metrics: discovered URLs, successful parses, failed parses, skip reasons.
- Target acceptance: >= 98% products parsed with at least `name`, `url`, `notes_all`.
- Store raw HTML snapshots when debugging is enabled.

## 3) Scoring Rules

- Recommendation ranking must remain hybrid and explainable in v1.
- Final score must be composed from explicit components:
  - note similarity
  - family match
  - similar-to-owned signal
  - occasion/mood/strength adjustment
- Recommending already-owned perfumes must be penalized by default.
- Every score contribution must be traceable for explanation output.
- Weight constants must be centralized (single source of truth), not hardcoded across files.
- Any scoring change must preserve cold-start behavior (no purchases).
- Add/update tests whenever scoring formulas, weight defaults, or penalties change.
- v2 embedding score may be added only as an additive component; do not remove v1 signals.

## 4) Logging Rules

- Use structured logging (key-value fields), not ad-hoc prints.
- Include correlation/request IDs in API and recommendation flows where available.
- Required scrape logs:
  - run start/end
  - URL fetch status
  - parse failures with reason
  - overall success rate
- Required recommendation logs:
  - candidate count
  - top-N IDs and scores
  - score component summary
  - fallback paths triggered
- Never log secrets or sensitive user input verbatim.
- Log level policy:
  - `INFO`: lifecycle and high-level metrics
  - `WARNING`: recoverable parsing/scoring anomalies
  - `ERROR`: failed operations and data integrity issues
  - `DEBUG`: feature/score traces when explicitly enabled

## 5) Testing Rules

- Add tests for every non-trivial behavior change.
- Minimum required coverage per change:
  - unit tests for parsing/normalization/scoring logic
  - integration tests for repository + API contracts on critical paths
- Scoring tests must validate:
  - owned-item penalty
  - family/note boosts
  - cold-start recommendations
  - explanation reasons align with top score drivers
- Scraper tests must include selector fallback behavior and normalization correctness.
- Avoid brittle snapshot tests for dynamic score values unless justified.
- Do not merge changes that alter scoring behavior without test updates.

## 6) Refactor Restrictions

- Do not rewrite architecture layers in one step; prefer incremental refactors.
- Preserve public API contracts unless explicitly requested and versioned.
- Preserve repository and port interfaces (`similarity_engine`, `ranker`, etc.) to keep v2 pluggable.
- Do not couple embeddings module directly into API handlers or domain models.
- Do not delete score trace/explanation pathways during optimization.
- No broad renames/moves without a clear migration path and updated tests.
- Keep data model compatibility for core fields in PRD (`perfume_id`, notes, families, events).
- If refactor risk is high, propose phased plan before making invasive changes.

## 7) Change Control

- For any meaningful logic change, include:
  - what changed
  - why it changed
  - expected behavioral impact
  - tests added/updated
- If requirement ambiguity exists, prefer PRD-aligned behavior and note assumptions explicitly.
