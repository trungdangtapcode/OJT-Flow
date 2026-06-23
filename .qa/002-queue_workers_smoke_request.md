# QA Request: Queue-backed OCR/RAG Workers

Please add tests under `tests/` for the RabbitMQ/Celery worker implementation.
Do not weaken existing smoke assertions.

Required coverage:

- In `OJT_QUEUE_BACKEND=rabbitmq`, `POST /api/v1/parse/extract` with a PDF or
  image returns HTTP `202` with a durable `job_id` instead of blocking.
- The returned job starts as `queued` and is pollable through
  `GET /api/v1/jobs/{job_id}`.
- A Celery worker executing a `file_parse` job writes `succeeded`, trace output,
  extractor metadata, and extracted text back to Postgres.
- OpenAI Vision OCR failures write a structured job error and do not fabricate
  extracted text.
- `runtime/readiness` reports `queue_backed=true` when the service is configured
  with RabbitMQ.
- In pilot/production mode, missing `OJT_QUEUE_BACKEND=rabbitmq` fails settings
  validation.
- `docker compose config --quiet` remains green with the monitoring stack.
- `/metrics` returns Prometheus text and includes API request counters after at
  least one API call.

Live smoke scenario:

1. Start `docker compose up -d postgres redis rabbitmq api worker-ocr flower prometheus grafana`.
2. Upload the noisy rotated scanned PDF fixture through `/parse/extract`.
3. Assert initial response is `202`.
4. Poll `/jobs/{job_id}` until terminal.
5. Assert status is `succeeded`, extractor is `openai_vision`, and extracted
   text contains `HBA1C 7.4%` and `FHIR OBS`.
6. Confirm Flower shows the task and Prometheus can scrape API/RabbitMQ/Celery
   targets.
