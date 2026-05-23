# Medical Multimodal and Japan-Market Detailed Plan

The full proposal extends OJTFlow beyond structured tables into clinical documents, DICOM metadata, image masks, detection boxes, and video tracks. This phase should preserve the same evidence and review backbone created for structured data.

## Scope Boundary

MVP plus research prototype:

- synthetic Japanese/English clinical-style documents
- OCR field extraction contracts
- DICOM metadata contracts using public or synthetic samples
- visual evidence object for segmentation masks, boxes, and tracks
- optional segmentation proof of concept on public data
- Japan-market governance checklist and JP Core/FHIR aliases

Out of scope:

- production clinical deployment
- autonomous diagnosis
- treatment recommendation
- real PHI without formal governance
- unreviewed medical document automation

## Multimodal Evidence Principle

Every extracted fact must point back to a source artifact:

- OCR page and bounding box
- table cell
- checkbox region
- DICOM study/series/instance
- image slice
- mask ID
- bounding box ID
- frame ID
- video track ID
- reviewer correction

The evidence object should not change shape just because the source is multimodal.

## OCR and Document AI

### Document Contract

```json
{
  "document_id": "doc_uuid",
  "workflow_id": "wf_uuid",
  "document_type": "lab_report",
  "language": ["ja", "en"],
  "pages": [
    {
      "page_number": 1,
      "width": 2480,
      "height": 3508,
      "blocks": [],
      "tables": [],
      "fields": []
    }
  ],
  "source_ref": "storage://documents/doc_uuid.pdf",
  "sha256": "hash"
}
```

### Field Extraction Contract

```json
{
  "field_id": "field_uuid",
  "name": "patient_id",
  "value": "P001",
  "confidence": 0.93,
  "page": 1,
  "bbox": [100, 200, 300, 250],
  "normalized_to": "FHIR.Patient.identifier",
  "requires_review": true
}
```

Review triggers:

- low OCR confidence
- conflicting fields
- APPI-sensitive field detected
- value mapped to clinical code
- table extraction uncertainty
- handwritten or stamped field

## DICOM Metadata

### DICOM Evidence Contract

```json
{
  "dicom_ref": {
    "study_uid": "1.2.3",
    "series_uid": "1.2.3.4",
    "instance_uid": "1.2.3.4.5",
    "frame_number": null
  },
  "modality": "CT",
  "body_part": "CHEST",
  "deidentified": true,
  "source_ref": "storage://dicom/public_sample",
  "metadata_fields": {
    "pixel_spacing": [0.7, 0.7],
    "slice_thickness": 1.0
  }
}
```

MVP behavior:

- ingest metadata only
- store references and de-identification status
- do not require real DICOM store
- connect metadata to evidence package

Future GCP path:

- Cloud Healthcare API DICOM store
- de-identification/export job
- segmentation/detection batch job
- mask artifact
- evidence index

## Visual Evidence

### Mask Contract

```json
{
  "mask_id": "mask_uuid",
  "source_type": "dicom_slice",
  "source_ref": "study:series:instance:slice",
  "label": "region_of_interest",
  "model_name": "medsam_demo",
  "model_version": "0.1.0",
  "prompt": {
    "type": "box",
    "coordinates": [120, 80, 300, 260]
  },
  "artifact_ref": "storage://visual/mask_uuid.png",
  "confidence": 0.74,
  "requires_clinician_review": true
}
```

### Detection Box Contract

```json
{
  "box_id": "box_uuid",
  "label": "candidate_region",
  "bbox": [120, 80, 300, 260],
  "score": 0.67,
  "source_ref": "image_uuid",
  "model_version": "detector_demo_0.1",
  "requires_review": true
}
```

### Video Track Contract

```json
{
  "track_id": "track_uuid",
  "label": "region_of_interest",
  "frame_start": 10,
  "frame_end": 80,
  "frame_refs": ["frame_010", "frame_011"],
  "artifact_ref": "storage://tracks/track_uuid.json",
  "metrics": {
    "temporal_iou": 0.81
  },
  "requires_review": true
}
```

