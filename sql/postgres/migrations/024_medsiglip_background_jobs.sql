-- Allow GPU-backed MedSigLIP image classification jobs in the durable queue.

alter table if exists ojtflow.background_jobs
    drop constraint if exists background_jobs_type_check;

alter table if exists ojtflow.background_jobs
    add constraint background_jobs_type_check check (
        job_type in (
            'retrieval_reindex',
            'file_parse',
            'ocr_extract',
            'embedding_reindex',
            'medsiglip_classification',
            'external_ingest',
            'export_package'
        )
    );
