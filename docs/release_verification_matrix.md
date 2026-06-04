# Release Verification Matrix

This matrix maps the release-candidate checklist to concrete evidence. It is
intended for merge review and demo freeze decisions: a checklist item is not
considered credible unless it is backed by a named test, script step, runtime
check, or documented manual boundary.

Run the full gate from the repository root:

```bash
PYTHON_BIN=python scripts/release-check.sh
```

Use the active virtualenv Python for `PYTHON_BIN` when running locally.

## Required Gate

| Release script label | Evidence |
| --- | --- |
| Python test suite | `scripts/release-check.sh` runs `python -m pytest -q`. |
| Retrieval quality evaluation | `scripts/release-check.sh` runs `scripts/evaluate-retrieval.py` against `tests/fixtures/retrieval_eval_cases.json`. |
| Frontend TypeScript/Vite build | `scripts/release-check.sh` runs `npm run build` in `frontend/`. |
| Docker stack rebuild | `scripts/release-check.sh` runs `docker compose up -d --build`. |
| Runtime frontend asset assertion | `frontend/scripts/assert-runtime-assets-current.mjs` compares served nginx assets with the rebuilt frontend image. |
| Browser E2E suite | `scripts/release-check.sh` runs `npm run e2e`. |
| E2E artifact cleanup | `npm run e2e:cleanup` removes Playwright-created users, workflows, and related artifacts after the browser suite. |
| E2E residue assertion | `assert_e2e_residue_clean` verifies zero Playwright-marked users and workflows remain in Postgres. |
| E2E local report cleanup | `npm run e2e:cleanup:local` removes successful-run Playwright reports and traces from the local workspace. |
| Git whitespace/conflict-marker hygiene | `scripts/release-check.sh` runs `git diff --check` and `git diff --cached --check`. |

## API And Auth

| Claim | Evidence |
| --- | --- |
| FastAPI app imports and registers the documented `/api/v1` route surface | `tests/test_api.py::test_api_contract_doc_covers_current_route_surface`. |
| `/api/v1` routes use `{data, error}` envelopes | `tests/test_api.py::test_api_v1_route_handlers_use_response_envelopes` and `tests/test_api.py::test_public_api_success_and_error_envelope_contracts`. |
| `GET /health` remains raw liveness JSON | `tests/test_api.py::test_health_route_is_raw_liveness_probe`. |
| Protected routes require backend sessions | `tests/test_api.py::test_private_api_routes_have_auth_dependency` and `tests/test_api.py::test_api_routes_require_session_envelope`. |
| Errors do not leak stack traces, raw payloads, or secrets | `tests/test_api.py::test_unhandled_api_errors_do_not_expose_internal_exception_types`, `tests/test_api.py::test_request_validation_errors_do_not_echo_payload_input`, and runtime readiness sanitization tests. |
| Runtime diagnostics expose sanitized configuration and readiness checks | `tests/test_api.py::test_runtime_config_exposes_sanitized_operational_settings`, `tests/test_config.py::test_postgres_database_url_must_be_supported`, `tests/test_config.py::test_postgres_database_url_supported_values_are_accepted`, `tests/test_config.py::test_database_url_fallback_is_validated`, `tests/test_config.py::test_redis_url_must_be_a_supported_redis_url`, `tests/test_api.py::test_runtime_readiness_returns_sanitized_operational_checks`, `tests/test_api.py::test_runtime_readiness_session_cache_errors_when_redis_is_unreachable`, `tests/test_auth_service.py::test_redis_session_cache_strict_mode_raises_when_redis_is_unavailable`, `tests/test_api.py::test_auth_dependency_failures_return_service_unavailable_envelope`, `tests/test_api.py::test_runtime_readiness_requires_trusted_schema_inventory`, `tests/test_api.py::test_runtime_readiness_requires_retrieval_sources`, and runtime failure sanitization tests. |
| API, demo, and testing docs cover current contracts and workflows | `tests/test_api.py::test_api_contract_doc_covers_current_route_surface` and `tests/test_repo_hygiene.py::test_release_docs_cover_demo_flow_and_testing_strategy`. |
| OAuth sessions use HTTP-only cookies and no bearer token by default | `tests/test_api.py::test_auth_callback_sets_and_logout_clears_cookie`, `tests/test_api.py::test_auth_callback_can_return_bearer_token_when_requested`, and `tests/test_frontend_architecture.py::test_frontend_auth_callback_contract_does_not_model_bearer_token`. |
| Auth/session responses are not cacheable | `tests/test_api.py::test_auth_url_and_session_responses_are_not_cacheable`. |
| Cookie-authenticated writes require trusted origin context | `tests/test_api.py::test_cookie_authenticated_writes_require_trusted_origin` and `tests/test_frontend_architecture.py::test_playwright_cookie_authenticated_posts_send_origin_header`. |

