-- Keep persisted retrieval evidence compatible with advanced retrieval modules.

alter table ojtflow.evidence
    drop constraint if exists evidence_source_type_check;

alter table ojtflow.evidence
    add constraint evidence_source_type_check check (
        source_type in (
            'input_data',
            'schema',
            'data_dictionary',
            'terminology_system',
            'healthcare_standard',
            'transformation_example',
            'validation_report',
            'tool_output',
            'human_decision',
            'audit_event',
            'ocr_box',
            'dicom_metadata',
            'image_mask',
            'video_track'
        )
    );
