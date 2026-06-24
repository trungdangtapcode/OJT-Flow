.PHONY: real-smoke
.PHONY: api-local
.PHONY: worker-ocr-local
.PHONY: queue-stack
.PHONY: queue-stack-down
.PHONY: migrate-artifacts-to-minio

-include .env.example
-include .env
-include .env.smoke.local
export OJT_REAL_SMOKE_AUTH_TOKEN
export OJT_REAL_SMOKE_API_BASE_URL

real-smoke:
	scripts/run-real-smoke-tests --no-build

api-local:
	scripts/run-api-local

worker-ocr-local:
	celery -A ojtflow.infrastructure.queue.celery_app:celery_app worker -Q $${OJT_OCR_QUEUE:-ocr} -n worker-ocr-local@%h --concurrency=$${OJT_OCR_WORKER_CONCURRENCY:-2} --loglevel=$${OJT_CELERY_LOG_LEVEL:-INFO}

queue-stack:
	docker compose up -d rabbitmq worker-ocr worker-rag worker-embedding worker-ingestion worker-export flower prometheus grafana rabbitmq-exporter celery-exporter node-exporter loki promtail

queue-stack-down:
	docker compose down --remove-orphans

migrate-artifacts-to-minio:
	scripts/migrate-local-artifacts-to-minio $(EXECUTE)