## Persistence And Isolation

| Claim | Evidence |
| --- | --- |
| Postgres is the production-like default while SQLite and memory remain explicit alternatives | `tests/test_config.py::test_env_example_is_secret_safe_and_loadable`, `tests/test_config.py::test_storage_backend_supported_values_are_accepted`, and `tests/test_docker_runtime_config.py::test_compose_runtime_uses_postgres_redis_and_persistent_app_data`. |
| Postgres migrations are ordered and complete | `tests/test_postgres_migrations.py`. |
| Postgres workflow state survives restart | `tests/test_postgres_storage_optional.py::test_postgres_workflow_restart_resume`. |
| SQLite fallback survives restart | `tests/test_sqlite_storage.py::test_sqlite_workflow_restart_resume_preserves_events` and `tests/test_sqlite_storage.py::test_sqlite_auth_repository_persists_and_revokes_sessions`. |
| Artifact refs cannot escape configured roots | `tests/test_postgres_storage_optional.py::test_postgres_dataset_store_rejects_file_refs_outside_artifact_roots` and `tests/test_sqlite_storage.py::test_sqlite_dataset_store_rejects_file_refs_outside_artifact_roots`. |
| Public payloads redact local artifact refs | `tests/test_api.py::test_api_redacts_local_file_artifact_refs_from_public_payloads`. |
| Output and input artifact hashes are verified | `tests/test_workflow_service.py::test_workflow_output_read_rejects_corrupted_artifact_content`, `tests/test_workflow_service.py::test_review_resume_rejects_corrupted_input_artifact_content`, and matching API tests. |
| Workflow ownership scopes user data | `tests/test_api.py::test_api_workflows_are_scoped_to_authenticated_user`, `tests/test_workflow_service.py::test_workflow_service_scopes_queries_reviews_events_and_output_by_owner`, and `tests/test_summary_storage.py::test_summary_and_stats_can_filter_by_owner`. |

## Healthcare Workflow Scope

| Claim | Evidence |
| --- | --- |
| CSV, JSON, and YAML parse/convert/validate deterministically | `tests/test_workflow_service.py`, `tests/test_api.py::test_api_direct_convert_validate_fhir_ocr_and_error`, and parser/converter cases in the Python suite. |
| CSV malformed rows and source-row evidence are surfaced | CSV parser and API workflow tests in `tests/test_workflow_service.py` and `tests/test_api.py`. |
| Conversion metadata includes formats, row counts, hashes, lossiness, warnings, and actions | `tests/test_api.py::test_api_direct_convert_validate_fhir_ocr_and_error` and workflow approval/output tests. |
| Validation flags missing fields, dates, units, PHI-like fields, prompt-injection patterns, and type problems | `tests/test_workflow_service.py` and `tests/test_api.py::test_api_workflow_review_roundtrip`. |
| FHIR-like profiling emits profile evidence and handoff context | `tests/test_workflow_service.py::test_fhir_like_workflow_adds_profile_evidence_and_handoff_context` and `tests/test_api.py::test_api_direct_convert_validate_fhir_ocr_and_error`. |
| OCR evidence normalization gates low-confidence fields | `tests/test_api.py::test_api_direct_convert_validate_fhir_ocr_and_error` and `tests/test_api.py::test_fhir_and_ocr_routes_use_medical_evidence_service_dependency`. |
| Graph-NER/RAG emits an auditable GraphRAG-lite handoff, not clinical decision support | `docs/retrieval_module_v0.md`, `tests/test_retrieval.py::test_retrieval_service_adds_graph_context`, and API retrieval handoff assertions in the Python suite. |

## Retrieval

