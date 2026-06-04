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
| Graph-NER/RAG is a v0 handoff contract, not a claimed live graph agent | `RELEASE_CANDIDATE.md`, `docs/retrieval_module_v0.md`, and workflow handoff assertions in the Python suite. |

## Retrieval

| Claim | Evidence |
| --- | --- |
| Retrieval uses trusted healthcare knowledge inventory | `tests/test_retrieval.py::test_static_retrieval_ranks_healthcare_evidence_with_trace` and retrieval endpoint tests. |
| Postgres mode uses full-text search, configured vector scoring, fusion, and reranking | `tests/test_postgres_migrations.py::test_retrieval_v0_migration_has_search_tables_and_pgvector_fallback`, `tests/test_postgres_migrations.py::test_semantic_embedding_vector_migration_uses_384_dimensions`, and retrieval-backed workflow tests. |
| Retrieval trace exposes strategy, variants, filters, candidate counts, selected IDs, safety flags, and warnings | `tests/test_retrieval.py`, `tests/test_api.py::test_api_direct_convert_validate_fhir_ocr_and_error`, and browser Evidence-tab checks. |
| Runtime readiness probes retrieval through the same service path used by workflows | `tests/test_api.py::test_runtime_readiness_returns_sanitized_operational_checks`, `tests/test_api.py::test_runtime_readiness_requires_trusted_schema_inventory`, and `tests/test_api.py::test_runtime_readiness_requires_retrieval_sources`. |
| Retrieval query context is treated as data | `tests/test_retrieval.py::test_retrieval_trace_flags_untrusted_query_context` and blank/trimmed boundary tests in `tests/test_api.py`. |

## Frontend

| Claim | Evidence |
| --- | --- |
| Frontend serves a built React bundle through nginx | `tests/test_docker_runtime_config.py::test_frontend_container_serves_built_assets_with_nginx` and `frontend/scripts/assert-runtime-assets-current.mjs`. |
| API calls stay behind `src/api.ts` and server-state hooks | `tests/test_frontend_architecture.py::test_frontend_network_calls_stay_behind_api_boundary` and `tests/test_frontend_architecture.py::test_frontend_features_use_server_state_boundary`. |
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
