# Interoperability Month 7 v0

This pass adds the first backend adapters for Month 7 interoperability work.
The implementation is intentionally deterministic and review-oriented: it
profiles and maps healthcare exchange data without claiming full conformance to
external standards.

Primary standards anchors:

- HL7 FHIR Bulk Data / NDJSON export patterns: https://hl7.org/fhir/uv/bulkdata/
- HL7 FHIR resource model: https://hl7.org/fhir/
- DICOM current standard: https://www.dicomstandard.org/current
- OHDSI OMOP Common Data Model: https://ohdsi.github.io/CommonDataModel/

## Implemented Scope

### F139 Bulk FHIR NDJSON Import

`parse_bulk_fhir_ndjson(...)` parses newline-delimited FHIR-like resources for
selected v0 resource types:

- Patient
- Observation
- DiagnosticReport
- DocumentReference
- Provenance
- AuditEvent
- ImagingStudy

It records line numbers, resource IDs, resource counts, rejected-line counts,
and warnings for unsupported resource types or missing IDs.

API:

```text
POST /api/v1/interoperability/fhir/bulk/import
```

### F140 Bulk FHIR NDJSON Export

`export_clinical_package_as_bulk_fhir_ndjson(...)` groups approved
`ClinicalPackage` resources by `resourceType` and emits one NDJSON file per
resource type with a SHA-256 hash.

Export is blocked when:

- the package review is pending/rejected/clarification/cancelled
- any resource still has `review_required=true`
- `require_approval=true` and the package is not export-ready

API:

```text
POST /api/v1/interoperability/fhir/bulk/export-package
```

### F141 HL7 v2 Starter Parser

`parse_hl7_v2_message(...)` parses pipe-delimited starter messages containing:

- MSH
- PID
- OBR
- OBX

The parser preserves segment indexes and raw segment text for provenance.

### F142 HL7 v2 To FHIR-Like Observation

`map_hl7_v2_lab_observations(...)` maps OBX rows into FHIR-like Observation
records while preserving field provenance:

- PID-3 -> `Observation.subject.reference`
- OBX-3 -> `Observation.code`
- OBX-5 -> `Observation.valueQuantity.value`
- OBX-6 -> `Observation.valueQuantity.unit`
- OBX-14 -> `Observation.effectiveDateTime`

API:

```text
POST /api/v1/interoperability/hl7v2/observations
```

### F143 DICOM Metadata Parser

`profile_dicom_metadata(...)` profiles DICOM metadata without parsing pixel data.
It extracts:

- StudyInstanceUID
- SeriesInstanceUID
- SOPInstanceUID
- Modality
- Laterality
- AccessionNumber
- de-identification status
- patient identifier presence

PixelData is intentionally removed from the stored profile.

### F144 ImagingStudy-Like Mapping

`map_dicom_to_imaging_study(...)` maps the metadata profile to an
ImagingStudy-like resource. It emits a warning that pixel data is not parsed or
exported by this v0 mapper.

API:

```text
POST /api/v1/interoperability/dicom/metadata
```

### F145 DocumentReference Mapping

`build_document_reference(...)` creates a DocumentReference-like resource for
uploaded PDFs, images, notes, and extracted reports by preserving:

- document/artifact ID
- filename
- content type
- artifact/source reference
- description

API:

```text
POST /api/v1/interoperability/document-reference
```

## Current Limits

- This is FHIR-like, not certified FHIR conformance.
- HL7 v2 support is a starter parser for common ORU-style lab messages.
- DICOM support is metadata-only; pixel data is not processed.
- OMOP analytics export is designed in F146-F149 and implemented separately.

Verification:

```bash
OJT_STORAGE_BACKEND=memory PYTHONPATH=src pytest -q tests/test_interoperability.py
```