| Claim | Evidence |
| --- | --- |
| Retrieval uses trusted healthcare knowledge inventory | `tests/test_retrieval.py::test_static_retrieval_ranks_healthcare_evidence_with_trace` and retrieval endpoint tests. |
| Retrieval expands healthcare queries through deterministic, auditable standard-aware rules loaded from trusted data | `tests/test_retrieval.py::test_query_analysis_expands_clinical_standard_terms`, `tests/test_retrieval.py::test_query_analysis_uses_data_driven_expansion_rules`, `tests/test_retrieval.py::test_static_retrieval_ranks_healthcare_evidence_with_trace`, `knowledge/retrieval/query_expansion_rules.json`, and `docs/retrieval_module_v0.md`. |
| Retrieval query rewrites are explainable | `tests/test_retrieval.py::test_query_variants_include_fields_schema_and_format`, `tests/test_retrieval.py::test_query_analysis_expands_clinical_standard_terms`, `tests/test_frontend_architecture.py::test_retrieval_page_surfaces_runtime_ranking_stack`, `docs/retrieval_module_v0.md`, and `trace.query_variant_details`. |
| Retrieval query analysis uses data-driven controlled-vocabulary seed concepts | `tests/test_retrieval.py::test_query_analysis_uses_data_driven_medical_concepts`, `tests/test_retrieval.py::test_query_analysis_uses_expanded_lab_seed_concepts`, `tests/test_retrieval.py::test_query_analysis_normalizes_medication_concept_from_registry`, `tests/test_retrieval.py::test_query_analysis_uses_mesh_seed_concepts_in_pubmed_hint`, `tests/test_retrieval.py::test_static_retrieval_lists_medical_concept_registry_source`, `knowledge/terminologies/medical_concepts.json`, and Retrieval UI concept candidate rendering in `frontend/src/features/retrieval/retrieval-page.tsx`. |
| Retrieval inventory includes curated official healthcare source and ingestion knowledge | `tests/test_retrieval.py::test_static_retrieval_lists_expanded_healthcare_knowledge_sources`, `tests/test_retrieval.py::test_knowledge_json_sources_are_valid`, `knowledge/source_catalog/official_healthcare_sources.json`, `knowledge/terminologies/fhir_search_parameters.json`, `knowledge/retrieval/filter_suggestion_rules.json`, `knowledge/retrieval/ranking_boost_rules.json`, `knowledge/corpus/clinical_data_standards_map.md`, `knowledge/corpus/medical_search_playbook.md`, and `knowledge/corpus/public_dataset_ingestion_plan.md`. |
| Retrieval index consistency is explicitly checkable | `tests/test_retrieval.py::test_static_retrieval_integrity_report_matches_seeded_knowledge`, `tests/test_retrieval.py::test_static_retrieval_integrity_report_detects_stale_indexed_source`, `tests/test_api.py::test_retrieval_integrity_route_delegates_to_workflow_service`, and `GET /api/v1/retrieval/integrity`. |
| Retrieval query analysis suggests metadata filters without silently applying them | `tests/test_retrieval.py::test_query_analysis_expands_clinical_standard_terms`, `tests/test_retrieval.py::test_query_analysis_marks_applied_filter_suggestions`, `tests/test_retrieval.py::test_query_analysis_uses_data_driven_filter_suggestion_rules`, `knowledge/retrieval/filter_suggestion_rules.json`, and Retrieval UI suggestion rendering in `frontend/src/features/retrieval/retrieval-page.tsx`. |
| Retrieval query analysis reports query-quality diagnostics | `tests/test_retrieval.py::test_query_analysis_reports_quality_diagnostics`, `tests/test_retrieval.py::test_query_analysis_reports_conflicting_standard_filter`, `tests/test_retrieval.py::test_query_analysis_detects_medication_and_analytics_routes`, `docs/retrieval_module_v0.md`, and Retrieval UI diagnostic rendering in `frontend/src/features/retrieval/retrieval-page.tsx`. |
| Retrieval query analysis exposes deterministic medical search syntax hints | `tests/test_retrieval.py::test_query_analysis_builds_medical_search_hints`, `tests/test_retrieval.py::test_query_analysis_uses_data_driven_search_hint_targets`, `tests/test_retrieval.py::test_query_analysis_builds_clinicaltrials_gov_hint`, `tests/test_retrieval.py::test_query_analysis_builds_openfda_drug_hints`, `tests/test_retrieval.py::test_static_retrieval_ranks_pubmed_mesh_search_evidence`, `tests/test_retrieval.py::test_static_retrieval_ranks_external_medical_search_evidence`, `knowledge/retrieval/search_hint_targets.json`, `docs/retrieval_module_v0.md`, and Retrieval UI search hint rendering in `frontend/src/features/retrieval/retrieval-page.tsx`. |
| Retrieval hits expose deterministic extractive snippets for operator review | `tests/test_retrieval.py::test_retrieval_snippet_extracts_query_focused_segment`, `tests/test_retrieval.py::test_static_retrieval_ranks_healthcare_evidence_with_trace`, and Retrieval UI snippet rendering in `frontend/src/features/retrieval/retrieval-page.tsx`. |
| Retrieval ranking boost policy is data-driven and observable | `tests/test_retrieval.py::test_rank_chunks_uses_data_driven_ranking_boost_rules`, `tests/test_retrieval.py::test_static_retrieval_lists_expanded_healthcare_knowledge_sources`, `knowledge/retrieval/ranking_boost_rules.json`, `docs/retrieval_module_v0.md`, `hits[].source_locator.ranking_boosts`, and `hits[].source_locator.ranking_boost_rules`. |
| Retrieval hit scores are explainable by component | `tests/test_retrieval.py::test_rank_chunks_uses_data_driven_ranking_boost_rules`, `tests/test_retrieval.py::test_second_stage_reranker_refines_ranked_candidates`, `tests/test_frontend_architecture.py::test_retrieval_page_surfaces_runtime_ranking_stack`, `docs/retrieval_module_v0.md`, and `hits[].score_components`. |
| Retrieval packages expose selected-hit facets for operator scanability | `tests/test_retrieval.py::test_static_retrieval_ranks_healthcare_evidence_with_trace`, `tests/test_retrieval.py::test_static_retrieval_filters_by_source_type`, and Retrieval UI facet rendering in `frontend/src/features/retrieval/retrieval-page.tsx`. |
| Retrieval diversity selection is auditable per selected hit | `tests/test_retrieval.py::test_retrieval_diversity_selection_reduces_redundant_sources`, `tests/test_frontend_architecture.py::test_retrieval_page_surfaces_runtime_ranking_stack`, `docs/retrieval_module_v0.md`, and `handoff_context.diversity.selected_hits`. |
| Retrieval packages expose actionable expected-standard coverage diagnostics | `tests/test_retrieval.py::test_retrieval_coverage_reports_missing_expected_standard`, `tests/test_retrieval.py::test_static_retrieval_ranks_healthcare_evidence_with_trace`, `docs/retrieval_module_v0.md`, `coverage.standard_system[].suggested_action`, `coverage.standard_system[].suggested_filter`, and Retrieval UI coverage rendering in `frontend/src/features/retrieval/retrieval-page.tsx`. |
| Retrieval packages expose package-level quality signals | `tests/test_retrieval.py::test_retrieval_quality_signals_flag_missing_standard_coverage`, `tests/test_frontend_architecture.py::test_retrieval_page_surfaces_runtime_ranking_stack`, `docs/retrieval_module_v0.md`, `quality_signals[]`, and Retrieval UI quality checklist rendering in `frontend/src/features/retrieval/retrieval-page.tsx`. |
| Retrieval operators can compare recent search runs | `tests/test_frontend_architecture.py::test_retrieval_page_surfaces_runtime_ranking_stack`, `docs/frontend_architecture.md`, and Retrieval UI in-session run history, selectable baseline, explicit relevance judgments, judgment-aware metrics, overlap/churn metrics, delta, rank movement, copyable JSON report, and evidence add/remove/retain rendering in `frontend/src/features/retrieval/retrieval-page.tsx`. |
| Retrieval has deterministic quality gates for known healthcare evidence queries | `tests/test_retrieval.py::test_retrieval_eval_fixture_passes_static_repository`, `tests/test_retrieval.py::test_retrieval_eval_cli_outputs_json_summary`, `tests/fixtures/retrieval_eval_cases.json`, and `scripts/evaluate-retrieval.py`. |
| Postgres mode uses full-text search, configured vector scoring, independent lexical/vector candidate pools, fusion, and reranking | `tests/test_postgres_migrations.py::test_retrieval_v0_migration_has_search_tables_and_pgvector_fallback`, `tests/test_postgres_migrations.py::test_semantic_embedding_vector_migration_uses_384_dimensions`, `tests/test_postgres_storage_optional.py::test_postgres_retrieval_sets_hnsw_ef_search_for_vector_queries`, `tests/test_postgres_storage_optional.py::test_postgres_retrieval_uses_lexical_pool_when_vector_column_mismatches`, `tests/test_retrieval.py::test_huggingface_embedding_provider_uses_query_and_document_methods`, and retrieval-backed workflow tests. |
| Trusted local corpus reindexing is explicit and authenticated | `tests/test_retrieval.py::test_static_retrieval_reindex_adds_local_corpus`, `tests/test_retrieval.py::test_local_corpus_loader_chunks_trusted_healthcare_docs`, and `tests/test_api.py::test_retrieval_reindex_route_delegates_to_workflow_service`. |
| Retrieval trace exposes strategy, variants, filters, candidate counts, selected IDs, safety flags, and warnings | `tests/test_retrieval.py`, `tests/test_api.py::test_api_direct_convert_validate_fhir_ocr_and_error`, and browser Evidence-tab checks. |
| Runtime readiness probes retrieval through the same service path used by workflows | `tests/test_api.py::test_runtime_readiness_returns_sanitized_operational_checks`, `tests/test_api.py::test_runtime_readiness_requires_trusted_schema_inventory`, and `tests/test_api.py::test_runtime_readiness_requires_retrieval_sources`. |
| Assistant and MCP tools stay allowlisted and write-gated | `tests/test_api.py::test_assistant_chat_runs_retrieval_tool_without_llm_tokens`, `tests/test_api.py::test_assistant_chat_requires_explicit_write_execution`, `tests/test_assistant_service.py`, `docs/assistant_mcp_agent.md`, and `src/ojtflow/mcp_servers/README.md`. |
| Retrieval query context is treated as data | `tests/test_retrieval.py::test_retrieval_trace_flags_untrusted_query_context` and blank/trimmed boundary tests in `tests/test_api.py`. |