## Medical Vision Prototype Options

Choose one practical demo, not all.

Option A: Segmentation evidence demo

- Use public image sample.
- Run SAM/MedSAM-style model or use precomputed mask fixture.
- Store mask artifact and metadata.
- Display/report mask as evidence only.
- Include review required flag.

Option B: DICOM metadata and mock mask demo

- Use public DICOM metadata fixture.
- Generate or include synthetic mask artifact.
- Focus on evidence contract and audit.
- Lower implementation risk.

Option C: OCR-first multimodal demo

- Use synthetic Japanese/English lab form.
- Extract fields with bounding boxes.
- Map fields to schema.
- Review low-confidence fields.
- Best fit for 12-week OJT if time is tight.

Recommended order:

1. OCR-first.
2. DICOM metadata.
3. Segmentation artifact.
4. Detection/tracking design only.

## Japan-Market Requirements

Japan readiness should be treated as product design:

- APPI-aware sensitive information handling.
- MHLW medical information security checklist mapping.
- PMDA/SaMD boundary statement.
- JP Core/FHIR mapping notes.
- Japanese terminology aliases.
- approval history suitable for ringi-style evidence review.
- tenant isolation assumptions.
- audit export.
- clear intended-use statement.

## JP Core and Terminology Alias Plan

Create an alias table:

```json
{
  "alias": "患者ID",
  "canonical": "patient_id",
  "maps_to": "FHIR.Patient.identifier",
  "language": "ja",
  "confidence": 1.0,
  "source_id": "jp_core_aliases_v1"
}
```

Initial categories:

- patient identifiers
- encounter identifiers
- observation/lab names
- medication names
- units
- dates
- departments
- provider names
- consent fields

## Clinical Explanation for Multimodal Outputs

Explanation must include:

- intended use
- source artifact references
- confidence and uncertainty
- limitations
- review recommendation
- unsupported claims
- reviewer corrections

Do not say:

- "The image shows disease X" unless the task is explicitly scoped, validated, and governed.

Do say:

- "The demo model produced an assistive region-of-interest mask on public sample image X. This is a research artifact and requires clinician review."

## Metrics

OCR:

- character error rate
- word error rate
- key-value extraction F1
- table-cell F1
- checkbox accuracy
- Japanese/English split performance
- human correction rate

Segmentation:

- Dice
- IoU
- HD95
- boundary F1
- reviewer correction time
- subgroup by modality if available

Detection:

- mAP
- sensitivity
- specificity
- FROC
- false positives per image

Tracking:

- IDF1
- HOTA
- temporal IoU
- identity switches
- track fragmentation

Governance:

- review gate coverage
- evidence completeness
- unsupported-claim rate
- APPI checklist completion

## Acceptance Criteria

- OCR output includes page and bounding-box provenance.
- Extracted clinical fields can be reviewed before transformation.
- DICOM metadata references are stored without requiring real PHI.
- Visual masks/boxes/tracks are evidence artifacts with review flags.
- Japan governance checklist exists and is tied to workflow controls.
- No multimodal output is represented as autonomous diagnosis.

## Build Sequence

1. Add OCR and document contracts.
2. Create synthetic Japanese/English document fixtures.
3. Add field extraction fixture and review flow.
4. Add JP Core/FHIR alias table.
5. Add DICOM metadata contract and public fixture.
6. Add visual evidence contracts.
7. Add optional segmentation artifact demo.
8. Add multimodal evidence to explanation output.
9. Add governance checklist and acceptance tests.

## Risks

| Risk | Control |
| --- | --- |
| Multimodal scope explodes | Pick one demo path first |
| Visual outputs look too authoritative | Label as assistive evidence and require review |
| Japan compliance is treated as decoration | Tie checklist to workflow controls |
| OCR errors corrupt structured data | Review low-confidence fields before mapping |
| Public datasets have license limits | Track dataset license and intended use |
