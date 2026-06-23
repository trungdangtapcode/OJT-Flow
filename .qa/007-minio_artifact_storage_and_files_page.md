# QA Request: MinIO Artifact Storage And Files Dashboard

Do not mock this. Run against a live local stack with Postgres, Redis, MinIO,
API, and frontend.

## Goal

Verify uploaded user files/artifacts are stored in MinIO object storage and
visible from the dashboard Files page.

## Required Environment

- `OJT_STORAGE_BACKEND=postgres`
- `OJT_OBJECT_STORAGE_BACKEND=minio`
- `OJT_MINIO_ENDPOINT=minio:9000` inside Docker, or `localhost:19000` from host
- `OJT_MINIO_ACCESS_KEY` set
- `OJT_MINIO_SECRET_KEY` set
- `OJT_MINIO_BUCKET=ojtflow-artifacts`

## Checks

1. Start stack:

   ```bash
   docker compose up -d postgres redis minio api worker-ocr worker-ingestion
   ```

2. Confirm runtime reports MinIO:

   ```bash
   curl -fsS http://127.0.0.1:18000/api/v1/runtime/config \
     -H "Authorization: Bearer $OJT_REAL_SMOKE_AUTH_TOKEN" | jq .
   ```

   Expected:

   - `storage_backend` is `postgres`
   - `object_storage_backend` is `minio`
   - `minio_configured` is `true`
   - `minio_bucket_configured` is `true`

3. Upload one CSV through Workbench and one PNG/PDF through Assistant or parse
   upload API.

4. Inspect Postgres:

   ```sql
   select artifact_id, organization_id, filename, source, storage_ref
   from ojtflow.uploaded_artifacts
   order by created_at desc
   limit 10;
   ```

   Expected:

   - new rows have non-null `organization_id`
   - new rows have `storage_ref` beginning with `s3://ojtflow-artifacts/`
   - no new upload row uses `file://`

5. Inspect MinIO:

   - Open MinIO console on `http://localhost:19001`
   - Bucket `ojtflow-artifacts` exists
   - Uploaded files exist under `uploads/{workspace}/{owner}/{artifact}/...`

6. Open dashboard:

   - Go to `http://localhost:15173/files`
   - Confirm the uploaded files are listed.
   - Confirm the storage badge says `MinIO`.
   - Open a file detail panel.
   - Confirm SHA-256, owner, workspace, source, extraction traces, and access
     events are visible.
   - Click download and confirm the original file bytes download.

7. Legacy migration dry-run:

   ```bash
   scripts/migrate-local-artifacts-to-minio
   ```

   Expected:

   - prints `DRY-RUN`
   - does not update Postgres rows

8. Legacy migration execution, only if a backup exists:

   ```bash
   scripts/migrate-local-artifacts-to-minio --execute
   ```

   Expected:

   - uploads local `file://` rows into MinIO
   - updates storage refs to `s3://...`
   - refuses to migrate any row whose local file hash does not match Postgres

## Fail Conditions

- New user upload saves only to local disk.
- New upload metadata is missing from `/files`.
- New upload has null `organization_id`.
- Dashboard download returns different bytes than the uploaded file.
- Migration updates Postgres before object upload/hash verification.