## Frontend

| Claim | Evidence |
| --- | --- |
| Frontend serves a built React bundle through nginx | `tests/test_docker_runtime_config.py::test_frontend_container_serves_built_assets_with_nginx` and `frontend/scripts/assert-runtime-assets-current.mjs`. |
| API calls stay behind `src/api.ts` and server-state hooks | `tests/test_frontend_architecture.py::test_frontend_network_calls_stay_behind_api_boundary` and `tests/test_frontend_architecture.py::test_frontend_features_use_server_state_boundary`. |
| Assistant UI stays a command surface over backend tools | `frontend/src/features/assistant/assistant-page.tsx`, `frontend/src/lib/server-state.ts`, `frontend/src/api.ts`, and `docs/frontend_architecture.md`. |
| Feature modules do not import sibling features | `tests/test_frontend_architecture.py::test_frontend_features_do_not_import_other_features`. |
| Browser storage and direct cookie access are not used for auth/session state | `tests/test_frontend_architecture.py::test_frontend_browser_storage_is_not_used_for_auth_or_state`. |
| Session loss clears protected UI and query cache | `frontend/e2e/auth.spec.ts` revoked-session test and `tests/test_frontend_architecture.py::test_auth_provider_clears_server_state_cache_on_session_loss`. |
| Desktop and mobile route matrix has no horizontal overflow, clipped controls, or bad tap targets | `frontend/e2e/layout.spec.ts` route integrity tests. |
| Workflow, review, evidence, output, audit, schema, settings, upload, and queue flows are browser-tested | `frontend/e2e/workflow.spec.ts`, `frontend/e2e/layout.spec.ts`, and `frontend/e2e/auth.spec.ts`. |
| Google OAuth handoff reaches Google, but human consent remains manual | `frontend/e2e/oauth.spec.ts`; consent completion is intentionally not automated with committed credentials. |

## Secret And Artifact Hygiene

| Claim | Evidence |
| --- | --- |
| `.env`, credentials, ADC, key files, `plan/`, caches, reports, and local artifacts are ignored | `tests/test_repo_hygiene.py::test_local_secret_and_runtime_paths_are_ignored` and `tests/test_repo_hygiene.py::test_generated_artifacts_are_not_visible_to_git`. |
| Docker build contexts exclude local state and credentials | `tests/test_docker_runtime_config.py::test_docker_build_contexts_exclude_local_state_and_secrets` and `tests/test_repo_hygiene.py::test_docker_build_contexts_exclude_cloud_credentials`. |
| Source tree contains no committed OAuth secrets, API tokens, private keys, local machine paths, or ADC material | `tests/test_repo_hygiene.py::test_source_tree_does_not_contain_committable_google_oauth_secrets`, `tests/test_repo_hygiene.py::test_source_tree_does_not_contain_committable_private_keys_or_api_tokens`, and `tests/test_repo_hygiene.py::test_docs_and_source_do_not_contain_local_machine_paths`. |
