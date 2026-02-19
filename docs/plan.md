# Milestone and Atomic Task Plan

Source documents reviewed:
- `docs/PRD.md`
- `docs/architecture.md`

Notes:
- Repository contains `docs/PRD.md` (uppercase), not `docs/prd.md`.
- Tasks are atomic and scoped to 1-3 files each.
- Logging and testing tasks are explicitly included in every milestone.

## M1 - Scraper + Normalized Dataset

Goal: crawl catalog, parse product data, normalize, and store.

1. Define perfume entity schema.
Files: `app/domain/models/perfume.py`

2. Add note normalization rules.
Files: `app/infrastructure/scraping/normalizers/notes_normalizer.py`

3. Add tag/family normalization rules.
Files: `app/infrastructure/scraping/normalizers/tags_normalizer.py`

4. Build listing-page parser.
Files: `app/infrastructure/scraping/parsers/listing_parser.py`

5. Build product-page parser (notes/description/tags/images).
Files: `app/infrastructure/scraping/parsers/product_parser.py`

6. Implement scrape HTTP client with retries/backoff.
Files: `app/infrastructure/scraping/client.py`

7. Add robots/rate-limit guard.
Files: `app/infrastructure/scraping/robots.py`

8. Create catalog schema + perfume repository.
Files: `app/infrastructure/persistence/sqlite/schema.sql`, `app/infrastructure/persistence/sqlite/perfume_repo_sqlite.py`

9. Orchestrate scrape pipeline.
Files: `app/application/pipelines/scrape_pipeline.py`

10. [LOG] Add structured scrape run logging contract.
Files: `app/config/logging.py`, `app/application/pipelines/scrape_pipeline.py`

11. [TEST] Parser tests (listing/product happy + fallback).
Files: `tests/unit/test_listing_parser.py`, `tests/unit/test_product_parser.py`

12. [TEST] Normalizer tests.
Files: `tests/unit/test_notes_normalizer.py`, `tests/unit/test_tags_normalizer.py`

13. [TEST] Pipeline integration test (success-rate metric + persistence).
Files: `tests/integration/test_scrape_pipeline.py`

## M2 - v1 Recommender + Explanations + API

Goal: hybrid ranking with explanations and minimal API surface.

1. Define user profile model.
Files: `app/domain/models/user_profile.py`

2. Implement note similarity feature.
Files: `app/infrastructure/recommendation/features/note_similarity.py`

3. Implement family match feature.
Files: `app/infrastructure/recommendation/features/family_match.py`

4. Implement similar-to-owned feature + owned penalty.
Files: `app/infrastructure/recommendation/features/owned_similarity.py`

5. Implement occasion/mood/strength rules.
Files: `app/infrastructure/recommendation/features/context_rules.py`

6. Add score weights registry.
Files: `app/infrastructure/recommendation/scoring/score_weights.py`

7. Add score trace structure.
Files: `app/infrastructure/recommendation/scoring/score_trace.py`

8. Implement hybrid scorer.
Files: `app/infrastructure/recommendation/scoring/hybrid_scorer.py`

9. Build explanation reason builder from trace.
Files: `app/infrastructure/recommendation/explain/reason_builder.py`

10. Wire recommendation service.
Files: `app/application/services/recommendation_service.py`

11. Add recommendation DTOs.
Files: `app/application/dto/recommendation_request.py`, `app/application/dto/recommendation_response.py`

12. Expose API routes/schemas (`GET /perfumes`, `POST /recommendations`).
Files: `app/api/routers/perfumes.py`, `app/api/routers/recommendations.py`, `app/api/schemas/recommendations.py`

13. [LOG] Add scoring debug logs (candidate count, component scores, top-N).
Files: `app/application/services/recommendation_service.py`, `app/config/logging.py`

14. [TEST] Scoring unit tests (cold start, boosts, penalties).
Files: `tests/unit/test_hybrid_scorer.py`

15. [TEST] Explanation unit tests (reasons align with top components).
Files: `tests/unit/test_reason_builder.py`

16. [TEST] API integration test for recommendation response contract.
Files: `tests/integration/test_recommendations_api.py`

## M3 - Feedback Loop + Personalization Signals

Goal: collect feedback events and apply lightweight personalization.

1. Define feedback event model.
Files: `app/domain/models/feedback_event.py`

2. Extend SQLite schema for feedback events.
Files: `app/infrastructure/persistence/sqlite/schema.sql`

3. Implement feedback repository.
Files: `app/infrastructure/persistence/sqlite/feedback_repo_sqlite.py`

4. Implement feedback service (click/like/dislike/purchase).
Files: `app/application/services/feedback_service.py`

5. Add feedback API router + schema.
Files: `app/api/routers/feedback.py`, `app/api/schemas/feedback.py`

6. Add profile-adjustment helper from feedback aggregates.
Files: `app/application/services/recommendation_service.py`, `app/application/services/feedback_service.py`

7. [LOG] Add feedback ingestion and aggregation logs.
Files: `app/application/services/feedback_service.py`, `app/config/logging.py`

8. [TEST] Repository integration test for event persistence.
Files: `tests/integration/test_feedback_repository.py`

9. [TEST] Feedback API integration test.
Files: `tests/integration/test_feedback_api.py`

10. [TEST] Personalization effect test (liked notes/families bias).
Files: `tests/unit/test_feedback_personalization.py`

## M4 - Embeddings + Optional Re-ranker (No Rewrite)

Goal: add semantic retrieval through existing interfaces without replacing v1.

1. Add embedding provider interface/adapter.
Files: `app/infrastructure/embeddings/provider.py`

2. Add embedding text builder (`name + description + notes + families`).
Files: `app/infrastructure/embeddings/text_builder.py`

3. Add vector index persistence abstraction.
Files: `app/infrastructure/embeddings/index_store.py`

4. Implement vector similarity engine (port-compatible).
Files: `app/infrastructure/embeddings/vector_similarity_engine.py`

5. Add optional reranker component.
Files: `app/infrastructure/embeddings/reranker.py`

6. Wire engine selection in config/dependencies.
Files: `app/config/settings.py`, `app/api/dependencies.py`

7. Update recommendation service to combine content + embedding scores (additive only).
Files: `app/application/services/recommendation_service.py`, `app/infrastructure/recommendation/scoring/score_weights.py`

8. Keep explanation compatibility via contribution metadata mapping.
Files: `app/infrastructure/recommendation/explain/reason_builder.py`, `app/infrastructure/recommendation/scoring/score_trace.py`

9. [LOG] Add embedding latency/index freshness/fallback logs.
Files: `app/application/services/recommendation_service.py`, `app/config/logging.py`

10. [TEST] Unit tests for vector engine contract.
Files: `tests/unit/test_vector_similarity_engine.py`

11. [TEST] Integration test: config switch content-only vs hybrid embedding mode.
Files: `tests/integration/test_recommendation_engine_switch.py`

12. [TEST] Regression test: v1 behavior remains correct when embeddings are disabled.
Files: `tests/integration/test_v1_compatibility.py`
