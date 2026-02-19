# Perfume Recommender Architecture Plan

Based on the product requirements in `docs/PRD.md`.

## 1) Folder Structure

```text
perfume_recommender/
  pyproject.toml
  README.md
  docs/
    PRD.md
    plan.md

  app/
    main.py
    config/
      settings.py
      logging.py

    domain/
      models/
        perfume.py
        user_profile.py
        recommendation.py
        feedback_event.py
      value_objects/
        note.py
        scent_family.py
        strength.py
      ports/
        perfume_repository.py
        feedback_repository.py
        feature_store.py
        similarity_engine.py
        ranker.py
        explainer.py

    application/
      services/
        catalog_refresh_service.py
        recommendation_service.py
        feedback_service.py
      dto/
        recommendation_request.py
        recommendation_response.py
      pipelines/
        scrape_pipeline.py
        feature_build_pipeline.py

    infrastructure/
      scraping/
        client.py
        robots.py
        parsers/
          listing_parser.py
          product_parser.py
        normalizers/
          notes_normalizer.py
          tags_normalizer.py
      persistence/
        sqlite/
          schema.sql
          perfume_repo_sqlite.py
          feedback_repo_sqlite.py
        parquet/
          export_catalog.py
      recommendation/
        features/
          note_similarity.py
          family_match.py
          owned_similarity.py
          context_rules.py
        scoring/
          hybrid_scorer.py
          score_weights.py
          score_trace.py
        explain/
          reason_builder.py
      embeddings/
        provider.py
        text_builder.py
        index_store.py
        vector_similarity_engine.py
        reranker.py

    api/
      routers/
        perfumes.py
        recommendations.py
        feedback.py
      schemas/
        perfumes.py
        recommendations.py
        feedback.py
      dependencies.py

  data/
    raw_html/
    staging/
    curated/
    sqlite/
  tests/
    unit/
    integration/
```

## 2) Module Responsibilities

- `infrastructure/scraping`: crawl listings/products, obey robots/rate limits, parse fields, keep raw HTML snapshots.
- `infrastructure/scraping/normalizers`: canonicalize notes/families/tags into normalized vocabulary.
- `domain/models`: stable business entities used everywhere (independent from DB/API).
- `persistence/sqlite`: catalog + feedback event storage and query implementations.
- `recommendation/features`: computes interpretable features (note overlap, family match, owned similarity, occasion/mood/strength alignment).
- `recommendation/scoring/hybrid_scorer`: weighted final score, penalties (already-owned), diversity knobs.
- `recommendation/explain`: converts score traces to user-facing reasons.
- `application/services/recommendation_service`: orchestrates retrieval, scoring, explanation, response assembly.
- `api/routers`: FastAPI endpoints `GET /perfumes`, `POST /recommendations`, `POST /feedback`.
- `infrastructure/embeddings`: future semantic retrieval + optional reranking behind interfaces.
- `application/pipelines`: reproducible flow: scrape -> normalize -> feature build.

## 3) Data Flow

1. `scrape_pipeline` fetches listing/product pages and saves raw + parsed records.
2. Normalizers convert noisy text to canonical notes/families and write curated catalog.
3. Feature pipeline precomputes static catalog features (note sets, family vectors, strength heuristics).
4. API request hits `recommendation_service` with `user_profile`.
5. Service retrieves candidate perfumes from repository.
6. Hybrid scorer computes feature contributions and total score.
7. Explanation layer reads `score_trace` and emits reasons/matched fields.
8. API returns ranked items with `score`, `reasons`, `matched_notes`, `matched_families`, `similar_to_owned`.
9. Feedback endpoint stores click/like/dislike/purchase events with context.
10. Periodic job updates profile priors and tuning stats from feedback history.

## 4) v2 Embeddings Without Rewrite

- Keep `domain/ports/similarity_engine.py` and `domain/ports/ranker.py` as stable contracts.
- v1 uses lexical/content implementation (`note/family/owned` feature engines).
- v2 adds `vector_similarity_engine` + optional `reranker` implementing same ports.
- `recommendation_service` depends only on ports, so switching is config-driven, not architectural rewrite.
- Explanation stays intact by requiring embedding engines to return contribution metadata (for reason generation).
- Hybrid mode in v2: `final_score = w1*content_score + w2*embedding_score + w3*reranker_score`, keeping existing v1 features and feedback loop usable.
