-- Expand datasets.source_kind to include values added by the document upload feature.
-- The original constraint only covered 'inline', 'upload', 'generated', 'fixture'.
-- File upload workflows use 'uploaded_file_raw' and 'uploaded_file_extracted_text'.

alter table ojtflow.datasets
    drop constraint if exists datasets_source_kind_check;

alter table ojtflow.datasets
    add constraint datasets_source_kind_check check (
        source_kind in (
            'inline',
            'upload',
            'generated',
            'fixture',
            'uploaded_file_raw',
            'uploaded_file_extracted_text',
            'binary'
        )
    );
