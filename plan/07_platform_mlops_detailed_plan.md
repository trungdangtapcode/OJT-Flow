# Platform, CI/CD, Observability, and MLOps Detailed Plan

The platform plan should make OJTFlow credible as deployable healthcare AI infrastructure, while keeping the MVP small enough to finish.

## Local MVP Stack

Recommended local stack:

- Python
- FastAPI
- Pydantic
- SQLite
- file-based dataset storage
- file-based knowledge sources
- simple lexical retrieval
- optional FAISS or local vector store
- direct Python tools
- Docker Compose
- structured JSON logs
- pytest

Optional local UI:

- Streamlit for fastest demo
- React/Next.js if product UI matters more than speed

## Production-Shaped Stack

Future deployment:

- FastAPI API service
- worker service for long workflows
- PostgreSQL
- pgvector or Qdrant/Milvus
- OpenSearch for lexical search
- graph DB or graph tables
- object storage for datasets/artifacts
- MCP servers
- model gateway
- review UI
- OpenTelemetry
- Prometheus/Grafana
- Evidently for drift/evaluation reports

## GCP-First Blueprint

GCP path:

- Cloud Healthcare API for FHIR/HL7v2/DICOM where appropriate
- Cloud Storage for raw and artifact storage
- BigQuery/BigLake for analytics and evaluation history
- GKE for API, workers, MCP servers, retrieval services
- Cloud Run for lightweight review/webhook/admin services
- Artifact Registry for images and packages
- Workload Identity Federation for GitHub Actions authentication
- Cloud Deploy and/or Argo CD for deployment
- Secret Manager
- Cloud KMS
- VPC Service Controls for restricted projects
- Cloud Logging, Monitoring, Trace
- Managed Prometheus
- Vertex AI Pipelines or Kubeflow Pipelines for ML workflows
- MLflow or Vertex metadata/model registry

## CI/CD Stages

### Pull Request Quality Gate

Run:

- format check
- lint
- type check
- unit tests
- integration tests with fixtures
- API contract tests
- schema validation tests
- prompt-injection fixture tests
- PHI/sensitive-field fixture tests
- documentation build if needed

### Secure Build

Run later:

- Docker build
- dependency scan
- SBOM generation
- vulnerability scan
- image signing
- provenance
- publish to Artifact Registry

### Retrieval and Data Validation

Run:

- knowledge source validation
- schema registry validation
- small index rebuild
- retrieval evaluation
- stale source check
- source coverage check

### ML/MLOps Evaluation

Run for optional models:

- baseline vs candidate comparison
- calibration if applicable
- fairness/subgroup report if data supports it
- latency
- model card update
- registry record
- promotion decision

### Deployment

MVP:

- local Docker Compose

Staging:

- Cloud Run or GKE
- environment variables from Secret Manager
- test database and storage bucket

Production-shaped:

- GitOps manifest
- Argo CD sync
- Cloud Deploy promotion
- manual approval for clinical/restricted environments

## Observability

Collect signals at these layers:

| Layer | Signals |
| --- | --- |
| API | request count, latency, status code, payload size |
| Workflow | duration, status, pause count, failure reason |
| Agent | step duration, status, retries, confidence |
| Tool | call count, latency, failure, permission denial |
| Validation | issue counts, severity, schema version |
| Retrieval | recall eval, empty rate, stale source rate, top-k scores |
| Explanation | unsupported-claim rate, evidence coverage |
| Review | pending count, approval/rejection rate, time to decision |
| Security | prompt injection flags, PHI flags, export blocks |
| Cost | model tokens, vector DB queries, GPU usage later |

Use workflow ID as a correlation key everywhere.

## SLOs

MVP demo SLOs:

- simple conversion p95 under 3 seconds
- complex workflow p95 under 15 to 30 seconds
- validation coverage 100 percent for transformed outputs
- audit reconstruction 100 percent for completed workflows
- review gate bypass 0 critical cases
- raw PHI in logs 0 seeded cases

Future SLOs:

- retrieval empty result rate below threshold
- unsupported clinical claim rate below threshold
- OCR/vision quality within approved pilot threshold
- model/index drift jobs complete on schedule

## MLOps Lifecycle

For every model, index, graph snapshot, prompt, or schema:

1. Register version.
2. Store source data and code commit.
3. Run evaluation.
4. Compare against baseline.
5. Record risks and limitations.
6. Approve or reject promotion.
7. Deploy through versioned release.
8. Monitor behavior.
9. Roll back if needed.

Artifacts to version:

- schemas
- prompts
- model gateway configs
- embedding models
- vector collections
- lexical indexes
- graph snapshots
- OCR processors
- segmentation checkpoints
- evaluation datasets
- transformation examples

## Docker Compose MVP

Initial services:

- `api`
- `worker` if async workflows are needed
- `db` optional SQLite volume or PostgreSQL
- `vector` optional Qdrant later
- `ui` optional

Start simple:

```text
api + sqlite + local files
```

Add services only when tests require them.

## Configuration

Use environment variables:

- `OJT_ENV`
- `DATABASE_URL`
- `DATASET_STORAGE_PATH`
- `KNOWLEDGE_PATH`
- `MODEL_PROVIDER`
- `MODEL_NAME`
- `VECTOR_STORE_URL`
- `LOG_LEVEL`
- `ENABLE_MCP`
- `ENABLE_RETRIEVAL`
- `ENABLE_HUMAN_REVIEW_REQUIRED`

Do not hardcode secrets.

## Acceptance Criteria

- Local dev setup can run with one command.
- Tests do not require cloud services.
- CI can run without secrets for basic checks.
- Docker build path is documented.
- Workflow logs are structured and correlated by workflow ID.
- Version fields exist for schemas, prompts, models, indexes, and graph snapshots.
- GCP blueprint is documented without forcing MVP to deploy there.

## Build Sequence

1. Create local settings module.
2. Add structured logging.
3. Add pytest and fixture layout.
4. Add basic CI workflow.
5. Add Dockerfile and Compose.
6. Add database migration path.
7. Add retrieval evaluation job.
8. Add security fixture tests.
9. Add GCP deployment blueprint docs.
10. Add MLOps artifact/version registry design.

## Risks

| Risk | Control |
| --- | --- |
| Cloud setup consumes MVP time | Keep GCP as blueprint until local flow works |
| Too many services locally | Start with SQLite and local files |
| Observability is skipped | Add structured logs from day one |
| Model/index versions are untracked | Add version fields before experiments |
| CI needs unavailable secrets | Make PR checks secret-free |
